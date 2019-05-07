#!/usr/bin/python
# -*- coding: ascii -*-

import serial
import logging
import datetime
import os
import math

# name the logging file
now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S_")
logging_file = now + "experiment_logs.txt"

# set the filepath relative to current location
filepath = os.path.join('logs', logging_file)
if not os.path.exists('logs'):
    os.makedirs('logs')

# set up logging to file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=filepath,
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

# Now, we can log to the root logger, or any other logger. First the root...
# logging.info('Jackdaws love my big sphinx of quartz.')

# Define loggers which represent areas in the application:
logger_pump = logging.getLogger('pump')
logger_collector = logging.getLogger('collector')
logger_pump.info("started")
logger_collector.info("started")


class Chain(serial.Serial):
    # TODO append carriage return to all commands send via serial
    """
    Object that holds all the information for establishing a serial connection.
    It inherits its default values from serial.Serial and changes them in its
    __init__.
    """

    # configure serial settings and start logging
    def __init__(self, port):
        super(serial.Serial, self).__init__(port=port, baudrate=9600, bytesize=serial.EIGHTBITS,
                                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=2)

        self.flushOutput()
        self.flushInput()

        logger_pump.info("Chain created on {}. Baudrate: {}".format(port, self.baudrate))
        logger_pump.debug("Baudrate: {}, byte size: {}, parity: {}, stop bits: {}, timeout {}.".format(self.baudrate,
                                                                                                       self.bytesize,
                                                                                                       self.parity,
                                                                                                       self.stopbits,
                                                                                                       self.timeout))

    def serial_read(self):
        response = port.read(5)
        logger_pump.info(response)


class PumpError(Exception):
    pass


class Pump(object):
    # TODO: Check flow rate ranges of pumps and integrate checks
    # that will throw errors if pump is supposed to pump faster than possible
    """
    This class holds all functions for HLL pumps. First, name, serial address
    and serial connection is initialized. Next, the pump is queried to
    give its software's version to verify established connection. Success or
    failure is logged and printed to the screen.
    """

    def __init__(self, chain, name, address):
        self.name = name
        self.address = address
        self.serialcon = chain

        try:
            self.serialcon.write(str(self.address) + 'VER\r')
            resp = self.serialcon.read(17)
            logger_pump.info(resp)

            if resp[1:3] != str(self.address):
                raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))
        except PumpError:
            self.serialcon.close()
            raise

        logger_pump.info('{}: created at address {} on {}.'.format(self.name,
                                                                   self.address, self.serialcon.port))

    def diameter(self, diameter):
        """ Turns diameter input into a string and change decimals
        separator to ".". Checks if diameter is 0.1 < diameter < 30.0 cm.
        """
        global dia  # das ist ziemlich unschoen, weil die Funktion dadurch Nebeneffekte hat. Saueberer ist am Ende return Dia und dan den caller der Methode die Variable setzen lassen
        dia = str(diameter).replace(",", ".")

        if 0.1 < float(dia) < 30.0:  # Denkbar waere auch hier mit assert zu arbeiten, dann bricht das Programm halt ab, wenn es nicht irgendwo gecatcht wird (try block oberhalb im stack) aber das kann ja durchaus erwuenscht sein
            self.serialcon.write(str(self.address) + "dia" + dia + "\r")
            resp = self.serialcon.read(5)

            if str(self.address) + "S" in resp:
                logger_pump.info(self.name + ": diameter set to " + dia + " cm.")

            else:
                logger_pump.warning(self.name + ": Diameter not set.")
                self.serialcon.close()
                raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))

        else:  # TODO: check if function works.
            logger_pump.warning("Diameter out of range. Accepted values: 0.1 - 30.0 cm. Diameter not set.")

    def volume(self, volume):
        """ Controls the volume to be dispensed. Turns input into strings
        and changes decimal separator to ".". Checks if volume is greater
        than syringe volume.
        """
        # max. volume is calulated the following way: (diameter / 2)**2*pi*60.
        # Hamilton and NormJect syringes' barrel is <= 60 mm long.
        max_volume = (float(dia) / 2) ** 2 * math.pi * 60
        # TODO: check if diameter.dia works
        if max_volume >= volume:
            vol = str(volume).replace(",", ".")
            self.serialcon.write(str(self.address) + "vol" + vol + "\r")
            resp = self.serialcon.read(5)

            if str(self.address) + "S" in resp:
                logger_pump.info(self.name + ": volume set to " + vol + " ??l.")  # ml is also possible!
            else:
                logger_pump.warning(self.name + ": Volume not set.")
                self.serialcon.close()
                raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))
        else:
            logger_pump.warning("Volume exceeds syringe volume. Please adjust volume.")
        # TODO: check if syringe volume is oor?
        # query: command without parameters e.g. 01dia will return diameter

    def rate(self, rate, unit):
        """ Controls the pump rate. The 'rate' input is transmitted to the pump
        and returns a warning, when the chosen rate is out of range for the chosen
        diameter. The 'unit' input is checked against a dictionary and changed, if necessary,
        to return the correct syntax.
        """
        units_dict = {"\u03BCl/min": "um", "\u03BCl/m": "um", "\u03BC/min": "um",
                      "ml/min": "mm", "ml/m": "mm", "m/min": "mm",
                      "\u03BCl/h": "uh", "\u03BC/h": "uh",
                      "ul/h": "uh", "u/h": "uh",
                      "ml/h": "mh", "m/h": "mh"}
        if unit in units_dict.values():
            command = "{}rat{}{}".format(self.address, rate, unit)  # gewoehn dir am besten gleich an, strings immer mit format zu bauen. Ist angenehmer, gerade wenn man dann mit floats arbeitet (angabe der nachkommastellen die gepritnet werden) oder die gleiche var mehrmals im string vorkommt OLD: str(self.address) + "rat" + str(rate) + unit
            self.serialcon.write(command + "\r")
            resp = self.serialcon.read(5)
            if str(self.address) + "S?" in resp:
                logger_pump.warning("{} {} out of range or command {} incorrect.".format(rate,
                                                                                         unit, command))
                self.serialcon.close()
            else:
                logger_pump.info("{}: Rate set to {} {}".format(self.name, rate, unit))
        elif unit in units_dict:
            unit_replaced = units_dict[unit]
            command = str(self.address) + "rat" + str(rate) + unit_replaced
            self.serialcon.write(command + "\r")
            resp = self.serialcon.read(5)
            if str(self.address) + "S?" in resp:
                logger_pump.warning("{} {} out of range or command {} incorrect.".format(rate,
                                                                                         unit, command))
                self.serialcon.close()
            else:
                logger_pump.info("{}: Rate set to {} {}".format(self.name, rate, unit))

        else:
            logger_pump.warning("Unit not accepted. Possible values:\n",
                                "um (\u03BCl/min), uh (\u03BCl/h), mm (ml/min), mh (ml/h).")

    def start(self):
        """ Starts the pump by issuing a start command. If a program is active on the
        pump, it will start at phase 0 or resume from the phase that was previously
        active.
        """
        self.serialcon.write(str(self.address) + "run\r")
        resp = self.serialcon.read(10)

        if str(self.address) + "I" in resp:
            logger_pump.info(self.name + ": started.")

        else:
            logger_pump.warning(self.name + ": did not start.")  # vll noch resp printen?
            self.serialcon.close()
            raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))

    def stop(self):
        """ Stops the pump by issuing a stop command. If a program is active on the
        pump, it will pause at the current phase and resume from this phase when
        a start command is issued. Two stop commands set current phase to 0.
        """
        self.serialcon.write(str(self.address) + "stp\r")
        resp = self.serialcon.read(5)
        logger_pump.debug(resp)

        if str(self.address) + "?" in resp:
            logger_pump.warning(self.name + " did not stop.")
            self.serialcon.close()
            raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))
        elif str(self.address) + "P" in resp:
            logger_pump.info(self.name + ": paused.")
        else:
            logger_pump.info(self.name + ": stopped.")

# TODO
# find the range the pumps can operate in (diamter & Flow rate)
# LA160: variable Pumpgeschwindigkeiten: 0.0262 cm/h bis 3.3327 cm/min
# LA120: variable Pumpgeschwindigkeiten: 0.0262 cm/h bis 3.3327 cm/min
# LA122: variable Pumpgeschwindigkeiten: 0,000085 cm/h bis 0,22 cm/min
