import time
import Module_pumps as p
import syringes as s
import channels as c


def countdown(t, name):
    """ This function takes two inputs: t in seconds (float or int) and any
    string as name. The time is converted to minutes and seconds and every
    second the name and the time (dd:dd) is printed to the screen
    effectively counting down to zero.
    """
    t = round(t)
    while t >= 0:
        mins, secs = divmod(t, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        print("{}: {}".format(name, timeformat), end='\r')
        time.sleep(1)
        t -= 1
    print("\n")


class GlobalPhaseNumber(object):
    """ This class holds two classmethods to control the phase number. 'next' increases the
    phase number by +1, while 'reset' resets it to 0.
    This class is used to assign a phase number to every event, creating a defined sequence of steps.
    """
    curr_phn = 1

    @classmethod
    def next(cls):
        cls.curr_phn += 1
        return cls.curr_phn - 1

    @classmethod
    def reset(cls):
        cls.curr_phn = 0

        
class Setup(object):
    """ This class holds all functions and variables related to the setup of the micro mixer.
     Upon instantiation, it creates an instance of the Chain class from 'Module_pumps.py' and from
     the Syringes Class from the module 'syringes.py'. Afterwards, each pump is contacted and
     their status (active / inactive) is stored in a variable.
     The functions in this class are used to select the utilized channel and syringes and to wash
     the setup.
     """
    def __init__(self, pumps):
        self.pumps_active = {"LA120": False, "LA122": False, "LA160": False}
        self.dict_pump_instances = {"LA120": False, "LA122": False, "LA160": False}
        self.syringe_washing = ""  # holds a string with the name of the syringe from the syringes.py module.
        self.channel_used = ""  # holds a string with the name of the channel from the channels.py module.
        self.number_of_active_pumps = 0
        self.chain = p.Chain("/dev/ttyUSB0")  # instantiates the Chain class.
        self.max_flowrate = 0  # ul/h, can be adapted to the respective channel.
        self.syringes = s.Syringes()  # instantiates the Syringes class.
        self.channel = 0  # instance of class Channel() from channels.py. Instantiated when select_channel() is called.
        # get the information which pumps are active
        try:
            self.LA120 = p.Pump(self.chain, str(sorted(pumps)[0]), str(pumps[sorted(pumps)[0]]))
            self.pumps_active["LA120"] = True
            self.dict_pump_instances["LA120"] = self.LA120
        except p.PumpError:
            p.logger_pump.info("{} is not responding at address {}.".format(sorted(pumps)[0],
                                                                            pumps[sorted(pumps)[0]]))
        try:
            self.LA122 = p.Pump(self.chain, sorted(pumps)[1], pumps[sorted(pumps)[1]])
            self.pumps_active["LA122"] = True
            self.dict_pump_instances["LA122"] = self.LA122
        except p.PumpError:
            p.logger_pump.info("{} is not responding at address {}.".format(sorted(pumps)[1],
                                                                            pumps[sorted(pumps)[1]]))
        try:
            self.LA160 = p.Pump(self.chain, sorted(pumps)[2], pumps[sorted(pumps)[2]])
            self.pumps_active["LA160"] = True
            self.dict_pump_instances["LA160"] = self.LA160
        except p.PumpError:
            p.logger_pump.info("{} is not responding at address {}.".format(sorted(pumps)[2],
                                                                            pumps[sorted(pumps)[2]]))

    @staticmethod
    def print_dict_keys(dictionary):
        """ this function returns a string of all dictionary keys separated by commas."""
        key_list = []
        for key in dictionary:
            key_list.append(key)
        string = ", ".join(key_list)
        return string

    def select_syringe_washing(self, **kwargs):  # ask user which syringes to use.
        """
        This function lets the user choose one of the syringes from the syringes.py
        module. It is assumed that all inlets are connected to this syringe type.
        The target syringe can also be passed to the function via the **kwargs
        argument. Example: Kwarg: syringe_washing = "Hamilton_1710TLL-XL_0.1mll"
        """

        def error_message(error_number):
            """ nested function that defines the error message to be given when the
            kwargs are wrong."""
            print("Error number: {}\n".format(error_number),
                  "Error in keyword arguments provided.",
                  "\nProvided {}.\n".format(kwargs),
                  "Expected:\n'syringe_washing' = {}".format(self.print_dict_keys(self.syringes.syringes)),
                  "\nProgram aborted.")
            p.logger_pump.debug("Error message {}: ".format(number),
                                "Function 'select_syringe_washing()' aborted",
                                " due to errors in the kwargs: {}.".format(kwargs))
            raise SystemExit("Program aborted.")

        if kwargs:
            syringe_washing = kwargs.get("syringe_washing", None)
            if syringe_washing is None:
                error_message(1)
            else:
                if syringe_washing not in self.syringes.syringes.keys():
                    error_message(2)
                else:
                    self.syringe_washing = syringe_washing
                    p.logger_pump.info("Selected syringe for washing: {}.".format(self.syringe_washing))
        else:
            print("Select syringe used for washing:")
            for item in sorted(self.syringes.syringes):
                print("{}: {}".format(sorted(self.syringes.syringes).index(item) + 1, item))
            syringe_number = input("> ")
            try:
                number = int(syringe_number)
                if number <= len(sorted(self.syringes.syringes)):
                    self.syringe_washing = (sorted(self.syringes.syringes)[number - 1])
                    p.logger_pump.info("Selected syringe for washing: {}.".format(self.syringe_washing))
                else:
                    print("There is no syringe with number {}.".format(number))
                    return self.select_syringe_washing()
            except ValueError:
                print("Please select a number between 1 and {}.".format(len(sorted(self.syringes.syringes))))
                return self.select_syringe_washing()
    
    # ask user which channel is used.
    def select_channel(self, **kwargs):
        """
        This function lets the user choose one of the channels from the channels.py
        module. This choice is essential to the program because the channel's
        properties define number of syringes and volume to be dispensed.
        The target channel can also be passed to the function via the **kwargs
        argument. Example: Kwarg: channel = "Single meander channel"
        """

        def error_message(error_number):
            """ nested function that defines the error message to be given when the
            kwargs are wrong."""
            print("Error number: {}\n".format(error_number),
                  "Error in keyword arguments provided.",
                  "\nProvided {}.\n".format(kwargs),
                  "Expected:\n'channel' = {}".format(self.print_dict_keys(c.channel_dict)),
                  "\nProgram aborted.",)
            p.logger_pump.debug("Error message {}: ".format(number),
                                "Function 'select_channel()' aborted",
                                " due to errors in the kwargs: {}.".format(kwargs))
            raise SystemExit("Program aborted.")

        if kwargs:
            channel = kwargs.get("channel", None)
            if channel is None:
                error_message(1)
            else:
                if channel not in c.channel_dict.keys():
                    error_message(2)
                else:
                    self.channel_used = channel
                    self.channel = c.Channel(c.channel_dict[self.channel_used])
                    self.max_flowrate = self.channel.max_flowrate
                    p.logger_pump.info("Selected channel: {}.".format(self.channel_used))
        else:
            print("Select channel:")
            for item in sorted(c.channel_dict):
                print("{}: {}".format(sorted(c.channel_dict).index(item) + 1, item))
            channel_number = input("> ")
            try:
                number = int(channel_number)
                if number <= len(sorted(c.channel_dict)):
                    self.channel_used = sorted(c.channel_dict)[number - 1]
                    self.channel = c.Channel(c.channel_dict[self.channel_used])
                    self.max_flowrate = self.channel.max_flowrate
                    p.logger_pump.info("Selected channel: {}.".format(self.channel_used))
                else:
                    print("There is no channel with number {}.".format(number))
                    return self.select_channel()
            except ValueError:
                print("Please select a number between 1 and {}.".format(len(sorted(c.channel_dict))))
                return self.select_channel()

    def washing(self):
        """
        This function needs to be called in the beginning and end of each program to
        wash the channel. The program assumes that all inlets of the chosen channel
        from select_channel() are connected to the same syringe type from
        select_syringe_washing(). Each pump will run with self.max_flowrate /
        number of inlets. After washing has finished, syringes need to be changed.
        """
        self.number_of_active_pumps = sum(value == True for value in self.pumps_active.values())
        channel = c.Channel(c.channel_dict[self.channel_used])
        volume_tubing_total = 0
        for key in channel.tubing_x:
            volume_tubing_total += channel.volume_tubing(key)
        # wash twice channel volume
        volume_per_syr = (channel.volume_total + volume_tubing_total) * 2 / channel.inlets_number
        rate = self.max_flowrate / channel.inlets_number
        washing_time = round(volume_per_syr / rate * 3600)

        # write variables to the pumps
        if self.pumps_active["LA120"]:
            self.LA120.diameter(self.syringes.syringes[self.syringe_washing])
            self.LA120.volume(volume_per_syr, "ul")
            self.LA120.rate(rate, "ul/h")

        if self.pumps_active["LA122"]:
            self.LA122.diameter(self.syringes.syringes[self.syringe_washing])
            self.LA122.volume(volume_per_syr, "ul")
            self.LA122.rate(rate, "ul/h")
    
        if self.pumps_active["LA160"]:
            self.LA160.diameter(self.syringes.syringes[self.syringe_washing])
            self.LA160.volume(volume_per_syr, "ul")
            self.LA160.rate(rate, "ul/h")
        # the start command is issued separately because pumps will not start at the same time otherwise.
        if self.pumps_active["LA120"]:
            self.LA120.start()
        if self.pumps_active["LA122"]:
            self.LA122.start()
        if self.pumps_active["LA160"]:
            self.LA160.start()

        countdown(washing_time, "washing")

        if self.pumps_active["LA120"]:
            self.LA120.stop()
        if self.pumps_active["LA122"]:
            self.LA122.stop()
        if self.pumps_active["LA160"]:
            self.LA160.stop()
