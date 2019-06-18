import time
import Module_pumps as p
import syringes as s
import channels as c

def countdown(t, name):
    t = round(t)
    while t >= 0:
        mins, secs = divmod(t, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        print("{}: {}".format(name, timeformat), end= '\r')
        time.sleep(1)
        t -= 1


class GlobalPhaseNumber(object):
    curr_phn = 1

    @classmethod
    def next(cls):
        cls.curr_phn += 1
        return cls.curr_phn - 1

    @classmethod
    def reset(cls):
        cls.curr_phn = 0

        
class Setup(object):
    def __init__(self, pumps):
        self.pumps_active = {"LA120": False, "LA122": False, "LA160": False}
        self.dict_pump_instances = {"LA120": False, "LA122": False, "LA160": False}
        self.syringe_washing = 0
        self.channel_used = 0
        self.number_of_active_pumps = 0
        self.chain = p.Chain("/dev/ttyUSB0")
        self.max_flowrate = 1500  # ul/h
        self.syringes = s.Syringes()
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

    def select_syringe_washing(self):  # ask user which syringes to use.
        """
        This function lets the user choose one of the syringes from the syringes.py
        module. It is assumed that all inlets are connected to this syringe type.
        """
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
    def select_channel(self):
        """
        This function lets the user choose one of the channels from the channels.py
        module. This choice is essential to the program because the channel's
        properties define number of syringes and volume to be dispensed.
        """
        print("Select channel:")
        for item in sorted(c.channel_dict):
            print("{}: {}".format(sorted(c.channel_dict).index(item) + 1, item))
        channel_number = input("> ")
        try:
            number = int(channel_number)
            if number <= len(sorted(c.channel_dict)):
                self.channel_used = sorted(c.channel_dict)[number - 1]
                self.channel = c.Channel(c.channel_dict[self.channel_used])
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
        select_syringe_washing(). Each pump will run with the max.max_flowrate /
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

        if self.pumps_active["LA120"]:
            self.LA120.diameter(self.syringes.syringes[self.syringe_washing])
            self.LA120.volume(volume_per_syr, "ul/h")
            self.LA120.rate(rate, "ul/h")

        if self.pumps_active["LA122"]:
            self.LA122.diameter(self.syringes.syringes[self.syringe_washing])
            self.LA122.volume(volume_per_syr, "ul/h")
            self.LA122.rate(rate, "ul/h")
    
        if self.pumps_active["LA160"]:
            self.LA160.diameter(self.syringes.syringes[self.syringe_washing])
            self.LA160.volume(volume_per_syr, "ul/h")
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

    #def pump_instances(self):
     #   if self.pumps_active["LA120"]:
     #       self.dict_pump_instances["LA120"] = self.LA120
       # else:
        #    self.dict_pump_instances["LA120"] = empty_class
     #   if self.pumps_active["LA122"]:
     #       self.dict_pump_instances["LA122"] = self.LA122
        #else:
        #    self.dict_pump_instances["LA122"] = empty_class
     #   if self.pumps_active["LA160"]:
      #      self.dict_pump_instances["LA160"] = self.LA160
        #else:
        #    self.dict_pump_instances["LA160"] = empty_class
