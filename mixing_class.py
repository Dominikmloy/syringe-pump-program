import ramping_class as ramp
import Module_pumps as p
import channels as c


class Mixing(object):
    """ This class asks the user rate and volume of each mixing step for each pump.
    These inputs are written to the respective pumps with their respective
    phase number and an overlap is inserted between each mixing process.
    """
    def __init__(self, ramping_instance=0, channel=0, setup_instance=0):
        """ Holds all the necessary attributes and functions."""
        self.ramping = ramping_instance  # passes the information of the ramping instance to this class.
        self.setup = setup_instance  # passes the information of the setup instance to this class.
        self.overlap = 8  # overlap to be inserted between runs. Defaults to 8 ul.
        self.runs = 1  # number of mixing runs with defined rates and volumes. Defaults to 1.
        self.diameter_LA120 = 0  # diameter of the syringe(s) equipped to pump LA120
        self.diameter_LA122 = 0  # diameter of the syringe(s) equipped to pump LA122
        self.diameter_LA160 = 0  # diameter of the syringe(s) equipped to pump LA160
        self.rates_LA120 = []  # list of flow rates (mixing operation and overlap) written to pump LA120
        self.rates_LA122 = []  # list of flow rates (mixing operation and overlap) written to pump LA122
        self.rates_LA160 = []  # list of flow rates (mixing operation and overlap) written to pump LA160
        self.volumes_LA120 = []  # list of volumes (mixing operation and overlap) written to pump LA120
        self.volumes_LA122 = []  # list of volumes (mixing operation and overlap) written to pump LA122
        self.volumes_LA160 = []  # list of volumes (mixing operation and overlap) written to pump LA160
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
        # define the two groups that should not be used together for purging
        self.inlet_group_1 = ["inlet_1_1", "inlet_1_2", "inlet_1_3"]
        self.inlet_group_2 = ["inlet_2_1", "inlet_2_2"]
        self.dict_rates_pumps = {}  # holds the flow rates of the first run
        self.units_dict = {"\u03BCl/min": "um", "\u03BCl/m": "um", "\u03BC/min": "um",
                           "ml/min": "mm", "ml/m": "mm", "m/min": "mm",
                           "\u03BCl/h": "uh", "\u03BC/h": "uh",
                           "ul/h": "uh", "u/h": "uh",
                           "ml/h": "mh", "m/h": "mh"}
        self.time_list = []  # stores the duration [s] of the discharge of each fraction at the outlet

        def _standalone():
            """ This function is called on initialisation of the class and
            checks for the presence of certain objects (specific:
            pump_configuration_n) to decide if syringe number & type and pump
            connections need to be asked from the user.
            """
            if ramping_instance == 0:
                self.ramping = ramp.Ramping(channel)
                self.ramping.syringes_number(self.setup.pumps_active)
                self.ramping.syringes_type(self.setup.dict_pump_instances, self.setup.pumps_active)
                self.ramping.tubing_connections()
            self.pump_configuration_n = self.ramping.pump_configuration_n
            self.pump_configuration_syr = self.ramping.pump_configuration_syr
            self.dict_inlets_pumps = self.ramping.dict_inlets_pumps

        _standalone()

    @staticmethod
    def print_dict_keys(dictionary):
        """ this function returns a string of all dictionary keys separated by commas."""
        key_list = []
        for key in dictionary:
            key_list.append(key)
        key_string = ", ".join(key_list)
        return key_string

    @staticmethod
    def dict_to_string(dictionary):
        """
        This function takes any dictionary as argument and returns
        a string containing all key:value pairs separated by a comma.
        :param dictionary:
        :return: string in the format: key1: value1, key2: value2:, ...
        """
        dict_list = []
        for key, value in dictionary.items():
            dict_list.append(str(key) + ": " + str(value))
        dict_string = ", ".join(dict_list)
        return dict_string

    @staticmethod
    def unit_conversion(unit_dict):
        """
        This function takes a dictionary with names mapped to rate units (e.g., "LA120": "ml/h")
        and returns a dictionary with the key from 'unit_dict' and the
        conversion factor to change to ul/h.
        """
        transformation_dict = {}
        for key in unit_dict:
            if "\u03BCl/h" in unit_dict[key]:
                transformation_dict[key] = 1
            elif "\u03BCl/min" in unit_dict[key]:
                transformation_dict[key] = 60
            elif "ml/h" in unit_dict[key]:
                transformation_dict[key] = 1000
            elif "ml/min" in unit_dict[key]:
                transformation_dict[key] = 60000
            else:
                print("error in static: ", key, unit_dict[key])
        return transformation_dict

    def number_of_runs(self, runs=None):
        """ This function establishes the number of runs to be executed and
        stores them in a variable. Default is 1. If number of runs > 1,
        self.overlap() should be called to allow for customization of overlap volume.
        Alternatively, the number of runs can be passed to the function vie the
        **kwargs argument. Example: runs = 5.
        """
        def error_message(error_number, additional_info):
            """ nested function that defines the error message to be given when the
            kwargs are wrong. Additional information about the error can be given
            vie the second argument"""
            print("Error number: {}".format(error_number),
                  "\nError in keyword arguments provided.",
                  "\nProvided {}.".format(runs),
                  "\nExpected: number of runs.",
                  "\nFor example: runs = 3.",
                  "\nAdditional info: ", additional_info,
                  "\nProgram aborted.")
            p.logger_pump.debug("""Error message {}: Function 'number_of_runs()' 
                                aborted due to errors in the kwargs: {}.""".format(error_number, runs)
                                )
            raise SystemExit("Program aborted.")

        if runs:
            try:
                self.runs = int(runs)
            except ValueError:
                error_message(1, "argument is not a number (int)")
        else:
            print("How many runs do you want to make?")
            runs = input("> ")
            try:
                self.runs = int(runs)
                p.logger_pump.info("Number of runs: {}".format(self.runs))
            except ValueError:
                print("Please choose a number (type: integer).")
                return self.number_of_runs()

    def rate(self, pumps_active, **kwargs):
        """ This function asks the user to provide rates for each run. The rates' unit is selected once for
        all subsequent runs on this pump.
        Alternatively, the rates and the respective unit can be passed directly to the function
        via the kwargs. The names of the arguments should be <name_of_pump>_rate for rates and
        <name_of_pump>_unit for units. Rates must be stored in a list. All active pumps must be used.
        Example: LA120_rates = [120,140,160], LA160_rates = [1200, 1400, 1600],
        LA120_unit = 'ul/h', LA160_unit = 'ul/h'.
        """
        def error_message(error_number, additional_info):
            """ nested function that defines the error message to be given when the
            kwargs are wrong. Additional information about the error can be given
            vie the second argument"""
            print("Error number: {}".format(error_number),
                  "\nError in keyword arguments provided.",
                  "\nProvided {}.".format(kwargs),
                  "\nExpected: name of all(!) active pumps: {}.".format(self.print_dict_keys(sorted(
                      pumps_active.keys()))),
                  "\n'_rate' or '_unit' must be appended to the pumps name"
                  "\n+ the respective list of rates or their unit.",
                  "\nFor example: LA120_rate = [120, 160, 180}.",
                  "\nAdditional info: ", additional_info,
                  "\nProgram aborted.")
            p.logger_pump.debug("""Error message {}: Function 'rate()' aborted 
                                due to errors in the kwargs: {}.\n {}""".format(error_number, kwargs, additional_info)
                                )
            raise SystemExit("Program aborted.")

        def check_max_flow_rate(question):
            # check if max flow rate is exceeded and ask, if the program
            # should be continued nevertheless or if it should be restarted.
            for i in range(self.runs):
                flow_rate = 0
                if len(self.rates_LA120) > 0:
                    flow_rate += self.rates_LA120[i] * self.pump_configuration_n["LA120"]
                if len(self.rates_LA122) > 0:
                    flow_rate += self.rates_LA122[i] * self.pump_configuration_n["LA122"]
                if len(self.rates_LA160) > 0:
                    flow_rate += self.rates_LA160[i] * self.pump_configuration_n["LA160"]
                p.logger_pump.debug("Total flow rate of run {}: {}".format(i + 1, flow_rate))

                if flow_rate > self.setup.max_flowrate:
                    p.logger_pump.warning("WARNING! TOTAL FLOW RATE EXCEEDS MAXIMUM FLOW RATE! ({})".format(
                                            self.setup.max_flowrate)
                                          )
                    print("Do you want to {}?".format(question))
                    answer = input("> ")
                    positive_answers = ["y", "j", "yes", "ja"]
                    if answer.lower() in positive_answers:
                        return True
                    else:
                        return False
            print("-" * 40)
            p.logger_pump.debug("Flow rate units: {}".format(self.dict_units_pumps))

        if kwargs:
            # check if all active pumps are used.
            list_active_pumps = [k for k, v in pumps_active.items() if v == True]
            for key in list_active_pumps:
                counter = ",".join(kwargs.keys()).count(key)  # counts the occurrences of the pump name
                if counter == 2:  # test if all active pumps are used in this function.
                    pass
                else:
                    error_message(1, "All active pumps must be used.")
            # check if a list of rates is given and check if all rates are numbers (floats.
            for key in kwargs:
                if 'rate' in key:
                    # check if the list of rates for each pump has a sufficient number of values.
                    if len(kwargs[key]) == self.runs:
                        pass
                    else:
                        error_message(2,
                                      "number of rates ({}) does not match number of runs ({}).".format(
                                          len(kwargs[key]),
                                          self.runs))
                    # check if the list contains only numbers
                    for rates in kwargs[key]:
                        try:
                            if "LA120" in key:
                                self.rates_LA120.append(float(rates))
                            elif "LA122" in key:
                                self.rates_LA122.append(float(rates))
                            elif "LA160" in key:
                                self.rates_LA160.append(float(rates))
                        except ValueError:
                            error_message(3, "Flow rate must be a number (int or float).")

                # check if the unit has the right format.
                elif 'unit' in key:
                    if kwargs[key] in self.units_dict:
                        self.dict_units_pumps[key[:5]] = kwargs[key]
                    else:
                        error_message(4, "The unit {} has the wrong format.".format(kwargs[key]))
                else:
                    error_message(5, "kwargs must be 'LA120_rate' or 'LA120_unit'")
            # make sure that the max. flow rate is not exceeded.
            check = check_max_flow_rate("abort the program")
            if check:
                p.logger_pump.debug("Program aborted.")
                raise SystemExit("Program aborted.")
            else:
                p.logger_pump.debug("Program continuing")

        # manual input of variables during program execution
        else:
            for i in range(self.runs):
                # rate and unit for the first pump is queried.
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

                    # in the first iteration the user is asked to select the rates' unit for all runs on this pump.
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

                # rate and unit for the second pump is queried.
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

                    # in the first iteration the user is asked to select the rates' unit for all runs on this pump.
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
                # rate and unit for the third pump is queried.
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

                    # in the first iteration the user is asked to select the rates' unit for all runs on this pump.
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

            # make sure that the max. flow rate is not exceeded.
            check = check_max_flow_rate("restart the rate selection process")
            if check:
                p.logger_pump.debug("Rate selection process restarted.")
                self.rate(pumps_active)
            else:
                p.logger_pump.debug("Program continuing.")
        # append the run's name to self.name for the countdown function to use.
        for i in range(self.runs):
            self.name.append("run {}".format(i + 1))

    def volume(self, pumps_active, **kwargs):
        """ This function asks the user volumes for each run and pump and appends it to respective list
        (self.volume_LAXXX).
        Alternatively, the volumes can be passed directly to the function via the kwargs.
        The names of the arguments should be <name_of_pump> = <list of volumes>.
        Volumes must be stored in a list. All active pumps must be used.
        Example: LA120 = [20, 40, 60]. The volumes' units are the same as chosen in the rate() function.
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
                  "\n+ the respective list of rates.",
                  "\nFor example: LA120 = [20, 40, 60}.",
                  "\nAdditional info: ", additional_info,
                  "\nProgram aborted.")
            p.logger_pump.debug("""Error message {}: Function 'volume()' aborted 
                                due to errors in the kwargs: {}.\n{}""".format(error_number,
                                                                               kwargs,
                                                                               additional_info)
                                )
            raise SystemExit("Program aborted.")

        if kwargs:
            # check if all active pumps are used.
            list_active_pumps = [k for k, v in pumps_active.items() if v == True]
            if sorted(kwargs.keys()) == sorted(
                    list_active_pumps):  # test if all active pumps are used in this function.
                pass
            else:
                error_message(1, "All active pumps must be used.")
            # check if a list of rates is given and check if all rates are numbers (floats.
            for key in kwargs:
                # check if the list of rates for each pump has a sufficient number of values.
                if len(kwargs[key]) == self.runs:
                    pass
                else:
                    error_message(2,
                                  "Number of volumes ({}) does not match number of runs ({}).".format(len(kwargs[key]),
                                                                                                      self.runs))
                # check if the list contains only numbers
                for volumes in kwargs[key]:
                    try:
                        if "LA120" in key:
                            self.volumes_LA120.append(float(volumes))
                        elif "LA122" in key:
                            self.volumes_LA122.append(float(volumes))
                        elif "LA160" in key:
                            self.volumes_LA160.append(float(volumes))
                    except ValueError:
                        error_message(3, "Volume must be a number (int or float).")

        else:
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

                if pumps_active[sorted(pumps_active)[1]]:  # LA122
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

    def overlap_calc(self, overlap=None):
        """ This function asks for the overlap between runs and stores them
        in a variable (self.overlap). A sensible value is 8 \u03BCl. Afterwards, it adds volumes
        and rates in between runs in self.rates_LAxxx und self.vol_LAxxx.
        Alternatively, the overlap volume can be passed to the function via the kwargs.
        The name of the argument must be 'overlap'. For example: overlap = 8
        """
        def error_message(error_number, additional_info):
            """ nested function that defines the error message to be given when the
            kwargs are wrong. Additional information about the error can be given
            vie the second argument"""
            print("Error number: {}".format(error_number),
                  "\nError in keyword arguments provided.",
                  "\nProvided {}.".format(overlap),
                  "\nExpected: the volume of the overlap between runs.",
                  "\nFor example: overlap = 12.",
                  "\nAdditional info: ", additional_info,
                  "\nProgram aborted.")
            p.logger_pump.debug("""Error message {}: Function 'overlap_calc()' aborted 
                                due to errors in the kwargs: {}.\n{}""".format(error_number,
                                                                               overlap,
                                                                               additional_info)
                                )
            raise SystemExit("Program aborted.")

        if overlap:
            try:
                self.overlap = int(overlap)
            except ValueError:
                error_message(1, "argument is not a number (int)")
        else:
            print("How much overlap [\u03BCl] do you want to have between runs?")
            overlap = input("> ")
            try:
                self.overlap = float(overlap)
                p.logger_pump.info("Overlap: {}".format(self.overlap))
            except ValueError:
                error_message(1, "Flow rate must be a number (int or float).")

            # calculate relative overlap for each pump
        def _relative_overlap_calc(rates_list):
            """
            This function takes the list of the rates from one pump as parameter and calculates the relative
            overlap volume for each pump.
            """
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
                    self.overlap_LA120.append(round(self.rates_LA120[j]/flowrate *
                                              self.overlap, 3))
                if self.rates_LA122:
                    self.overlap_LA122.append(round(self.rates_LA122[j]/flowrate *
                                              self.overlap, 3))
                if self.rates_LA160:
                    self.overlap_LA160.append(round(self.rates_LA160[j]/flowrate *
                                              self.overlap, 3))
        # checks, if self.rates_LA120 exists, calculates the necessary overlaps and inserts them into the
        # pump volume's list. Additionally, the name of the overlap is inserted into the variable self.name which
        # is used to inform the user with the countdown function.
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

    def end_process(self, channels_instance, pumps_active, purging_pumps=None):
        """ This functions asks if the channel shall be purged after the last run, and if yes,
        which pumps (one ore more are possible) should be used to transport the product of the
        final mixing step to the outlet.
        Alternatively, the pumps purging the channel can be passed to the function via the kwargs.
        The name of the keyword must be 'purging_pumps', and the argument must be a
        list of the target pumps. For example: purging_pumps = ['LA120', 'LA160']
        Attention: Only pumps serving the mixing zone one OR mixing zone two (in case of the double
        meander channel) can be chosen. If the pumps serving mixing zone two are chosen, the channel
        is only purged from the second mixing zone.
        """

        def error_message(error_number, additional_info):
            """ nested function that defines the error message to be given when the
            kwargs are wrong. Additional information about the error can be given
            vie the second argument"""
            print("Error number: {}".format(error_number),
                  "\nError in keyword arguments provided.",
                  "\nProvided {}.".format(purging_pumps),
                  "\nExpected: a list of the pumps supposed to purge the channel.",
                  "\nFor example: purging_pumps = ['LA120', 'LA160'] ",
                  "\nAdditional info: ", additional_info,
                  "\nProgram aborted.")
            p.logger_pump.debug("""Error message {}: Function 'purging_pumps()' aborted
                                due to errors in the kwargs: {}.\n{}""".format(error_number,
                                                                               purging_pumps,
                                                                               additional_info)
                                )
            raise SystemExit("Program aborted.")

        pumps_end_process = []
        if purging_pumps:
            # check if the chosen pump is active
            list_active_pumps = [k for k, v in pumps_active.items() if v == True]
            for item in purging_pumps:
                if item in list_active_pumps:
                    pass
                else:
                    error_message(1, "chosen pump is not active or does not exist: {}".format(item))
            pumps_end_process = purging_pumps

        else:
            print("Do you want to pump the product of the final mixing run into the collector?")
            answer = input("> ")
            if "n" in answer.lower():
                p.logger_pump.info("Channel is not purged after the last run")

            if "y" in answer.lower():
                print("""Which pump(s) will pump the product of the final mixing
                run (that means: purge the channel)?
                Choose one or more numbers:""")
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
                    print("Please choose a number (1, 2, and / or 3).")
                    return self.end_process(channels_instance, pumps_active)
                p.logger_pump.info("""The following pumps will pump the
                                   final product: {}""".format(", ".join(pumps_end_process)))
        if pumps_end_process:
            # calculate relative flow rates and add them to
            # dict_last_flowrate and dict_last_volume.
            self.name.append("purging")
            last_flowrate = []
            transformation_dict = self.unit_conversion(self.dict_units_pumps)
            # transform dictionaries into strings for better logging
            trans_string = self.dict_to_string(transformation_dict)
            units_string = self.dict_to_string(self.dict_units_pumps)
            p.logger_pump.debug("transformation dict: {}, {}".format(units_string, trans_string))

            # make a list of the inlets connected to the pumps that will purge the channel.
            pumps_inlets = []
            for pump in pumps_end_process:
                for inlet in self.dict_inlets_pumps.keys():
                    if pump == self.dict_inlets_pumps[inlet]:
                        pumps_inlets.append(inlet)
            # check if pumps for purging are from one group only
            if any(i in self.inlet_group_1 for i in pumps_inlets) and any(i in self.inlet_group_2 for i in pumps_inlets):
                text = "Either the pumps serving the first or the pumps " + \
                       "serving the second mixing zone can be used for purging."
                if purging_pumps:
                    error_message(2, text)
                else:
                    print(text, "\nPlease repeat the selection process.")
                    return self.end_process(channels_instance, pumps_active)

            def get_total_last_flowrate(inlet):
                """ Function to avoid copying code. The function returns the last flow rate in ul/s
                of the pump that is connected to the inlet specified as function argument. """
                if self.dict_inlets_pumps[inlet] == "LA120":
                    return self.rates_LA120[-1] * transformation_dict["LA120"]
                elif self.dict_inlets_pumps[inlet] == "LA122":
                    return self.rates_LA122[-1] * transformation_dict["LA122"]
                elif self.dict_inlets_pumps[inlet] == "LA160":
                    return self.rates_LA160[-1] * transformation_dict["LA160"]

            # self.inlet_group_1: Inlets that serve the first mixing zone -> will purge the complete channel
            if all(i in self.inlet_group_1 for i in pumps_inlets):
                # volume to be purged from the channels.
                # e.g., single meander channel
                volume = round(channels_instance.channel_volume
                               - channels_instance.volume_to_mixing_1()
                               + channels_instance.volume_tubing("outlet"), 2)
                for inlet in self.dict_inlets_pumps:
                    if inlet in self.inlet_group_1:
                        last_flowrate.append(get_total_last_flowrate(inlet))

            # self.inlet_group_2: Inlets that serve the 2nd mixing zone
            # -> will purge the channel only from the second mixing zone.
            if all(i in self.inlet_group_2 for i in pumps_inlets):
                # volume to be purged from the channels.
                # eg., double meander channel: only the volume after the second mixing zone is purged.
                volume = round(channels_instance.channel_volume
                               - channels_instance.volume_to_mixing_2()
                               + channels_instance.volume_tubing("outlet"), 2)

                # the additional volume the pumps connected to the self.inlet_group_1 need to pump in order to
                # send the last run's complete product to mixing zone 2.
                volume_to_mixing_2 = round(channels_instance.volume_to_mixing_2()
                                           - channels_instance.volume_to_mixing_1())
                pumps_pumping_mixing_2 = {}
                pumps_pumping_mixing_2_flow_rate = 0

                for inlet in self.inlet_group_1:
                    if inlet in self.dict_inlets_pumps.keys():
                        pumps_pumping_mixing_2_flow_rate += get_total_last_flowrate(inlet)
                        if self.dict_inlets_pumps[inlet] not in pumps_pumping_mixing_2.keys():
                            pumps_pumping_mixing_2[self.dict_inlets_pumps[inlet]] = get_total_last_flowrate(inlet)

                # add pumps serving inlet group 1 to the last flow rate dict.
                if "LA120" in pumps_pumping_mixing_2.keys():
                    self.dict_last_flowrate["LA120"] = round(pumps_pumping_mixing_2["LA120"]
                                                             / transformation_dict["LA120"]
                                                             / self.pump_configuration_n["LA120"],
                                                             3)
                    self.dict_last_volume["LA120"] = round(volume_to_mixing_2
                                                           * pumps_pumping_mixing_2["LA120"]
                                                           / pumps_pumping_mixing_2_flow_rate
                                                           / self.pump_configuration_n["LA120"],
                                                           3)
                if "LA122" in pumps_pumping_mixing_2.keys():
                    self.dict_last_flowrate["LA122"] = round(pumps_pumping_mixing_2["LA122"]
                                                             / transformation_dict["LA122"]
                                                             / self.pump_configuration_n["LA122"],
                                                             3)
                    self.dict_last_volume["LA122"] = round(volume_to_mixing_2
                                                           * pumps_pumping_mixing_2["LA122"]
                                                           / pumps_pumping_mixing_2_flow_rate
                                                           / self.pump_configuration_n["LA122"],
                                                           3)
                if "LA160" in pumps_pumping_mixing_2.keys():
                    self.dict_last_flowrate["LA160"] = round(pumps_pumping_mixing_2["LA160"]
                                                             / transformation_dict["LA160"]
                                                             / self.pump_configuration_n["LA160"],
                                                             3)
                    self.dict_last_volume["LA160"] = round(volume_to_mixing_2
                                                           * pumps_pumping_mixing_2["LA160"]
                                                           / pumps_pumping_mixing_2_flow_rate
                                                           / self.pump_configuration_n["LA160"],
                                                           3)

                # I want the pump in group 2 to pump with the total flow rate of the last run
                for inlet in self.dict_inlets_pumps.keys():
                    last_flowrate.append(get_total_last_flowrate(inlet))

            last_flowrate_sum = sum(last_flowrate)
            rate_per_pump = last_flowrate_sum / len(pumps_end_process)
            # write the time for flushing the final product from the channel
            # to self.end_time.
            time_sec = round(volume / last_flowrate_sum * 3600, 0)
            self.end_time = time_sec
            # calculate relative flow rates and volumes and store them
            # in the respective dicts
            if "LA120" in pumps_end_process:
                self.dict_last_flowrate["LA120"] = round(rate_per_pump
                                                         / transformation_dict["LA120"]
                                                         / self.pump_configuration_n["LA120"],
                                                         3)
                self.dict_last_volume["LA120"] = round(volume
                                                       / len(pumps_end_process)
                                                       / self.pump_configuration_n["LA120"],
                                                       3)
            if "LA122" in pumps_end_process:
                self.dict_last_flowrate["LA122"] = round(rate_per_pump
                                                         / transformation_dict["LA122"]
                                                         / self.pump_configuration_n["LA122"],
                                                         3)
                self.dict_last_volume["LA122"] = round(volume
                                                       / len(pumps_end_process)
                                                       / self.pump_configuration_n["LA122"],
                                                       3)
            if "LA160" in pumps_end_process:
                self.dict_last_flowrate["LA160"] = round(rate_per_pump
                                                         / transformation_dict["LA160"]
                                                         / self.pump_configuration_n["LA160"],
                                                         3)
                self.dict_last_volume["LA160"] = round(volume
                                                       / len(pumps_end_process)
                                                       / self.pump_configuration_n["LA160"],
                                                       3)
        else:
            p.logger_pump.debug("Channel is not purged after the last run")

    def writing(self, pumps_instances_dict, pumps_active, global_phase_number):
        """ Writes the rates and volumes to the pumps
        together with the global phase number
        """

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
            print("-" * 40)
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
            print_list = [self.name[i], pump1, pump2, pump3]
            for item in print_list:
                if item:
                    p.logger_pump.info(item)
            print("-" * 40)

        # insert end volume and rate into the pumping program
        if self.dict_last_flowrate:
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
            print("-" * 40)
            print_list = [self.name[-1], pump1_end, pump2_end, pump3_end]
            for item in print_list:
                if item:
                    p.logger_pump.info(item)
            print("-" * 40)

    def mixing(self, channel_used, countdown, dict_pump_instances, channel_instance,
               pumps_active, pumps_adr, ramping_time=0, dict_rate_pumps={}):
        """ This function checks which channel is used and starts the pumps.
        If the double meander channel is used, it asks if the user if he/she
        wants to pump the educts at the different inlets
        at different times. Then it calculates the time difference
        and starts the pumps.
        If an unknown channel is chosen, it asks the user if one of
        the known channels should be used.
        """
        # assign the pump instances to their respective variables
        if pumps_active["LA120"]:
            pump_instance = dict_pump_instances["LA120"]
        elif pumps_active["LA122"]:
            pump_instance = dict_pump_instances["LA122"]
        elif pumps_active["LA160"]:
            pump_instance = dict_pump_instances["LA160"]

        def total_V_FR_calculation(inlet_group):
            """
            This function calculates the total flow rate and total volume associated with
            each event from self.name.
            """
            # get the conversion factors for the various pumps
            total_V = []
            total_FR = []
            conversion_rate = self.unit_conversion(self.dict_units_pumps)
            conversion_volume = {}
            for key in conversion_rate.keys():
                if conversion_rate[key] == 60 or conversion_rate[key] == 1:
                    conversion_volume[key] = 1
                elif conversion_rate[key] == 60000 or conversion_rate[key] == 1000:
                    conversion_volume[key] = 1000
            # transform the following dictionaries to strings for the logging function
            conversion_rate_str = self.dict_to_string(conversion_rate)
            conversion_volume_str = self.dict_to_string(conversion_volume)
            p.logger_pump.debug("conversions: {}, {}".format(conversion_rate_str, conversion_volume_str))
            pumps_in_inlet_group = []
            for inlet in inlet_group:
                if inlet in self.dict_inlets_pumps.keys():
                    pumps_in_inlet_group.append(self.dict_inlets_pumps[inlet])
            if "LA120" in pumps_in_inlet_group:
                for i in range(len(self.volumes_LA120)):
                    vol = (self.volumes_LA120[i]
                           * self.pump_configuration_n["LA120"]
                           * conversion_volume["LA120"])
                    rat = (self.rates_LA120[i]
                           * self.pump_configuration_n["LA120"]
                           * conversion_rate["LA120"])
                    if "LA122" in pumps_in_inlet_group:
                        vol += (self.volumes_LA122[i]
                                * self.pump_configuration_n["LA122"]
                                * conversion_volume["LA122"])
                        rat += (self.rates_LA122[i]
                                * self.pump_configuration_n["LA122"]
                                * conversion_rate["LA122"])
                    if "LA160" in pumps_in_inlet_group:
                        vol += (self.volumes_LA160[i]
                                * self.pump_configuration_n["LA160"]
                                * conversion_volume["LA160"])
                        rat += (self.rates_LA160[i]
                                * self.pump_configuration_n["LA160"]
                                * conversion_rate["LA160"])
                    total_V.append(vol)
                    total_FR.append(rat)

            elif "LA122" in pumps_in_inlet_group:
                for i in range(len(self.volumes_LA122)):
                    vol = (self.volumes_LA122[i]
                           * self.pump_configuration_n["LA122"]
                           * conversion_volume["LA122"])
                    rat = (self.rates_LA122[i]
                           * self.pump_configuration_n["LA122"]
                           * conversion_rate["LA122"])
                    if "LA160" in pumps_in_inlet_group:
                        vol += (self.volumes_LA160[i]
                                * self.pump_configuration_n["LA160"]
                                * conversion_volume["LA160"])
                        rat += (self.rates_LA160[i]
                                * self.pump_configuration_n["LA160"]
                                * conversion_rate["LA160"])
                    total_V.append(vol)
                    total_FR.append(rat)

            elif "LA160" in pumps_in_inlet_group:
                for i in range(len(self.volumes_LA160)):
                    total_V.append(self.volumes_LA160[i]
                                   * self.pump_configuration_n["LA160"]
                                   * conversion_volume["LA160"]
                                   )
                    total_FR.append(self.rates_LA160[i]
                                    * self.pump_configuration_n["LA160"]
                                    * conversion_rate["LA160"])

            # append purging
            if self.dict_last_flowrate:
                last_volume = 0
                last_rate = 0
                for key in self.dict_last_volume.keys():
                    if key in pumps_in_inlet_group:
                        last_volume += self.dict_last_volume[key] * self.pump_configuration_n[key]
                for key in self.dict_last_flowrate.keys():
                    if key in pumps_in_inlet_group:
                        last_rate += self.dict_last_flowrate[key] * self.pump_configuration_n[key]
                p.logger_pump.debug("last rate: {}, volume: {}".format(str(last_rate), str(last_volume)))
                total_V.append(last_volume)
                total_FR.append(last_rate)

            else:
                # 0 is appended in order to avoid a out of range error
                # when lists are passed to the countdown function.
                total_V.append(0)
                total_FR.append(0)
            return total_V, total_FR

        def collecting_calculation():
            """
            This function calculates the discharge's duration of each product fraction
            from the outlet. Since the product needs some time to reach the outlet,
            the total flow rate might change during the discharge process, changing the
            time that is needed for discharging the complete product fraction.
            """
            i = 0
            transfer = 0
            while i < len(total_V) - 1:  # if dead volume < run 1
                if total_v_outlet[0] <= total_V[0]:
                    if i == 0:
                        self.time_list.append(round(total_v_outlet[0] / total_FR[i] * 3600, 2))
                    vol_1 = total_V[i] - total_v_outlet[0]
                    vol_2 = total_V[i] - vol_1
                    self.time_list.append(round((vol_1 / total_FR[i] + vol_2 / total_FR[i + 1]) * 3600, 2))
                    # print("vol_1: {}\nvol_2: {}\ntime list: {}".format(vol_1, vol_2, self.time_list))
                    i += 1
                else:  # if total_V[0] > total_V_outlet[0]
                    j = len(self.time_list)
                    if j == 0:
                        rest = total_v_outlet[j] - total_V[j]
                        self.time_list.append(round(total_V[j] / total_FR[j] * 3600, 2))
                        # print("48: ", i, j, self.time_list)

                    else:
                        if transfer < total_v_outlet[j]:
                            self.time_list.append(round(transfer / total_FR[i] * 3600, 2))
                            # print("52: ", i, j, self.time_list)
                            rest = total_v_outlet[j] - transfer  # belongs to self.time_list [-1]
                        else:  # transfer > total_v_outlet
                            self.time_list.append(round(total_v_outlet[j] / total_FR[i] * 3600, 2))
                            # print("56: ", i, j, self.time_list)
                            rest = transfer - total_v_outlet[j]  # belongs to self.time_list [-1]

                    while rest != 0:
                        i += 1
                        if rest >= total_V[i]:
                            self.time_list[j] = self.time_list[j] + round(total_V[i] / total_FR[i] * 3600, 2)
                            # print("62: ", i, j, self.time_list)
                            rest -= total_V[i]
                        else:
                            self.time_list[j] = self.time_list[j] + round(rest / total_FR[i] * 3600, 2)
                            # print("66: ", i, j, self.time_list)
                            transfer = total_V[i] - rest  # the rest of the volume when the waste collection is over
                            rest = 0

                    # if j > 0:
                    if i == len(total_V) - 1:
                        while j < i:
                            j += 1
                            self.time_list.append(round(total_v_outlet[j] / total_FR[i] * 3600, 2))
                            # print("84: ", i, j, self.time_list)

        def collecting_calculation_2():
            i = 0
            for volume in total_v_outlet:
                duration = 0
                rest = volume  # wie gehe ich mit dem overlap um?
                # print("105: ", rest)
                while rest > 0:
                    if rest >= total_V[i]:
                        duration += total_V[i] / total_FR[i] * 3600
                        rest -= total_V[i]
                        # print(
                        #   "109: {}\nV: {}, FR: {}\nrest: {}, duration: {}, ".format(i, total_V[i], total_FR[i], rest,
                        #                                                            duration))
                        i += 1
                    elif rest < total_V[i]:
                        duration += rest / total_FR[i] * 3600
                        total_V[i] = total_V[i] - rest
                        rest = 0
                        # print("115: {}\nV: {}, FR: {}, duration: {}, ".format(i, total_V[i], total_FR[i], duration))
                self.time_list.append(duration)

        # Depending on the channel used, different parts of the code need to be executed.
        if channel_used == "Single meander channel":  # from main.py select_channel()
            pump_instance.start_all(pumps_active, pumps_adr)
            if ramping_time > 0:  # surrogate test if the ramping class was instantiated before.
                print(ramping_time, "ramping:")  # countdown
            # calculate the dead volume of the channel: volume of the complete channel +
            # volume of the outlet - volume of the channels leading to the mixing zone.
            dead_volume = (channel_instance.channel_volume
                           + channel_instance.volume_tubing("outlet")
                           - channel_instance.volume_channel_section("inlet_1_1-mixing_1")
                           - channel_instance.volume_channel_section("inlet_1_2-mixing_1")
                           - channel_instance.volume_channel_section("inlet_1_3-mixing_1")
                           )
            self.name.insert(0, "waste")
            print("dead volume: ", dead_volume)

            total_V = total_V_FR_calculation(self.inlet_group_1)[0]
            total_FR = total_V_FR_calculation(self.inlet_group_1)[1]
            total_v_outlet = total_V[:-1]
            total_v_outlet.insert(0, dead_volume)

            p.logger_pump.debug("total_V: {}".format(total_V))
            p.logger_pump.debug("total_FR: {}".format(total_FR))

            p.logger_pump.debug("total_v_outlet: ".format(total_v_outlet))
            collecting_calculation()

            for i in range(len(self.name[:-1])):
                countdown(self.name[i], self.time_list[i])

        elif channel_used == "Double meander channel":

            def error_message(error_number, additional_info):
                """ nested function that defines the error message to be given when the
                kwargs are wrong. Additional information about the error can be given
                vie the second argument"""
                print("Error number: {}".format(error_number),
                      "\nAn error has occurred in the 'mixing()' function.",
                      "\nAdditional info:", additional_info,
                      "\nProgram aborted.")
                p.logger_pump.debug("""Error message {}: Function 'mixing()' aborted.
                                    Additional info: {}.""".format(error_number,
                                                                   additional_info)
                                    )

                raise SystemExit("Program aborted.")

            # assign pump instances to inlets to enable the starting of the pumps at different time points.
            pump_inlet_1_2 = None
            pump_inlet_2_2 = None
            pump_inlet_1_1 = dict_pump_instances[self.dict_inlets_pumps["inlet_1_1"]]
            if self.dict_inlets_pumps["inlet_1_1"] != self.dict_inlets_pumps["inlet_1_2"]:
                pump_inlet_1_2 = dict_pump_instances[self.dict_inlets_pumps["inlet_1_2"]]

            # one pump is not supposed to serve both inlets leading to separate mixing zones at the same time.
            # therefore, pump_inlet_2 cannot be the same as pump_inlet_1.
            pump_inlet_2_1 = dict_pump_instances[self.dict_inlets_pumps["inlet_2_1"]]
            if self.dict_inlets_pumps["inlet_2_1"] != self.dict_inlets_pumps["inlet_2_2"]:
                pump_inlet_2_2 = dict_pump_instances[self.dict_inlets_pumps["inlet_2_2"]]

            # check, if pumps are wired correctly.
            if pump_inlet_1_1 == pump_inlet_2_1 or pump_inlet_1_1 == pump_inlet_2_2:
                add_info = "\nOne pump cannot be connected to inlet_1_1 and inlet_2_1 or inlet_2_2 at the same time"
                error_message(1, add_info)
            if pump_inlet_1_2 == pump_inlet_2_1 or pump_inlet_1_2 == pump_inlet_2_2:
                add_info = "\nOne pump cannot be connected to inlet_1_2 and inlet_2_1 or inlet_2_2 at the same time"
                error_message(2, add_info)

            # calculate the dead volume
            ramping_volume = round(channel_instance.volume_tubing("inlet_1_1"), 2)
            volume_to_mixing_2 = round(channel_instance.volume_to_mixing_2(), 2)
            volume_mixing_2_to_outlet = round((channel_instance.volume_channel_section("mixing_2-meander_2")
                                               + channel_instance.volume_channel_section("meander_2-meander_2")
                                               + channel_instance.volume_channel_section("meander_2-outlet")
                                               + channel_instance.volume_tubing("outlet")
                                               ), 2)
            dead_volume = volume_to_mixing_2 + volume_mixing_2_to_outlet
            p.logger_pump.debug("""ramping volume: {}\nvolume to mixing 2: {}
                                volume mixing 2 to outlet: {}""".format(round(ramping_volume, 1),
                                                                        round(volume_to_mixing_2, 1),
                                                                        round(volume_mixing_2_to_outlet, 1))
                                )

            self.name.insert(0, "Waste (channel)")
            self.name.insert(0, "Waste (ramping)")
            p.logger_pump.debug("""dead volumes:\n inlet to mixing 2: {}
                                mixing 2 to outlet: {}""".format(round(volume_to_mixing_2, 1),
                                                                 round(volume_mixing_2_to_outlet, 1))
                                )
            # passing a list to the logging function raises a TypeError
            p.logger_pump.debug("name: {}".format(self.name))

            total_V_group1 = total_V_FR_calculation(self.inlet_group_1)[0]
            total_FR_group1 = total_V_FR_calculation(self.inlet_group_1)[1]
            total_V_group2 = total_V_FR_calculation(self.inlet_group_2)[0]
            total_FR_group2 = total_V_FR_calculation(self.inlet_group_2)[1]

            # create a list of the volumes to be gathered at the outlet.
            total_v_outlet = [ramping_volume, dead_volume]
            for i in range(self.runs + self.runs - 1):  # number of runs + number of overlaps
                all_volumes = 0
                if self.volumes_LA120:
                    all_volumes += self.volumes_LA120[i]*self.pump_configuration_n["LA120"]
                if self.volumes_LA122:
                    all_volumes += self.volumes_LA122[i]*self.pump_configuration_n["LA122"]
                if self.volumes_LA160:
                    all_volumes += self.volumes_LA160[i]*self.pump_configuration_n["LA160"]
                total_v_outlet.append(all_volumes)  # zB total_v_run1, overlap, total_v_run2, overlap, total_v_run3
            p.logger_pump.debug("total_v_outlet: {}".format(total_v_outlet))

            volume_to_mixing_2_time = volume_to_mixing_2 / total_FR_group1[0]*3600
            # passing lists to the logging function raises a TypeError
            p.logger_pump.debug("total vols: Group 1: {}\nGroup 2: {}".format(total_V_group1,
                                                                              total_V_group2)
                                )
            p.logger_pump.debug("total FRs: Group 1: {}\nGroup 2: {}".format(total_FR_group1,
                                                                             total_FR_group2)
                                )

            # calculate time points group 1 and group 2 in sec. and sort them in ascending order in a new list.
            time_points_1 = [ramping_time]
            time_points_2 = [volume_to_mixing_2_time,
                             volume_to_mixing_2_time + ramping_time]

            ramping_volume = self.ramping.mean_flowrate * ramping_time / 3600

            # create a sorted list of all time points
            for i in range(len(total_V_group1)):
                if total_FR_group1[i] != 0:
                    time_points_1.append(time_points_1[i] + total_V_group1[i] / total_FR_group1[i] * 3600)
                else:
                    pass

            for i in range(len(total_V_group2)):
                if total_FR_group2[i] != 0:
                    time_points_2.append(time_points_2[i + 1] + total_V_group2[i] / total_FR_group2[i] * 3600)
                else:
                    pass

            time_points_total = sorted(time_points_1 + time_points_2)

            # insert the flow rates and volumes for the additional events
            # (waiting and ramping) into total_V and total_FR of each group
            # ramping
            total_V_group2.insert(0, ramping_volume)
            total_FR_group2.insert(0, self.ramping.mean_flowrate)
            total_V_group1.insert(0, ramping_volume)
            total_FR_group1.insert(0, self.ramping.mean_flowrate)
            # waiting
            total_V_group2.insert(0, 0)
            total_FR_group2.insert(0, 0)
            total_V_group1.append(0)
            total_FR_group1.append(0)

            # calculate total FR and Volumes for each time period
            i, j = 0, 0
            total_FR = []
            total_V = []
            prev_time = 0
            for time in time_points_total:
                div_time = time - prev_time
                if time in time_points_1:
                    total_FR.append(total_FR_group1[i] + total_FR_group2[j])
                    total_V.append((total_FR_group1[i] + total_FR_group2[j]) * div_time / 3600)
                    i += 1

                if time in time_points_2:
                    total_FR.append(total_FR_group1[i] + total_FR_group2[j])
                    total_V.append((total_FR_group1[i] + total_FR_group2[j]) * div_time / 3600)
                    j += 1
                prev_time = time

            # calculate the time points for collecting the product from the outlet
            collecting_calculation_2()

            # start pumps connected to inlets 1_1 and 1_2.
            pump_inlet_1_1.start()
            if pump_inlet_2_1:
                pump_inlet_1_2.start()
            p.logger_pump.debug("""Steps: {}\nTime points 1: {}\nTime points 2: {}
            Time points total: {}\nTime list: {}""".format(self.name,
                                                           time_points_1,
                                                           time_points_2,
                                                           time_points_total,
                                                           self.time_list))
            for i in range(len(self.name[:-1])):
                if i == 0:
                    countdown(time_points_2[0], self.name[i])
                    p.logger_pump.debug("{}: {}".format(self.name[i],
                                                        round(time_points_2[0]))
                                        )
                    # start pumps connected to inlet 2_1 and inlet 2_2.
                    pump_inlet_2_1.start()
                    if pump_inlet_2_2:
                        pump_inlet_2_2.start()
                    countdown(round(self.time_list[i] - time_points_2[0]), self.name[i])  # countdown

                    p.logger_pump.debug("{}: {}".format(self.name[i],
                                                        round(self.time_list[i] - time_points_2[0]))
                                        )
                else:
                    countdown(round(self.time_list[i]), self.name[i])
                    p.logger_pump.debug("{}: {}".format(self.name[i], round(self.time_list[i])))  # countdown

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
            if "y" in resp.lower():
                for item in sorted(c.channel_dict):
                    print("{}: {}".format(sorted(c.channel_dict).index(item) + 1, item))
                channel_number = input("> ")
                try:
                    number = int(channel_number)
                    if number <= len(sorted(c.channel_dict)):
                        self.channel_used = sorted(c.channel_dict)[number - 1]
                        p.logger_pump.info("Selected channel: {}.".format(self.channel_used))
                        return self.mixing(channel_used, countdown, dict_pump_instances, channel_instance,
                                           pumps_active, pumps_adr, ramping_time=0, dict_rate_pumps={})
                    else:
                        print("There is no channel with number {}.".format(number))
                        return self.mixing(channel_used, countdown, dict_pump_instances, channel_instance,
                                           pumps_active, pumps_adr, ramping_time=0, dict_rate_pumps={})
                except ValueError:
                    print("Please select a number between 1 and {}.".format(len(sorted(c.channel_dict))))
                    return self.mixing(channel_used, countdown, dict_pump_instances, channel_instance,
                                       pumps_active, pumps_adr, ramping_time=0, dict_rate_pumps={})
