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
        self.dict_rates_pumps = {}  # holds the flow rates of the first run
        self.units_dict = {"\u03BCl/min": "um", "\u03BCl/m": "um", "\u03BC/min": "um",
                           "ml/min": "mm", "ml/m": "mm", "m/min": "mm",
                           "\u03BCl/h": "uh", "\u03BC/h": "uh",
                           "ul/h": "uh", "u/h": "uh",
                           "ml/h": "mh", "m/h": "mh"}

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
        string = ", ".join(key_list)
        return string

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
            p.logger_pump.debug("Error message {}: ".format(error_number),
                                "Function 'number_of_runs()' aborted",
                                " due to errors in the kwargs: {}.".format(runs))
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
            p.logger_pump.debug("Error message {}: ".format(error_number),
                                "Function 'rate()' aborted",
                                " due to errors in the kwargs: {}.\n".format(kwargs),
                                additional_info)
            raise SystemExit("Program aborted.")

        def check_max_flow_rate(question):
            # check if max flow rate is exceeded and ask, if the program
            # should be continued nevertheless or if it should be restarted.
            for i in range(self.runs):
                flow_rate = 0
                if len(self.rates_LA120) > 0:
                    flow_rate += self.rates_LA120[i]
                if len(self.rates_LA122) > 0:
                    flow_rate += self.rates_LA122[i]
                if len(self.rates_LA160) > 0:
                    flow_rate += self.rates_LA160[i]
                p.logger_pump.debug("Total flow rate of run {}: {}".format(i + 1, flow_rate))

                if flow_rate > self.setup.max_flowrate:
                    p.logger_pump.warning(
                        "WARNING! TOTAL FLOW RATE EXCEEDS MAXIMUM FLOW RATE! ({})".format(
                            self.setup.max_flowrate))
                    print("Do you want to {}?".format(question))
                    answer = input("> ")
                    positive_answers = ["y", "j", "yes", "ja"]
                    if answer.lower() in positive_answers:
                        return True
                    else:
                        return False
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
                p.logger_pump.info("Program continuing.")

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
            p.logger_pump.info("Program continuing.")

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
            p.logger_pump.debug("Error message {}: ".format(error_number),
                                "Function 'volume()' aborted",
                                " due to errors in the kwargs: {}.".format(kwargs))
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
            p.logger_pump.debug("Error message {}: ".format(error_number),
                                "Function 'overlap_calc()' aborted",
                                " due to errors in the kwargs: {}.".format(overlap))
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
                print("Please choose a number (type: float).")
                return self.overlap_calc()
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
            print("Error message {}: ".format(error_number),
                  "Function 'purging_pumps()' aborted",
                  " due to errors in the kwargs: {}.".format(purging_pumps))
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
                    print("Please choose a number (1, 2, and / or 3).")
                    return self.end_process(channels_instance, pumps_active)
                p.logger_pump.info("""The following pumps will pump the
                                   final product: {}""".format(", ".join(pumps_end_process)))
        if pumps_end_process:
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
        else:
            p.logger_pump.debug("Channel is not purged after the last run")

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
        If the double meander channel is used, it asks if the user if he/she
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
            # self.dict_inlets_pumps = {}  # holds {'inlet_1_1': 'LA160', 'inlet_1_2': 'LA120', 'inlet_1_3': 'LA160'}
            # self.dict_units_pumps = {}  # holds {'LA120': 'ul/h', 'LA160': 'ul/h'}
            if dict_rate_pumps:
                self.dict_rates_pumps = dict_rate_pumps

            # calculate time reactants need to get to the second inlet
            # convert time to seconds in dict_rates_pumps
            if "h" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_1_1"]]:
                rate_pump_inlet_11 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_1_1"]] / 3600  # change vol / sec
            elif "min" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_1_1"]]:
                rate_pump_inlet_11 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_1_1"]] / 60  # change vol / sec
            if "h" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_1_2"]]:
                rate_pump_inlet_12 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_1_2"]] / 3600  # change vol / sec
            elif "min" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_1_2"]]:
                rate_pump_inlet_12 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_1_2"]] / 60  # change vol / sec
            if "h" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_2_1"]]:
                rate_pump_inlet_21 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_2_1"]] / 3600  # change vol / sec
            elif "min" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_2_1"]]:
                rate_pump_inlet_21 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_2_1"]] / 60  # change vol / sec
            if "h" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_2_2"]]:
                rate_pump_inlet_22 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_2_2"]] / 3600  # change vol / sec
            elif "min" in self.dict_units_pumps[self.dict_inlets_pumps["inlet_2_2"]]:
                rate_pump_inlet_22 = self.dict_rates_pumps[self.dict_inlets_pumps["inlet_2_2"]] / 60  # change vol / sec

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
                pump_inlet_2 = dict_pump_instances[self.dict_inlets_pumps["inlet_2_1"]]
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
            if "Y" in resp.lower():
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
