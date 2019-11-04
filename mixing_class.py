import ramping_class as ramp
import Module_pumps as p
import channels as c


class Mixing(object):
    """ This class asks the user rate and volume of each mixing step for each pump.
    These inputs are written to the respective pumps with their respective
    phase number and an overlap is inserted between each mixing process.
    """
    def __init__(self, ramping_instance=0, channel=0):
        """ Holds all the necessary attributes and functions."""
        self.ramping = ramping_instance
        self.overlap = 8
        self.runs = 1
        self.diameter_LA120 = 0
        self.diameter_LA122 = 0
        self.diameter_LA160 = 0
        self.rates_LA120 = []
        self.rates_LA122 = []
        self.rates_LA160 = []
        self.volumes_LA120 = []
        self.volumes_LA122 = []
        self.volumes_LA160 = []
        self.overlap_LA120 = []
        self.overlap_LA122 = []
        self.overlap_LA160 = []
        self.pump_configuration_n = {}  # how many syringes are in which pump?
        self.pump_configuration_syr = {}  # Which syringes are in which pump?
        self.dict_inlets_pumps = {}  # which inlet is connected to which pump?
        self.possible_units = ["\u03BCl/min", "\u03BCl/h", "ml/min", "ml/h"]
        self.dict_units_pumps = {}  # units used by each pump.
        self.name = []  # name of each run (e.g. overlap, run 1)
        self.dict_last_flowrate = {}  # stores the flow rate for each pump that
        # was selected to pump the final product into the collector
        self.dict_last_volume = {}  # stores the volume for each pump that
        # was selected to pump the final product into the collector
        self.end_time = 0  # time that is needed to flush the final product
        # from the channel
        self.channel_used = 0
        self.dict_rates_pumps = {}  # holds the flow rates of the first run

        def _standalone():
            """ This function is called on initialisation of the class and
            checks for the presence of certain objects (specific:
            pump_configuration_n) to decide if syringe number & type and pump
            connections need to be asked from the user.
            """
            if ramping_instance == 0:
                self.ramping = ramp.Ramping(channel)
                self.ramping.syringes_number(pumps_active)
                self.ramping.syringes_type(dict_pump_instances)
                self.ramping.tubing_connections()
            self.pump_configuration_n = self.ramping.pump_configuration_n
            self.pump_configuration_syr = self.ramping.pump_configuration_syr
            self.dict_inlets_pumps = self.ramping.dict_inlets_pumps

        _standalone()

    def number_of_runs(self):
        """ This function establishes the number of runs to be executed and
        stores them in a variable. Default is 1. If number of runs > 1,
        self.overlap() is called to allow for customization of overlap volume.
        """
        print("How many runs do you want to make?")
        runs = input("> ")
        try:
            self.runs = int(runs)
            p.logger_pump.info("Number of runs: {}".format(self.runs))
        except ValueError:
            print("Please choose a number (type: integer).")
            return self.number_of_runs()

    def rate(self, pumps_active):
        """ This function asks the user rates to each run.
        """
        for i in range(self.runs):
            if pumps_active[sorted(pumps_active)[0]]:  # pumps_active: dict aus 'main.py', [0]: LA120
                print("What is the flow rate for run {} for pump {}?".format(i+1, sorted(pumps_active)[0]))
                rate = input("> ").replace(",", ".")
                try:
                    self.rates_LA120.append(float(rate))
                    p.logger_pump.info("Run {}: {}'s rate is {}.".format(i+1, sorted(pumps_active)[0],
                                                                         self.rates_LA120[-1]))
                except ValueError:
                    print("Please choose a number.")
                    return self.rate(pumps_active)
                if i == 0:
                    print("Select the unit for all flow rates for pump {}:".format(sorted(pumps_active)[0]))
                    for unit in self.possible_units:
                        print("{}: {}".format(self.possible_units.index(unit) + 1, unit))
                    unit = input("> ")
                    try:
                        if int(unit) <= len(self.possible_units):
                            self.dict_units_pumps[sorted(pumps_active)[0]] = self.possible_units[int(unit) - 1]
                            print("{}'s unit is {}.".format(sorted(pumps_active)[0],
                                                            self.dict_units_pumps[sorted(pumps_active)[0]]))
                        else:
                            print("There is no unit with number {}.".format(unit))
                            return self.rate(pumps_active)
                    except ValueError:
                        print("Please select a number between 1 and {}.".format(len(self.possible_units)))
                        return self.rate(pumps_active)

            if pumps_active[sorted(pumps_active)[1]]:  # LA122
                print("What is the flow rate for run {} for pump {}?".format(i+1, sorted(pumps_active)[1]))
                rate = input("> ").replace(",", ".")
                try:
                    self.rates_LA122.append(float(rate))
                    p.logger_pump.info("Run {}: {}'s rate is {}.".format(i+1, sorted(pumps_active)[1],
                                                                         self.rates_LA122[-1]))
                except ValueError:
                    print("Please choose a number.")
                    return self.rate(pumps_active)
                if i == 0:
                    print("Select the flow rate's unit:")
                    for unit in self.possible_units:
                        print("{}: {}".format(self.possible_units.index(unit) + 1, unit))
                    unit = input("> ")
                    try:
                        if int(unit) <= len(self.possible_units):
                            self.dict_units_pumps[sorted(pumps_active)[1]] = self.possible_units[int(unit) - 1]
                            print("{}'s unit is {}.".format(sorted(pumps_active)[1],
                                                            self.dict_units_pumps[sorted(pumps_active)[1]]))
                        else:
                            print("There is no unit with number {}.".format(unit))
                            return self.rate(pumps_active)
                    except ValueError:
                        print("Please select a number between 1 and {}.".format(len(self.possible_units)))
                        return self.rate(pumps_active)

            if pumps_active[sorted(pumps_active)[2]]:  # LA160
                print("What is the flow rate for run {} for pump {}?".format(i+1, sorted(pumps_active)[2]))
                rate = input("> ").replace(",", ".")
                try:
                    self.rates_LA160.append(float(rate))
                    p.logger_pump.info("Run {}: {}'s rate is {}.".format(i+1,
                                                                         sorted(pumps_active)[2],
                                                                         self.rates_LA160[-1]))
                except ValueError:
                    print("Please choose a number.")
                    return self.rate(pumps_active)
                if i == 0:
                    print("Select the flow rate's unit:")
                    for unit in self.possible_units:
                        print("{}: {}".format(self.possible_units.index(unit) + 1, unit))
                    unit = input("> ")
                    try:
                        if int(unit) <= len(self.possible_units):
                            self.dict_units_pumps[sorted(pumps_active)[2]] = self.possible_units[int(unit) - 1]
                            print("{}'s unit is {}.".format(sorted(pumps_active)[2],
                                                            self.dict_units_pumps[sorted(pumps_active)[2]]))
                        else:
                            print("There is no unit with number {}.".format(unit))
                            return self.rate(pumps_active)
                    except ValueError:
                        print("Please select a number between 1 and {}.".format(len(self.possible_units)))
                        return self.rate(pumps_active)
            # append the run's name to self.name for the countdown function to use.
            self.name.append("run {}".format(i + 1))

    def volume(self, pumps_active):
        """ This function asks the user volumes to each run.
        """
        for i in range(self.runs):
            if pumps_active[sorted(pumps_active)[0]]:  # LA120
                print("What is the volume for run {} for pump {}?".format(i+1, sorted(pumps_active)[0]))
                volume = input("> ").replace(",", ".")
                try:
                    self.volumes_LA120.append(float(volume))
                    p.logger_pump.info("Run {}: {}'s volume is {} {}.".format(i+1,
                                                                              sorted(pumps_active)[0],
                                                                              self.volumes_LA120[-1],
                                                                              self.dict_units_pumps[sorted(
                                                                                  pumps_active)[0]][:2]))
                except ValueError:
                    print("Please choose a number.")
                    return self.volume(pumps_active)
            if pumps_active[sorted(pumps_active)[1]]:  #  LA122
                print("What is the volume for run {} for pump {}?".format(i+1, sorted(pumps_active)[1]))
                volume = input("> ").replace(",", ".")
                try:
                    self.volumes_LA122.append(float(volume))
                    p.logger_pump.info("Run {}: {}'s volume is {} {}.".format(i+1,
                                                                              sorted(pumps_active)[1],
                                                                              self.volumes_LA122[-1],
                                                                              self.dict_units_pumps[sorted(
                                                                                  pumps_active)[1]][:2]))
                except ValueError:
                    print("Please choose a number.")
                    return self.volume(pumps_active)
            if pumps_active[sorted(pumps_active)[2]]:  # LA160
                print("What is the volume for run {} for pump {}?".format(i+1, sorted(pumps_active)[2]))
                volume = input("> ").replace(",", ".")
                try:
                    self.volumes_LA160.append(float(volume))
                    p.logger_pump.info("Run {}: {}'s volume is {} {}.".format(i+1,
                                                                              sorted(pumps_active)[2],
                                                                              self.volumes_LA160[-1],
                                                                              self.dict_units_pumps[sorted(
                                                                                  pumps_active)[2]][:2]))
                except ValueError:
                    print("Please choose a number.")
                    return self.volume(pumps_active)

    def overlap_calc(self):
        """ This function asks for the overlap between runs and
        stores them in a variable. Default is 8 \u03BCl. Afterwards, it adds volumes
        and rates in between runs in self.rates_LAxxx und self.vol_LAxxx.
        """
        print("How much overlap [\u03BCl] do you want to have between runs?")
        overlap = input("> ")
        try:
            self.overlap = float(overlap)
            p.logger_pump.info("Overlap: {}".format(self.overlap))
        except ValueError:
            print("Please choose a number (type: float).")
            return self.overlap_calc()
        # calculate relative overlap for each pump

        def _relative_overlap_calc(rates_list):
            for j in range(0, len(rates_list)):
                # calculate total flow rate
                flowrate = 0
                if self.rates_LA120:
                    flowrate += self.rates_LA120[j] * self.pump_configuration_n["LA120"]
                if self.rates_LA122:
                    flowrate += self.rates_LA122[j] * self.pump_configuration_n["LA122"]
                if self.rates_LA160:
                    flowrate += self.rates_LA160[j] * self.pump_configuration_n["LA160"]
                # calculate relative flow rates and store it in self.overlap_LA1xx
                if self.rates_LA120:
                    self.overlap_LA120.append(self.rates_LA120[j]/flowrate *
                                              self.pump_configuration_n["LA120"] *
                                              self.overlap)
                if self.rates_LA122:
                    self.overlap_LA122.append(self.rates_LA122[j]/flowrate *
                                              self.pump_configuration_n["LA122"] *
                                              self.overlap)
                if self.rates_LA160:
                    self.overlap_LA160.append(self.rates_LA160[j]/flowrate *
                                              self.pump_configuration_n["LA160"] *
                                              self.overlap)
        if self.rates_LA120:
            _relative_overlap_calc(self.rates_LA120)
            for i in range(len(self.overlap_LA120)):
                self.name.insert(i*2, "overlap {}".format(i))
            del self.name[0]
        elif self.rates_LA122:
            _relative_overlap_calc(self.rates_LA122)
            for i in range(len(self.overlap_LA122)):
                self.name.insert(i*2, "overlap {}".format(i))
            del self.name[0]
        elif self.rates_LA160:
            _relative_overlap_calc(self.rates_LA160)
            for i in range(len(self.overlap_LA160)):
                self.name.insert(i*2, "overlap {}".format(i))
            del self.name[0]
        # insert relative overlap into each self.volume
        for i in range(0, len(self.volumes_LA120)):
            self.volumes_LA120.insert(i*2, self.overlap_LA120[i])
        if self.volumes_LA120:
            del self.volumes_LA120[0]  # removes first item in the list. Overlap is only necessary between runs.
        for i in range(0, len(self.volumes_LA122)):
            self.volumes_LA122.insert(i*2, self.overlap_LA122[i])
        if self.volumes_LA122:
            del self.volumes_LA122[0]
        for i in range(0, len(self.volumes_LA160)):
            self.volumes_LA160.insert(i*2, self.overlap_LA160[i])
        if self.volumes_LA160:
            del self.volumes_LA160[0]
        # insert overlap flow rate (rate of the next run) into each self.rate
        for i in range(0, len(self.rates_LA120)):
            self.rates_LA120.insert(i*2, self.rates_LA120[i*2])  # *2 because with each iteration of the loop the
            # length of rates.LA120 grows
        if self.rates_LA120:
            del self.rates_LA120[0]
        for i in range(0, len(self.rates_LA122)):
            self.rates_LA122.insert(i*2, self.rates_LA122[i*2])
        if self.rates_LA122:
            del self.rates_LA122[0]
        for i in range(0, len(self.rates_LA160)):
            self.rates_LA160.insert(i*2, self.rates_LA160[i*2])
        if self.rates_LA160:
            del self.rates_LA160[0]

    def end_process(self, channels_instance, pumps_active):
        """ This functions asks which pumps should be used to transport
        the product of the final mixing step to the outlet.
        """
        print("Do you want to pump the product of the final mixing run into the collector?")
        answer = input("> ")
        if "y" in answer.lower():
            pumps_end_process = []
            volume = channels_instance.channel_volume + channels_instance.volume_tubing("outlet")
            print("""Which pump(s) will pump the product of the final mixing
            run ({} \u03BCl)?
            Choose one or more numbers:""".format(volume))
            if pumps_active["LA120"]:
                print("1: LA120")
            if pumps_active["LA122"]:
                print("2: LA122")
            if pumps_active["LA160"]:
                print("3: LA160")
            user_input = input("> ")
            if "1" in user_input:
                pumps_end_process.append("LA120")
            if "2" in user_input:
                pumps_end_process.append("LA122")
            if "3" in user_input:
                pumps_end_process.append("LA160")
            if str(user_input) not in "123":
                print("Please choose a number.")
                return self.end_process(channels_instance, pumps_active)
            p.logger_pump.info("""The following pumps will pump the
                               final product: {}""".format(", ".join(pumps_end_process)))
            # calculate relative flow rates and add them to
            # dict_last_flowrate and dict_last_volume.
            last_flowrate = []
            if self.rates_LA120:
                last_flowrate.append(self.rates_LA120[-1] *
                                     self.pump_configuration_n["LA120"])
            if self.rates_LA122:
                last_flowrate.append(self.rates_LA122[-1] *
                                     self.pump_configuration_n["LA122"])
            if self.rates_LA160:
                last_flowrate.append(self.rates_LA160[-1] *
                                     self.pump_configuration_n["LA160"])
            last_flowrate_sum = sum(last_flowrate)
            rate_per_pump = last_flowrate_sum / len(pumps_end_process)
            # write the time for flushing the final product from the channel
            # to self.end_time.
            time_sec = volume / last_flowrate_sum
            if "h" in self.dict_units_pumps.values():
                time_sec = round(time_sec * 3600)
            elif "min" in self.dict_units_pumps.values():
                time_sec = round(time_sec * 60)
            self.end_time = time_sec
            # calculate relative flow rates and volumes and store them
            # in the respective dicts
            if "LA120" in pumps_end_process:
                self.dict_last_flowrate["LA120"] = (rate_per_pump /
                                                    self.pump_configuration_n["LA120"]
                                                    )
                self.dict_last_volume["LA120"] = (volume / len(pumps_end_process) /
                                                  self.pump_configuration_n["LA120"])

            if "LA122" in pumps_end_process:
                self.dict_last_flowrate["LA122"] = (rate_per_pump /
                                                    self.pump_configuration_n["LA122"]
                                                    )
                self.dict_last_volume["LA122"] = (volume / len(pumps_end_process) /
                                                  self.pump_configuration_n["LA122"])
            if "LA160" in pumps_end_process:
                self.dict_last_flowrate["LA160"] = (rate_per_pump /
                                                    self.pump_configuration_n["LA160"]
                                                    )
                self.dict_last_volume["LA160"] = (volume / len(pumps_end_process) /
                                                  self.pump_configuration_n["LA160"])

    def writing(self, pumps_instances_dict, channels_instance, pumps_active, global_phase_number):
        """ Asks for overlap and writes the rates and volumes to the pumps
        together with the global phase number
        """

        self.overlap_calc()
        self.end_process(channels_instance, pumps_active)
        if "LA120" in pumps_instances_dict:
            LA120 = pumps_instances_dict["LA120"]
        if "LA122" in pumps_instances_dict:
            LA122 = pumps_instances_dict["LA122"]
        if "LA160" in pumps_instances_dict:
            LA160 = pumps_instances_dict["LA160"]
        # decide which list to use to iterate over all items.
        if pumps_active["LA120"]:
            length_rate_list = len(self.rates_LA120)
        elif pumps_active["LA122"]:
            length_rate_list = len(self.rates_LA122)
        elif pumps_active["LA160"]:
            length_rate_list = len(self.rates_LA160)

        for iterator in range(length_rate_list):
            phn = global_phase_number.next()  # returns the current phase number and adds 1
            if self.rates_LA120:
                LA120.phase_number(phn)
                LA120.rate(self.rates_LA120[iterator], self.dict_units_pumps["LA120"])
                LA120.volume(self.volumes_LA120[iterator], self.dict_units_pumps["LA120"][:2])
                if iterator == 0:
                    self.dict_rates_pumps["LA120"] = self.rates_LA120[0]
            if self.rates_LA122:
                LA122.phase_number(phn)
                LA122.rate(self.rates_LA122[iterator], self.dict_units_pumps["LA122"])
                LA122.volume(self.volumes_LA122[iterator], self.dict_units_pumps["LA122"][:2])
                if iterator == 0:
                    self.dict_rates_pumps["LA122"] = self.rates_LA122[0]
            if self.rates_LA160:
                LA160.phase_number(phn)
                LA160.rate(self.rates_LA160[iterator], self.dict_units_pumps["LA160"])
                LA160.volume(self.volumes_LA160[iterator], self.dict_units_pumps["LA160"][:2])
                if iterator == 0:
                    self.dict_rates_pumps["LA160"] = self.rates_LA160[0]
        for i in range(length_rate_list):
            pump1 = ""
            pump2 = ""
            pump3 = ""
            if "LA120" in self.pump_configuration_n.keys():
                pump1 = "{}: {} {}, {} {}".format("LA120",
                                                  self.rates_LA120[i],
                                                  self.dict_units_pumps["LA120"],
                                                  round(self.volumes_LA120[i], 2),
                                                  self.dict_units_pumps["LA120"][:2]
                                                  )
            if "LA122" in self.pump_configuration_n.keys():
                pump2 = "{}: {} {}, {} {}".format("LA122",
                                                  self.rates_LA122[i],
                                                  self.dict_units_pumps["LA122"],
                                                  round(self.volumes_LA122[i], 2),
                                                  self.dict_units_pumps["LA122"][:2]
                                                  )
            if "LA160" in self.pump_configuration_n.keys():
                pump3 = "{}: {} {}, {} {}".format("LA160",
                                                  self.rates_LA160[i],
                                                  self.dict_units_pumps["LA160"],
                                                  round(self.volumes_LA160[i], 2),
                                                  self.dict_units_pumps["LA160"][:2]
                                                  )
            p.logger_pump.info("{}:\n{}.\n{}.\n{}.\n".format(self.name[i], pump1, pump2, pump3))
            # insert end volume and rate into the pumping program
        phn = global_phase_number.next()  # returns the current phase number and adds 1
        pump1_end = ""
        pump2_end = ""
        pump3_end = ""
        if "LA120" in self.dict_last_flowrate.keys():
            LA120.phase_number(phn)
            LA120.rate(self.dict_last_flowrate["LA120"], self.dict_units_pumps["LA120"])
            LA120.volume(self.dict_last_volume["LA120"], self.dict_units_pumps["LA120"][:2])
            pump1_end = "{}: {} {}, {} {}".format("LA120",
                                                  round(self.dict_last_flowrate["LA120"]),
                                                  self.dict_units_pumps["LA120"],
                                                  round(self.dict_last_volume["LA120"]),
                                                  self.dict_units_pumps["LA120"][:2]
                                                  )
        if "LA122" in self.dict_last_flowrate.keys():
            LA122.phase_number(phn)
            LA122.rate(self.dict_last_flowrate["LA122"], self.dict_units_pumps["LA122"])
            LA122.volume(self.dict_last_volume["LA122"], self.dict_units_pumps["LA122"][:2])
            pump2_end = "{}: {} {}, {} {}".format("LA122",
                                                  round(self.dict_last_flowrate["LA122"]),
                                                  self.dict_units_pumps["LA122"],
                                                  round(self.dict_last_volume["LA122"]),
                                                  self.dict_units_pumps["LA122"][:2]
                                                  )
        if "LA160" in self.dict_last_flowrate.keys():
            LA160.phase_number(phn)
            LA160.rate(self.dict_last_flowrate["LA160"], self.dict_units_pumps["LA160"])
            LA160.volume(self.dict_last_volume["LA160"], self.dict_units_pumps["LA160"][:2])
            pump3_end = "{}: {} {}, {} {}".format("LA160",
                                                  round(self.dict_last_flowrate["LA160"]),
                                                  self.dict_units_pumps["LA160"],
                                                  round(self.dict_last_volume["LA160"]),
                                                  self.dict_units_pumps["LA160"][:2]
                                                  )
        p.logger_pump.info("End run:\n{}.\n{}.\n{}.\n".format(pump1_end,
                                                              pump2_end,
                                                              pump3_end))

    def mixing(self, channel_used, countdown, dict_pump_instances, channel_instance,
               pumps_active, pumps_adr, ramping_time=0, dict_rate_pumps={}):
        """ This function checks which channel is used and starts the pumps.

        If the double meander channel is used, it asks if the user
        wants to pump the educts at the different inlets
        at different times. Then it calculates the time difference
        and starts the pumps.
        If an unknown channel is chosen, it asks the user if one of
        the known channels should be used.
        """
        if pumps_active["LA120"]:
            pump_instance = dict_pump_instances["LA120"]
        elif pumps_active["LA122"]:
            pump_instance = dict_pump_instances["LA122"]
        elif pumps_active["LA160"]:
            pump_instance = dict_pump_instances["LA160"]
        if channel_used == "Single meander channel":  # aus main.py select_channel()
            pump_instance.start_all(pumps_active, pumps_adr)
            if ramping_time > 0:  # surrogate test if the ramping class was instantiated before.
                countdown(ramping_time, "ramping:")
            dead_volume = channel_instance.channel_volume + channel_instance.volume_tubing("outlet")
            total_V = []
            total_FR = []
            time = 0
            # calculate time that the reactants need to get to the outlet
            if self.volumes_LA120:
                for i in range(len(self.volumes_LA120)):
                    vol = self.volumes_LA120[i]
                    rat = self.rates_LA120[i]
                    if self.volumes_LA122:
                        vol += self.volumes_LA122[i]
                        rat += self.rates_LA122[i]
                    if self.volumes_LA160:
                        vol += self.volumes_LA160[i]
                        rat += self.rates_LA160[i]
                    total_V.append(vol)
                    total_FR.append(rat)

            elif self.volumes_LA122:
                for i in range(len(self.volumes_LA122)):
                    vol = self.volumes_LA122[i]
                    rat = self.rates_LA122[i]
                    if self.volumes_LA160:
                        vol += self.volumes_LA160[i]
                        rat += self.rates_LA160[i]
                    total_V.append(vol)
                    total_FR.append(rat)

            elif self.volumes_LA160:
                for i in range(len(self.volumes_LA160)):
                    total_V.append(self.volumes_LA160[i])
                    total_FR.append(self.rates_LA160[i])

            for i in range(len(total_V)):
                if dead_volume > total_V[i]:
                    time += total_V[i] / total_FR[i] * 3600
                    dead_volume -= total_V[i]
                elif dead_volume < 0:
                    break
                else:
                    time += dead_volume / total_FR[i] * 3600
                    break
            countdown(time, "waste")

            if self.rates_LA120:
                for i in range(len(self.rates_LA120)):
                    times = self.volumes_LA120[i] / self.rates_LA120[i]
                    if "h" in self.dict_units_pumps["LA120"]:
                        time_s = round(times * 3600)
                    elif "min" in self.dict_units_pumps["LA120"]:
                        time_s = round(times * 60)
                    countdown(time_s, self.name[i])

            elif self.rates_LA122:
                for i in range(len(self.rates_LA122)):
                    times = self.volumes_LA122[i] / self.rates_LA122[i]
                    if "h" in self.dict_units_pumps["LA122"]:
                        time_s = round(times * 3600)
                    elif "min" in self.dict_units_pumps["LA122"]:
                        time_s = round(times * 60)
                    countdown(time_s, self.name[i])

            elif self.rates_LA160:
                for i in range(len(self.rates_LA160)):
                    times = self.volumes_LA160[i] / self.rates_LA160[i]
                    if "h" in self.dict_units_pumps["LA160"]:
                        time_s = round(times * 3600)
                    elif "min" in self.dict_units_pumps["LA160"]:
                        time_s = round(times * 60)
                    countdown(time_s, self.name[i])
            countdown(self.end_time, "End run")

        elif channel_used == "Double meander channel":
            volume_to_mixing_2 = channel_instance.volume_to_mixing_2()
            volume_mixing_2_to_outlet = (channel_instance.volume_channel_section("mixing_2-meander_2") +
                                         channel_instance.volume_channel_section("meander_2-meander_2") +
                                         channel_instance.volume_channel_section("meander_2-outlet") +
                                         channel_instance.volume_tubing("outlet")
                                         )
            # self.dict_inlets_pumps = {}  # holds {'inlet_1-1': 'LA160', 'inlet_1-2': 'LA120', 'inlet_1-3': 'LA160'}
            # self.dict_units_pumps = {}  # holds {'LA120': 'ul/h', 'LA160': 'ul/h'}
            if dict_rate_pumps:
                self.dict_rates_pumps = dict_rate_pumps

            # calculate time reactants need to get to the second inlet
            # convert time to seconds in dict_rates_pumps
            if "h" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_1-1"]]:
                rate_pump_inlet_11 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_1-1"]] / 3600  # change vol / sec
            elif "min" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_1-1"]]:
                rate_pump_inlet_11 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_1-1"]] / 60  # change vol / sec
            if "h" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_1-2"]]:
                rate_pump_inlet_12 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_1-2"]] / 3600  # change vol / sec
            elif "min" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_1-2"]]:
                rate_pump_inlet_12 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_1-2"]] / 60  # change vol / sec
            if "h" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_2-1"]]:
                rate_pump_inlet_21 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_2-1"]] / 3600  # change vol / sec
            elif "min" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_2-1"]]:
                rate_pump_inlet_21 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_2-1"]] / 60  # change vol / sec
            if "h" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_2-2"]]:
                rate_pump_inlet_22 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_2-2"]] / 3600  # change vol / sec
            elif "min" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_2-2"]]:
                rate_pump_inlet_22 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_2-2"]] / 60  # change vol / sec

            time_to_mixing_2 = round(volume_to_mixing_2 / (rate_pump_inlet_11 + rate_pump_inlet_12))

            # calculate time reactants need to get to the outlet
            time_to_outlet = round(volume_mixing_2_to_outlet / (rate_pump_inlet_11 +
                                                                rate_pump_inlet_12 +
                                                                rate_pump_inlet_21 +
                                                                rate_pump_inlet_22
                                                                ))
            p.logger_pump.debug("""time to mixing 2: {} s
                                time to outlet: {} s""".format(time_to_mixing_2,
                                                               time_to_outlet))

            pump_instance.start_all(pumps_active, pumps_adr)
            if ramping_time > 0:  # surrogate test if the ramping class was instantiated before.
                countdown(ramping_time, "Waste: ramping:")
                pump_inlet_2 = dict_pump_instances[self.dict_inlets_pumps["inlet_2-1"]]
                pump_inlet_2.stop()
                countdown(time_to_mixing_2, "Waste (mixing 1 -> mixing 2): ")
                print("\n")
                pump_inlet_2.start()
                countdown(time_to_outlet, "Waste(mixing 2 -> outlet): ")
                print("\n")

            # TODO: introduce possibility to change syringes and immediately start mixing again without having to
            #  start the whole procedure again
            if self.rates_LA120:
                for i in range(len(self.rates_LA120)):
                    times = self.volumes_LA120[i] / self.rates_LA120[i]
                    if "h" in self.dict_units_pumps["LA120"]:
                        time_s = round(times * 3600)
                    elif "min" in self.dict_units_pumps["LA120"]:
                        time_s = round(times * 60)
                    countdown(time_s, self.name[i])
            elif self.rates_LA122:
                for i in range(len(self.rates_LA122)):
                    times = self.volumes_LA122[i] / self.rates_LA122[i]
                    if "h" in self.dict_units_pumps["LA122"]:
                        time_s = round(times * 3600)
                    elif "min" in self.dict_units_pumps["LA122"]:
                        time_s = round(times * 60)
                    countdown(time_s, self.name[i])
            elif self.rates_LA160:
                for i in range(len(self.rates_LA160)):
                    times = self.volumes_LA160[i] / self.rates_LA160[i]
                    if "h" in self.dict_units_pumps["LA160"]:
                        time_s = round(times * 3600)
                    elif "min" in self.dict_units_pumps["LA160"]:
                        time_s = round(times * 60)
                    countdown(time_s, self.name[i])
            countdown(self.end_time, "End run")

        else:
            print("""Either there is a spelling issue in the attribute 'channel_dict' in
                  channels.py or a new channel design was added to channels.py.
                  In the first case please compare spelling of the channel name in
                  mixing(self) in mixing_class.py against channel_dict in channels.py.
                  In the second case please write a function to cover your new
                  channels' properties.\n""")
            print("""Do you want to execute the program for the single or double
                  meander channel anyway?""")
            resp = input("Yes/No >")
            if "Y" in resp or "y" in resp:
                for item in sorted(c.channel_dict):
                    print("{}: {}".format(sorted(c.channel_dict).index(item) + 1, item))
                channel_number = input("> ")
                try:
                    number = int(channel_number)
                    if number <= len(sorted(c.channel_dict)):
                        self.channel_used = sorted(c.channel_dict)[number - 1]  # TODO: irgendwie muss ich diese Auswahl
                        # noch in global bekommen, damit auch mixing_class.py darauf zugreifen kann.
                        p.logger_pump.info("Selected channel: {}.".format(self.channel_used))
                        return self.mixing(channel_used, countdown, dict_pump_instances, channel_instance,
                                           pumps_active, pumps_adr, ramping_time=0, dict_rate_pumps={})  # return mixing()?
                    else:
                        print("There is no channel with number {}.".format(number))
                        return self.mixing(channel_used, countdown, dict_pump_instances, channel_instance,
                                           pumps_active, pumps_adr, ramping_time=0, dict_rate_pumps={})
                except ValueError:
                    print("Please select a number between 1 and {}.".format(len(sorted(c.channel_dict))))
                    return self.mixing(channel_used, countdown, dict_pump_instances, channel_instance,
                                       pumps_active, pumps_adr, ramping_time=0, dict_rate_pumps={})
