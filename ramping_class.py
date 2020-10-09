import Module_pumps as p
import channels as c
import syringes as s


class EmptyClass(object):
    """ This class works as dummy to allow for optional arguments in writing(self)
    without raising errors if forgotten.
    """

    def phase_number(self, phn):
        p.logger_pump.warning("""The function 'writing' attempted to write {} to some pump.
                                 Please repeat the ramping process.""".format(phn))

    def rate(self, rates, units):
        p.logger_pump.warning("""The function 'writing' attempted to write {} snd {} to some pump.
                                             Please repeat the ramping process.""".format(rates, units))

    def volume(self, volumes, units):
        p.logger_pump.warning("""The function 'writing' attempted to write {} and {] to some pump.
                                             Please repeat the ramping process.""".format(volumes, units))


class Ramping(object):
    """
    This class asks the configuration of each pump (which syringe?, how many?,
    final flow rate? [that means what is the flow rate of the first mixing exp?])
    and ramps each pump's flow rate up (or down) to have each educt at the same
    time at the mixing zone. Argument 'channel' (e.g. which microfluidic channel
    is used) needs to be set upon instantiation.
    """
    def __init__(self, channel):
        """holds all the necessary attributes"""
        self.pump_max_syr = {"LA120": 2, "LA122": 2, "LA160": 8}  # max number of syringes target pump can hold.
        self.possible_units = ["\u03BCl/min", "\u03BCl/h", "ml/min", "ml/h"]
        self.steps = 10  # the ramping function's number of steps (rate + volume)
        self.channel = channel
        self.max_flowrate = 0
        self.total_flowrate = 0
        self.mean_flowrate = 350
        self.pump_configuration_n = {}  # Holds the numbers of syringes per pump, e.g., LA120: 2
        self.pump_configuration_syr = {}  # Holds the syringe's type per pump, e.g., LA120: Hamilton_1710TLL-XL_0.1ml
        self.dict_tubing_volume = {}  # Holds the channel's inlets and their resp. volumes [ul], e.g., inlet_1_1: 12
        self.dict_inlets_pumps = {}  # Holds the channel's inlets and their respective pumps, e.g., inlet_1_1: LA120
        self.dict_rates_pumps = {}  # Holds the final flow rate of the ramping process. This is the first flow rate
        # of the mixing process, as well.
        self.dict_units_pumps = {}
        self.ramping_time = 0
        self.rates_LA120 = []
        self.rates_LA122 = []
        self.rates_LA160 = []
        self.time_per_step = 0
        self.vol_LA120 = []
        self.vol_LA122 = []
        self.vol_LA160 = []
        # used to check kwargs in first_rate() for validity.
        self.units_dict = {"\u03BCl/min": "um", "\u03BCl/m": "um", "\u03BC/min": "um",
                           "ml/min": "mm", "ml/m": "mm", "m/min": "mm",
                           "\u03BCl/h": "uh", "\u03BC/h": "uh",
                           "ul/h": "uh", "u/h": "uh",
                           "ml/h": "mh", "m/h": "mh"}

        def _tubing_volume():
            """
            get the volume of each tubing connecting the syringes to
            the channel's inlets.
            """
            used_channel = c.Channel(c.channel_dict[channel])
            self.max_flowrate = used_channel.max_flowrate
            for key in used_channel.tubing_x.keys():
                if used_channel.tubing_x[key] > 0:
                    self.dict_tubing_volume[key] = used_channel.volume_tubing(key)
        _tubing_volume()

    @staticmethod
    def print_dict_keys(dictionary):
        """ this function returns a string of all dictionary keys separated by commas."""
        key_list = []
        for key in dictionary:
            key_list.append(key)
        string = ", ".join(key_list)
        return string

    def syringes_number(self, pumps_active, **kwargs):
        """
        get the number of syringes in each pump from the user and checks if target pump
        can hold as much syringes. The number of syringes per pump can also be passed
        to the function via the kwargs. Example: LA120 = 2.
        """

        def error_message(error_number):
            """ nested function that defines the error message to be given when the
            kwargs are wrong."""
            print("Error number: {}\n".format(error_number),
                  "Error in keyword arguments provided.",
                  "\nProvided {}.\n".format(kwargs),
                  "Expected:\nname of active pumps: {}".format(self.print_dict_keys(list_active_pumps)),
                  "+ number of syringes in it.",
                  "\nProgram aborted.")
            p.logger_pump.debug("Error message {}: ".format(error_number),
                                "Function 'syringes_number()' aborted",
                                " due to errors in the kwargs: {}.".format(kwargs))
            raise SystemExit("Program aborted.")

        if kwargs:
            list_active_pumps = [k for k, v in pumps_active.items() if v == True]
            if sorted(list_active_pumps) == sorted(kwargs.keys()):
                for key in kwargs:
                    try:
                        if kwargs[key] <= self.pump_max_syr[key]:
                            self.pump_configuration_n[key] = kwargs[key]
                            p.logger_pump.info("{} holds {} syringe(s).".format(key, kwargs[key]))
                        else:
                            print("Pump {} cannot hold {} syringes.".format(key, kwargs[key]))
                            error_message(1)
                    except TypeError:
                        print("'{}' is not a valid number of syringes.".format(kwargs[key]))
            else:
                error_message(2)
            if sum(self.pump_configuration_n.values()) != len(self.dict_tubing_volume) - 1:  # -1: number of outlets
                p.logger_pump.warning("Number of syringes does not match number of inlets!")

        else:
            for key in sorted(pumps_active):
                if pumps_active[key]:
                    print("How many syringes are in pump {}?".format(key))
                    number = input("> ")
                    try:
                        if int(number) <= self.pump_max_syr[key]:
                            self.pump_configuration_n[key] = int(number)
                            p.logger_pump.info("{} holds {} syringe(s).".format(key, number))
                        else:
                            print("Pump {} cannot hold {} syringes.".format(key, number))
                            return self.syringes_number(pumps_active)
                    except ValueError:
                        print("'{}' is not a valid number of syringes.".format(number))
                        return self.syringes_number(pumps_active)
            # check if number of syringes matches number of inlets.
            if sum(self.pump_configuration_n.values()) != len(self.dict_tubing_volume) - 1:  # -1: number of outlets
                print("Number of syringes does not match number of inlets.")
                return self.syringes_number(pumps_active)

    def syringes_type(self, dict_pump_instances, pumps_active, **kwargs):
        """
        get the type of syringes in each pump from the user and write their diameter
        to the respective pump. The user selects the correct syringe from a list
        of possible syringes from the module syringes.py.
        Alternatively, the syringes' type and the respective pumps can be passed
        directly to the function via the **kwargs argument.
        Example: LA120 = 'Hamilton_1001TLL_1ml'
        """
        # instantiate syringes class to enable access to the syringes' specs.
        syringes = s.Syringes()

        def error_message(error_number):
            """ nested function that defines the error message to be given when the
            kwargs are wrong."""
            print("Error number: {}\n".format(error_number),
                  "Error in keyword arguments provided.",
                  "\nProvided {}.\n".format(kwargs),
                  "Expected:\nname of active pumps: {}".format(self.print_dict_keys(list_active_pumps)),
                  "+ name of syringe type equipped to it.\nFor example: LA120 = 'Hamilton_1001TLL_1ml'.",
                  "\nProgram aborted.")
            p.logger_pump.debug("Error message {}: ".format(error_number),
                                "Function 'syringes_type()' aborted",
                                " due to errors in the kwargs: {}.".format(kwargs))
            raise SystemExit("Program aborted.")

        if kwargs:
            list_active_pumps = [k for k, v in pumps_active.items() if v == True]
            if sorted(list_active_pumps) == sorted(kwargs.keys()):
                for key in kwargs:
                    if kwargs[key] in syringes.syringes.keys():  # syringes.syringes.keys():
                        self.pump_configuration_syr[key] = kwargs[key]
                        p.logger_pump.info("{} is equipped with the syringe type {}.".format(key, kwargs[key]))
                    else:
                        print("There is no syringe named {}.".format(kwargs[key]))
                        if type(kwargs[key]) is not str:
                            print("The function expects the name of the syringe as string.")
                        error_message(1)
            else:
                error_message(2)
        else:
            for key in self.pump_configuration_n.keys():
                print("Which syringe type is in pump {}?".format(key))
                for syr in sorted(syringes.syringes):
                    print("{}: {}.".format(sorted(syringes.syringes).index(syr) + 1, syr))
                number = input("> ")
                try:
                    if int(number) <= len(sorted(syringes.syringes)):
                        self.pump_configuration_syr[key] = sorted(syringes.syringes)[int(number) - 1]
                        p.logger_pump.debug("{} is equipped with syringe {}.".format(key,
                                                                                     self.pump_configuration_syr[key]))
                    else:
                        print("There is no syringe with number {}.".format(number))
                        return self.syringes_type(dict_pump_instances, pumps_active)
                except ValueError:
                    print("Please select a number between 1 and {}.".format(len(sorted(syringes.syringes))))
                    return self.syringes_type(dict_pump_instances, pumps_active)
            for key in self.pump_configuration_syr.keys():
                pump_instance = dict_pump_instances[key]
                pump_instance.diameter(syringes.syringes[self.pump_configuration_syr[key]])
                p.logger_pump.info("{} holds {} syringe(s). Type: {}".format(key,
                                                                             self.pump_configuration_n[key],
                                                                             self.pump_configuration_syr[key]))

    def check_connections(self):
        """Checks if the number of syringes matches the number of inlets."""
        check_LA120 = sum(1 for x in self.dict_inlets_pumps.values() if x == "LA120")
        check_LA122 = sum(1 for x in self.dict_inlets_pumps.values() if x == "LA122")
        check_LA160 = sum(1 for x in self.dict_inlets_pumps.values() if x == "LA160")
        if check_LA120 > self.pump_max_syr["LA120"]:
            print("""Pump LA120 cannot hold {} syringes. 
                  Please repeat the selection process.""".format(check_LA120))
            self.tubing_connections()
        if check_LA122 > self.pump_max_syr["LA122"]:
            print("""Pump LA120 cannot hold {} syringes. 
                  Please repeat the selection process.""".format(check_LA122))
            self.tubing_connections()
        if check_LA160 > self.pump_max_syr["LA160"]:
            print("""Pump LA120 cannot hold {} syringes. 
                  Please repeat the selection process.""".format(check_LA160))
            self.tubing_connections()

    def tubing_connections(self, **kwargs):
        """
        get the connections: user  is queried: Which tubing is connected to which pump?
        After the selection process, the function checks if the inlets mapped to each
        pump do not exceed target pump's maximum channels.
        Alternatively, the mapping of the inlets to the respective pumps can be passed
        directly to the function via the **kwargs argument.
        Example: inlet_1_1 = 'LA120'
        """

        def error_message(error_number):
            """ nested function that defines the error message to be given when the
            kwargs are wrong."""
            print("Error number: {}".format(error_number),
                  "\nError in keyword arguments provided.",
                  "\nProvided {}.".format(kwargs),
                  "\nExpected: name of all(!) inlets: {}".format(self.print_dict_keys(sorted(
                      self.dict_tubing_volume.keys())[:-1])),
                  "\n+ name of active pumps: {}".format(self.print_dict_keys(self.pump_configuration_syr.keys())),
                  "\nFor example: inlet_1_1 = 'LA120'.",
                  "\nProgram aborted.")
            p.logger_pump.debug("Error message {}: ".format(error_number),
                                "Function 'tubing_connections()' aborted",
                                " due to errors in the kwargs: {}.".format(kwargs))
            raise SystemExit("Program aborted.")

        if kwargs:
            for key in self.pump_configuration_syr.keys():
                if key in kwargs.values():
                    pass
                else:
                    error_message(1)
            if sorted(kwargs.keys()) == sorted(self.dict_tubing_volume.keys())[:-1]:  # inlet_1_1: 12
                for key in kwargs:
                    self.dict_inlets_pumps[key] = kwargs[key]  # inlet_1_1: LA120
                    print("{} is connected to pump {}.".format(key, kwargs[key]))
            else:
                error_message(2)
        else:
            for inlet in sorted(self.dict_tubing_volume)[:-1]:
                print("The inlet {} is connected to which pump?".format(inlet))
                for pump in sorted(self.pump_configuration_syr):
                    print("{}: {}".format(sorted(self.pump_configuration_syr).index(pump) + 1, pump))
                pump = input("> ")
                try:
                    if int(pump) <= len(sorted(self.pump_configuration_syr)):
                        self.dict_inlets_pumps[inlet] = sorted(self.pump_configuration_syr)[int(pump) - 1]
                        p.logger_pump.info("{} is routed to pump {}.".format(inlet, self.dict_inlets_pumps[inlet]))
                    else:
                        print("There is no pump with number {}.".format(pump))
                        return self.tubing_connections()
                except ValueError:
                    print("Please select a number between 1 and {}.".format(len(sorted(self.pump_configuration_syr))))
                    return self.tubing_connections()
            # checks if number of inlets mapped to target pump exceeds number of syringes in that pump.
            if len(self.dict_inlets_pumps) != sum(self.pump_configuration_n.values()):
                p.logger_pump.warning("""There are {} inlets connected to {} syringes.
                                      Please repeat the selection process.
                                      """.format(len(self.dict_inlets_pumps),
                                      sum(self.pump_configuration_n.values())))
                self.tubing_connections()
            for key in self.dict_inlets_pumps.keys():  # log and inform user.
                p.logger_pump.debug("Routing: {} - {}".format(key, self.dict_inlets_pumps[key]))
            # after having mapped inlets to pumps, the connection process is checked.
            self.check_connections()

    def first_rate(self, **kwargs):
        """
        This function ask the user for the flow rate and volume for
        each pump that is used for the first mixing cycle. These rates
        serve as anchor points the ramping function will ramp up or down to.
        Alternatively, the pumps' rates and their respective units can be passed
        directly to the function via the **kwargs argument.
        Example: LA120_rate = 150, LA120_unit = 'ul/h'
        """

        def error_message(error_number, additional_info):
            """ nested function that defines the error message to be given when the
            kwargs are wrong. Additional information about the error can be given
            vie the second argument"""
            print("Error number: {}".format(error_number),
                  "\nError in keyword arguments provided.",
                  "\nProvided {}.".format(kwargs),
                  "\nExpected: name of all(!) active pumps: {}.".format(self.print_dict_keys(sorted(
                      self.pump_configuration_syr.keys()))),
                  "\n'_rate' or '_unit' must be appended to the pumps name"
                  "\n+ the respective rate or unit.",
                  "\nFor example: LA120_rate = 120.",
                  "\nAdditional info: ", additional_info,
                  "\nProgram aborted.")
            p.logger_pump.debug("Error message {}: ".format(error_number),
                                "Function 'first_rate()' aborted",
                                " due to errors in the kwargs: {}.".format(kwargs))
            raise SystemExit("Program aborted.")

        if kwargs:
            # surrogate test, if arguments for all active pumps are provided
            for key in self.pump_configuration_syr.keys():
                counter = ",".join(kwargs.keys()).count(key)  # counts the occurrences of the pump name
                if counter == 2:  # test if all active pumps are used in this function.
                    pass
                else:
                    error_message(1, "All active pumps must be used.")
            # check if flow rates are type integer or float. Variable total_flow_rate is not used again,
            # a separate function is used to check if max flow rate is exceeded.
            total_flow_rate = 0
            for key in kwargs:
                if 'rate' in key:
                    try:
                        total_flow_rate += kwargs[key]
                    except TypeError:
                        error_message(2, "Flow rate must be a number (int or float).")
                elif 'unit' in key:
                    if kwargs[key] in self.units_dict:
                        pass
                    else:
                        error_message(3, "The unit {} has the wrong format.".format(kwargs[key]))
                else:
                    error_message(4, "kwargs must be 'LA120_rate' or 'LA120_unit'")
            for key in kwargs:
                # distribute the kwargs to their respective category.
                if 'rate' in key:
                    self.dict_rates_pumps[key[:5]] = kwargs[key]
                    print("{}'s rate is {}.".format(key[:5], self.dict_rates_pumps[key[:5]]))
                elif 'unit' in key:
                    self.dict_units_pumps[key[:5]] = kwargs[key]
                    print("{}'s unit is {}.".format(key[:5], self.dict_units_pumps[key[:5]]))
        else:
            for pump in sorted(self.pump_configuration_n):
                print("What is the first flow rate for pump {}?".format(pump))
                rate = input("> ").replace(",", ".")
                try:
                    self.dict_rates_pumps[pump] = float(rate)
                    p.logger_pump.info("{}'s rate is {}.".format(pump, self.dict_rates_pumps[pump]))
                except ValueError:
                    print("Please choose a number.")
                    return self.first_rate()
                print("Select the flow rate's unit:")
                for unit in self.possible_units:
                    print("{}: {}".format(self.possible_units.index(unit) + 1, unit))
                unit = input("> ")
                try:
                    if int(unit) <= len(self.possible_units):
                        self.dict_units_pumps[pump] = self.possible_units[int(unit) - 1]
                        p.logger_pump.info("{}'s unit is {}.".format(pump, self.dict_units_pumps[pump]))
                    else:
                        print("There is no unit with number {}.".format(unit))
                        return self.first_rate()
                except ValueError:
                    print("Please select a number between 1 and {}.".format(len(self.possible_units)))
                    return self.first_rate()

    def calc_mean_flowrate(self, channel):
        """Calculates the mean flow rate of the ramping phase. Mean FR is
        the same on all pumps, just the range is different."""
        for key in self.pump_configuration_n.keys():  # makes sure that the pump rate is in ul/h
            if "min" in self.dict_units_pumps[key]:
                if "ml" in self.dict_units_pumps[key]:
                    self.total_flowrate += self.pump_configuration_n[key] * self.dict_rates_pumps[key] * 60 * 1000
                    self.dict_rates_pumps[key] = self.dict_rates_pumps[key] * 60 * 1000
                else:
                    self.total_flowrate += self.pump_configuration_n[key] * self.dict_rates_pumps[key] * 60
                    self.dict_rates_pumps[key] = self.dict_rates_pumps[key] * 60
            else:
                if "ml" in self.dict_units_pumps[key]:
                    self.total_flowrate += self.pump_configuration_n[key] * self.dict_rates_pumps[key] * 1000
                    self.dict_rates_pumps[key] = self.dict_rates_pumps[key] * 1000
                else:
                    self.total_flowrate += self.pump_configuration_n[key] * self.dict_rates_pumps[key]
        # print a error warning if max flow rate is exceeded and ask the user to abort the program.
        if self.total_flowrate > self.max_flowrate:
            p.logger_pump.warning("WARNING! TOTAL FLOW RATE EXCEEDS MAXIMUM FLOW RATE! ({})".format(self.max_flowrate))
            print("Do you want to abort the program?")
            answer = input("> ")
            positive_answers = ["y", "j", "yes", "ja"]
            if answer.lower() in positive_answers:
                p.logger_pump.debug("Program aborted.")
                raise SystemExit("Program aborted.")
            else:
                p.logger_pump.info("Program continuing.")
        # calculate mean flow rate
        highest_rate = max(j for i, j in self.dict_rates_pumps.items() if j > 0)
        ramping_list = [self.total_flowrate * 0.25]
        while len(ramping_list) < self.steps:
            ramping_list.append(ramping_list[-1] + (highest_rate - ramping_list[0])/9)
        # mean flow rate is set manually to decrease the possibility of damaging the channel
        # due to very high flow rates. former code: sum(ramping_list)/float(len(ramping_list))
        # problem: intermediate flow rates too high.
        self.ramping_time = channel.volume_tubing("inlet_1_1")/self.mean_flowrate * 3600
        p.logger_pump.debug("Mean flow rate: {}".format(self.mean_flowrate))
        p.logger_pump.debug("Total flow rate: {}".format(self.total_flowrate))
        p.logger_pump.info("Ramping time [s]: {}".format(round(self.ramping_time)))

    def ramping_calc(self):
        """This function calculates the flow rate and volume of each ramping step
        and stores them in a list"""
        for key in self.dict_rates_pumps.keys():
            if "LA120" in key:  # surrogate test: is pump LA120 being used?
                # Decides if ramping to the final flow rate (FR) is done from a higher or lower FR
                if self.dict_rates_pumps[key] > self.total_flowrate / sum(self.pump_configuration_n.values()):
                    self.rates_LA120.append(self.total_flowrate * 0.25)
                    while len(self.rates_LA120) < self.steps:
                        self.rates_LA120.append(round(self.rates_LA120[-1] + (self.dict_rates_pumps[key] -
                                                                              self.rates_LA120[0])/9, 3))
                else:
                    if self.dict_rates_pumps[key] <= self.total_flowrate / sum(self.pump_configuration_n.values()):
                        self.rates_LA120.append(self.mean_flowrate * 2 - self.dict_rates_pumps[key])
                        while len(self.rates_LA120) < self.steps:
                            self.rates_LA120.append(round(self.rates_LA120[-1] + (self.dict_rates_pumps[key] -
                                                                                  self.rates_LA120[0])/9, 3))
                p.logger_pump.debug("Ramping rates LA120: {}".format(", ".join(str(x) for x in self.rates_LA120)))

            elif "LA122" in key:  # surrogate test: is pump LA122 being used?
                if self.dict_rates_pumps[key] > self.total_flowrate / sum(self.pump_configuration_n.values()):
                    self.rates_LA122.append(self.total_flowrate * 0.25)
                    while len(self.rates_LA122) < self.steps:
                        self.rates_LA122.append(round(self.rates_LA122[-1] + (self.dict_rates_pumps[key] -
                                                                              self.rates_LA122[0])/9, 3))
                else:
                    if self.dict_rates_pumps[key] <= self.total_flowrate / sum(self.pump_configuration_n.values()):
                        self.rates_LA122.append(round(self.mean_flowrate * 2 - self.dict_rates_pumps[key], 3))
                        while len(self.rates_LA122) < self.steps:
                            self.rates_LA122.append(round(self.rates_LA122[-1] + (self.dict_rates_pumps[key] -
                                                                                  self.rates_LA122[0])/9, 3))
                p.logger_pump.debug("Ramping rates LA122: {}".format(", ".join(str(x) for x in self.rates_LA122)))

            elif "LA160" in key:  # surrogate test: is pump LA160 being used?
                if self.dict_rates_pumps[key] > self.total_flowrate / sum(self.pump_configuration_n.values()):
                    self.rates_LA160.append(self.total_flowrate * 0.25)
                    while len(self.rates_LA160) < self.steps:
                        self.rates_LA160.append(round(self.rates_LA160[-1] + (self.dict_rates_pumps[key] -
                                                                              self.rates_LA160[0])/9, 3))
                else:
                    if self.dict_rates_pumps[key] <= self.total_flowrate / sum(self.pump_configuration_n.values()):
                        self.rates_LA160.append(self.mean_flowrate * 2 - self.dict_rates_pumps[key])
                        while len(self.rates_LA160) < self.steps:
                            self.rates_LA160.append(round(self.rates_LA160[-1] + (self.dict_rates_pumps[key] -
                                                                                  self.rates_LA160[0])/9, 3))
                p.logger_pump.debug("Ramping rates LA160: {}".format(", ".join(str(x) for x in self.rates_LA160)))

        # calculate volume per step and write it into a list
        self.time_per_step = self.ramping_time / self.steps
        if len(self.rates_LA120) > 0:
            if "h" in self.dict_units_pumps["LA120"]:
                for rate in self.rates_LA120:
                    self.vol_LA120.append(round(rate * self.time_per_step / 3600, 3))
            elif "min" in self.dict_units_pumps["LA120"]:
                for rate in self.rates_LA120:
                    self.vol_LA120.append(round(rate * self.time_per_step / 60, 3))
            p.logger_pump.debug("Ramping volumes LA120: {}".format(", ".join(str(x) for x in self.vol_LA120)))

        if len(self.rates_LA122) > 0:
            if "h" in self.dict_units_pumps["LA122"]:
                for rate in self.rates_LA122:
                    self.vol_LA122.append(round(rate * self.time_per_step / 3600, 3))
            elif "min" in self.dict_units_pumps["LA122"]:
                for rate in self.rates_LA122:
                    self.vol_LA122.append(round(rate * self.time_per_step / 60, 3))
            p.logger_pump.debug("Ramping volumes LA122: {}".format(", ".join(str(x) for x in self.vol_LA122)))

        if len(self.rates_LA160) > 0:
            if "h" in self.dict_units_pumps["LA160"]:
                for rate in self.rates_LA160:
                    self.vol_LA160.append(round(rate * self.time_per_step / 3600, 3))
            elif "min" in self.dict_units_pumps["LA160"]:
                for rate in self.rates_LA160:
                    self.vol_LA160.append(round(rate * self.time_per_step / 60, 3))
            p.logger_pump.debug("Ramping volumes LA160: {}".format(", ".join(str(x) for x in self.vol_LA160)))

    # instantiate EmptyClass from the beginning of this module.
    empty_class = EmptyClass()  # I am sure this class is not necessary, but it works this way.

    def writing(self, global_phase_number, LA120 = empty_class, LA122=empty_class, LA160=empty_class):
        """Writes the rates and volumes to the pumps together with the global
        phase number"""
        for iterator in range(self.steps):
            phn = global_phase_number.next()  # returns the current phase number and adds 1
            if len(self.rates_LA120) > 0:
                LA120.phase_number(phn)
                LA120.rate(self.rates_LA120[phn - 1], self.dict_units_pumps["LA120"])
                LA120.volume(self.vol_LA120[phn - 1], self.dict_units_pumps["LA120"][:2])
            if len(self.rates_LA122) > 0:
                LA122.phase_number(phn)
                LA122.rate(self.rates_LA122[phn - 1], self.dict_units_pumps["LA122"])
                LA122.volume(self.vol_LA122[phn - 1], self.dict_units_pumps["LA122"][:2])
            if len(self.rates_LA160) > 0:
                LA160.phase_number(phn)
                LA160.rate(self.rates_LA160[phn - 1], self.dict_units_pumps["LA160"])
                LA160.volume(self.vol_LA160[phn - 1], self.dict_units_pumps["LA160"][:2])
        pump_rates_list = []
        for pump in self.pump_configuration_n.keys():
            string = str(self.dict_rates_pumps[pump]) + ' ' + self.dict_units_pumps[pump]
            pump_rates_list.append(string)
        p.logger_pump.info("Pumps {} ramp to {} in {} s ({} steps)".format(', '.join([k for k in
                                                                                      self.dict_rates_pumps.keys()]),
                                                                           ', '.join([i for i in pump_rates_list]),
                                                                           round(self.ramping_time, 1),
                                                                           self.steps))
