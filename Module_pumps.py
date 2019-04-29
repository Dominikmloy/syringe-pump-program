import serial
import logging
import datetime
import os


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
                    filename= filepath,
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
    describe function of this class
    """
    #configure serial settings and start logging
    def __init__(self, port):
        serial.Serial.__init__(self, port=port, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, timeout=2)
        # port = port
        # baudrate = 9600
        # bytesize = "EIGHTBITS" # confirm
        # parity = "PARITY_NONE" # confirm
        # stopbits = "STOPBITS_ONE"
        # write_timeout = 2 # seconds

        self.flushOutput()
        self.flushInput()

        logger_pump.info("Chain created on %s", port)#"\n{port},\n{baudrate},\n{bytesize},\n{parity},\n{stopbits},\n{write_timeout}")

    def serial_read(self):
        response=port.read(1)
        logger_pump.info(response)

class PumpError(Exception):
    pass

class Pump(object):
# TODO: Check flowrate ranges of pumps and integrate checks
# that will throw errors if pump is supposed to pump faster than possible
    """
    This class holds all functions for HLL pumps.
    """
    def __init__(self, chain, name, address):
        # pump needs to be initialized with address and name (optional)
        # a check needs to be performed to make sure pump is responding
        # result of this check must be logged and error must be raised
        # if not responding.
        self.name = name
        self.address = address
        self.serialcon = chain

        try:
            self.serialcon.write(str(self.address) + 'VER\r')
            resp = self.serialcon.read(17)
            logger_pump.info(resp)

            if resp[1:3] != str(self.address):
                raise PumpError('No response from pump at address %s' %
                                self.address)
        except PumpError:
            self.serialcon.close()
            raise

        logger_pump.info('%s: created at address %s on %s', self.name,
                      self.address, self.serialcon.port)


    def diameter(self):
        pass

    def volume(self):
        pass

    def rate(self):
        pass

    def start(self):
        self.serialcon.write(str(self.address) + "run\r")
        resp = self.serialcon.read(17)
        logger_pump.info(resp)


    def stop(self):
        self.serialcon.write(str(self.address) + "stp\r")
        resp = self.serialcon.read(17)
        logger_pump.info(resp)
