#!/usr/bin/python
# -*- coding: ascii -*-

import serial
import logging
import datetime
import os
import math
import time


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
# Confirm the function of the loggers by printing "started" to the console
# and to the log file.
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
                                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

        self.flushOutput()
        self.flushInput()

        logger_pump.info("Chain created on {}. Baudrate: {}".format(port, self.baudrate))
        logger_pump.debug("Baudrate: {}, byte size: {}, parity: {}, stop bits: {}, timeout {}.".format(self.baudrate,
                                                                                                       self.bytesize,
                                                                                                       self.parity,
                                                                                                       self.stopbits,
                                                                                                       self.timeout))

    def serial_read(self):
        response = self.port.read(10)
        logger_pump.info(response)


class PumpError(Exception):
    pass


class Pump(object):
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
        self.dia = 0
        self.status = False

        try:
            command = "{}{}".format(str(self.address), '?\r')
            logger_pump.debug(command)
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(17).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

            if self.address in resp:
                self.status = True
                logger_pump.info('{}: created at address {} on {}.'.format(self.name,
                                                                           self.address, self.serialcon.port))
            else:
                self.status = False
                raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))

        except PumpError:
            # self.serialcon.close()
            raise

    def diameter(self, diameter):
        """ Turns diameter input into a string and change decimals
        separator to ".". Checks if diameter is 0.1 < diameter < 30.0 cm.
        """

        dia = str(diameter).replace(",", ".")

        if len(dia) > 5:
            dia = dia[0:5]
            logger_pump.info('{}: diameter truncated to {}.'.format(self.name, dia))
        else:
            pass
        try:
            assert 0.1 < float(dia) < 30.0  # Denkbar waere auch hier mit assert zu arbeiten, dann bricht das
            # Programm halt ab, wenn es nicht irgendwo gecatcht wird (try block oberhalb im stack) aber das kann
            # ja durchaus erwuenscht sein
            command = "{}dia{}\r".format(str(self.address), dia)
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

            if str(self.address) + "S" in resp:
                logger_pump.info(self.name + ": diameter set to " + dia + " cm.")
                self.dia = dia
                # return dia

            else:
                logger_pump.warning(self.name + ": Diameter not set.")
                self.serialcon.close()
                raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))

        except AssertionError:
            logger_pump.warning("Diameter out of range. Accepted values: 0.1 - 30.0 cm. Diameter not set.")
            self.serialcon.close()

    def volume(self, volume, unit):
        """ Controls the volume to be dispensed. Turns input into strings
        and changes decimal separator to ".". Checks if volume is greater
        than syringe volume.
        """
        # max. volume is calulated the following way: (diameter / 2)**2*pi*60.
        # Hamilton and NormJect syringes' barrel is <= 60 mm long. dia = self.diameter(diameter) -
        # so wuerde es mit return funktionieren, dann muesste ich aber bei jedem call von volume den diameter neu
        # setzen, der aendert sich ja aber nicht staendig. Habs jetzt mit einer neuen variable geloest.
        # Wie findest du diese Loesung?
        volume = str(volume)
        if len(volume) > 5:
            volume = volume[0:5]
            logger_pump.debug('{}: volume truncated to {}.'.format(self.name, volume))
        else:
            pass
        dia = self.dia
        max_volume = (float(dia) / 2) ** 2 * math.pi * 60

        if max_volume >= float(volume):
            vol = str(volume).replace(",", ".")
            command = "{}vol{}\r".format(str(self.address), vol)
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

            if str(self.address) in resp and "?" in resp or "NA" in resp:
                i = 3
                while i > 0:
                    self.serialcon.write(command.encode())
                    resp = self.serialcon.read(10).decode()
                    logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
                    if str(self.address) in resp and "?" in resp or "NA" in resp:
                        i -= 1
                    else:
                        logger_pump.info("{}: Volume set to {} {}".format(self.name, vol, unit))
                        break
                if i == 0:
                    logger_pump.warning("{} {} out of range or command {} incorrect.".format(vol,
                                                                                             unit, command))
                    self.serialcon.close()
            else:
                logger_pump.info("{}: volume set to {} {}".format(self.name, vol, unit))
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
        # set phase function to 'rate' (otherwise setting vol and rate commands do not work.
        command = "{}funrat\r".format(str(self.address))
        self.serialcon.write(command.encode())
        resp = self.serialcon.read(10).decode()
        logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

        if str(self.address) in resp and "?" in resp or "NA" in resp:
            logger_pump.warning("{}: Could not set phase function to 'rate'".format(self.name))
            self.serialcon.close()
            raise PumpError("{}: Could not set phase function to 'rate'".format(self.name))
        rate = str(rate)
        if len(rate) > 5:
            rate = rate[0:5]
            logger_pump.debug('{}: flow rate truncated to {} {}'.format(self.name, rate, unit))
        units_dict = {"\u03BCl/min": "um", "\u03BCl/m": "um", "\u03BC/min": "um",
                      "ml/min": "mm", "ml/m": "mm", "m/min": "mm",
                      "\u03BCl/h": "uh", "\u03BC/h": "uh",
                      "ul/h": "uh", "u/h": "uh",
                      "ml/h": "mh", "m/h": "mh"}
        if unit in units_dict.values():
            command = "{}rat{}{}\r".format(str(self.address), rate, unit)
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

            if str(self.address) in resp and "?" in resp or "NA" in resp:
                i = 3
                while i > 0:
                    self.serialcon.write(command.encode())
                    resp = self.serialcon.read(10).decode()
                    logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
                    if str(self.address) in resp and "?" in resp or "NA" in resp:
                        i -= 1
                    else:
                        logger_pump.info("{}: Rate set to {} {}".format(self.name, rate, unit))
                        break
                if i == 0:
                    logger_pump.warning("{} {} out of range or command {} incorrect.".format(rate,
                                                                                             unit, command))
                    self.serialcon.close()
            else:
                logger_pump.info("{}: Rate set to {} {}".format(self.name, rate, unit))
        elif unit in units_dict:
            unit_replaced = units_dict[unit]
            command = "{}rat{}{}\r".format(str(self.address), str(rate), unit_replaced)
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

            if str(self.address) in resp and "?" in resp or "NA" in resp:
                i = 3
                print("reached if str(self.address) in resp and '?' in resp:")
                while i > 0:
                    print("reached if str(self.address) in resp and '?' in resp: - while loop")
                    self.serialcon.write(command.encode())
                    resp = self.serialcon.read(10).decode()
                    logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
                    if str(self.address) in resp and "?" in resp or "NA" in resp:
                        i -= 1
                    else:
                        logger_pump.info("{}: Rate set to {} {}".format(self.name, rate, unit))
                        break
                if i == 0:
                    logger_pump.warning("{} {} out of range or command {} incorrect.".format(rate,
                                                                                             unit, command))
                    self.serialcon.close()
            else:
                logger_pump.info("{}: Rate set to {} {}".format(self.name, rate, unit))

        else:
            logger_pump.warning("Unit not accepted. Possible values:\n",
                                "um (\u03BCl/min), uh (\u03BCl/h), mm (ml/min), mh (ml/h).")

    def phase_number(self, number):
        """
        This function can be used to write a pumping program. If phase numbers are
        written to the pump before another command, the command will be assigned
        to the phase number. The pump starts at phase 01 and can store 41 phases max.
        If the pump is paused during executing a program, starting it again resumes
        from the phase number it has been at when paused.
        """
        command = "{}phn{}\r".format(str(self.address), number)
        self.serialcon.write(command.encode())
        resp = self.serialcon.read(10).decode()
        logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

        if str(self.address) in resp and "?" in resp or "NA" in resp:
            i = 3
            while i > 0:
                self.serialcon.write(command.encode())
                resp = self.serialcon.read(10).decode()
                if str(self.address) in resp and "?" in resp or "NA" in resp:
                    i -= 1
                else:
                    logger_pump.info("{}: phase number set to {}.".format(self.name, number))
                    break
            if i == 0:
                logger_pump.warning("Phase number {} out of range or command {} incorrect.".format(number,
                                                                                                   command))
                self.serialcon.close()
                raise PumpError("Phase number {} was not set at pump {} at address {}.".format(number,
                                                                                               self.name,
                                                                                               self.address))
        else:
            logger_pump.info("{}: phase number set to {}.".format(self.name, number))

    def start(self):
        """ Starts the pump by issuing a start command. If a program is active on the
        pump, it will start at phase 0 or resume from the phase that was previously
        active.
        """
        command = "{}run\r".format(str(self.address))
        self.serialcon.write(command.encode())
        resp = self.serialcon.read(10).decode()
        logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

        if str(self.address) + "I" in resp:
            logger_pump.info(self.name + ": started.")

        else:
            logger_pump.warning(self.name + ": did not start.")  # vll noch resp printen?
            self.serialcon.close()
            raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))

    def start_all(self, pumps_active, pumps_adr):
        """
        This function issues a command at all pumps in the daisy-chain to start pumping.
        """
        command = "*run\r"
        self.serialcon.write(command.encode())
        time.sleep(0.5)
        self.serialcon.reset_input_buffer()
        if pumps_active["LA120"]:  # pumps_active from main.py
            command = "{}?\r".format(pumps_adr["LA120"])
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
            if "{}{}".format(pumps_adr["LA120"], "I") in resp:
                logger_pump.info("LA120: started.")
            else:
                logger_pump.warning("LA120 did not start!")
        if pumps_active["LA122"]:
            command = "{}?\r".format(pumps_adr["LA122"])
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
            if "{}{}".format(pumps_adr["LA122"], "I") in resp:
                logger_pump.info("LA122: started.")
            else:
                logger_pump.warning("LA122 did not start!")
        if pumps_active["LA160"]:
            command = "{}?\r".format(pumps_adr["LA160"])
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
            if "{}{}".format(pumps_adr["LA160"], "I") in resp:
                logger_pump.info("LA160: started.")
            else:
                logger_pump.warning("LA160 did not start!")

    def stop(self):
        """ Stops the pump by issuing a stop command. If a program is active on the
        pump, it will pause at the current phase and resume from this phase when
        a start command is issued. Two stop commands set current phase to 0.
        """
        command = "{}stp\r".format(str(self.address))
        self.serialcon.write(command.encode())
        resp = self.serialcon.read(10).decode()
        logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))

        if str(self.address) in resp and "?" in resp:
            i = 3
            while i > 0:
                self.serialcon.write(command.encode())
                resp = self.serialcon.read(10).decode()
                logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
                if str(self.address) in resp and "?" in resp or "NA" in resp:
                    i -= 1
                elif str(self.address) + "P" in resp:
                    logger_pump.info(self.name + ": paused.")
                    break
                else:
                    logger_pump.info(self.name + ": stopped.")
                    break
            if i == 0:
                logger_pump.warning("Phase number out of range or command {} incorrect.".format(command))
                logger_pump.warning(self.name + " did not stop.")
                self.serialcon.close()
                raise PumpError("No response from pump {} at address {}.".format(self.name, self.address))
        elif str(self.address) + "P" in resp:
            logger_pump.info(self.name + ": paused.")
        else:
            logger_pump.info(self.name + ": stopped.")

    def stop_all(self, pumps_active, pumps):
        """
        This function issues a command at all pumps in the daisy-chain to start pumping.
        """
        command = "*stp\r"
        self.serialcon.write(command.encode())
        self.serialcon.reset_input_buffer()
        if pumps_active["LA120"]:  # pumps_active from main.py
            command = "{}?\r".format(pumps["LA120"])
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
            if "{}{}".format(pumps["LA120"], "P") in resp:
                logger_pump.info("LA120: paused.")
            elif "{}{}".format(pumps["LA120"], "S") in resp:
                logger_pump.info("LA120: stopped.")
            else:
                logger_pump.warning("LA120 did not stop!")
        if pumps_active["LA122"]:
            command = "{}?\r".format(pumps["LA122"])
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
            if "{}{}".format(pumps["LA122"], "P") in resp:
                logger_pump.info("LA122: paused.")
            elif "{}{}".format(pumps["LA122"], "S") in resp:
                logger_pump.info("LA122: stopped.")
            else:
                logger_pump.warning("LA122 did not stop!")
        if pumps_active["LA160"]:
            command = "{}?\r".format(pumps["LA160"])
            self.serialcon.write(command.encode())
            resp = self.serialcon.read(10).decode()
            logger_pump.debug("{}: command: {}, response: {}".format(self.name, command, resp))
            if "{}{}".format(pumps["LA160"], "P") in resp:
                logger_pump.info("LA160: paused.")
            elif "{}{}".format(pumps["LA160"], "S") in resp:
                logger_pump.info("LA160: stopped.")
            else:
                logger_pump.warning("LA160 did not stop!")
# TODO
# find the range the pumps can operate in (diamter & Flow rate)
# LA160: variable Pumpgeschwindigkeiten: 0.0262 cm/h bis 3.3327 cm/min
# LA120: variable Pumpgeschwindigkeiten: 0.0262 cm/h bis 3.3327 cm/min
# LA122: variable Pumpgeschwindigkeiten: 0,000085 cm/h bis 0,22 cm/min
