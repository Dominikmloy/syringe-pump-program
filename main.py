#!/usr/bin/python

import channels as c
import Module_pumps as p
import syringes as s
import re

pumps = {"LA120": "01", "LA122": "02", "LA160": "03"}
chain = p.Chain("/dev/ttyUSB0")
syringes = s.Syringes()
max_flowrate = 1300
pumps_active = {"LA120": False, "LA122": False, "LA160": False}

rates_LA120 = []
rates_LA122 = []
rates_LA160 = []

vol_LA120 = []
vol_LA122 = []
vol_LA160 = []

dict_phase_number_LA120 = {}
dict_phase_number_LA122 = {}
dict_phase_number_LA160 = {}

pump_configuration_n = {} # stores number of syringes in each pump
pump_configuration_syr = {} # stores syringe type in each pump
dict_rates_pumps = {}
dict_units_pumps = {}

phn_global = 0
# channel = c.Channel("single_meander.txt")

# ask user which syringes to use.
def select_syringe_washing():
    """
    This function lets the user choose one of the syringes from the syringes.py
    module. It is assumed that all inlets are connected to this syringe type.
    """
    print("Select syringe used for washing:")
    for item in sorted(syringes.syringes):
        print("{}: {}".format(sorted(syringes.syringes).index(item) + 1, item))
    syringeNumber = input("> ")
    try:
        number = int(syringeNumber)
        if number <= len(sorted(syringes.syringes)):
            syringe_washing = sorted(syringes.syringes)[number - 1]
            p.logger_pump.info("Selected syringe for washing: {}.".format(syringe_washing))
            return syringe_washing
        else:
            print("There is no syringe with number {}.".format(number))
            return select_syringe_washing()
    except ValueError:
        print("Please select a number between 1 and {}.".format(len(sorted(syringes.syringes))))
        return select_syringe_washing()

# ask user which channel is used.
def select_channel():
    """
    This function lets the user choose on of the channels from the channels.py
    module. This choice is essential to the program because the channel's
    properties define number of syringes and volume to be dispensed.
    """
    print("Select channel:")
    for item in sorted(c.channel_dict):
        print("{}: {}".format(sorted(c.channel_dict).index(item) + 1, item))
    channelNumber = input("> ")
    try:
        number = int(channelNumber)
        if number <= len(sorted(c.channel_dict)):
            channel_used = sorted(c.channel_dict)[number - 1]
            p.logger_pump.info("Selected channel: {}.".format(channel_used))
            return channel_used
        else:
            print("There is no channel with number {}.".format(number))
            return select_channel()
    except ValueError:
        print("Please select a number between 1 and {}.".format(len(sorted(c.channel_dict))))
        return select_channel()

# can i put this inside of a function and stil access the instances in all the other functions?
try:
    LA120 = p.Pump(chain, str(sorted(pumps)[0]), str(pumps[sorted(pumps)[0]]))
    pumps_active["LA120"] = True
except p.PumpError:
    p.logger_pump.info("{} is not responding at address {}.".format(sorted(pumps)[0],
                                                                   pumps[sorted(pumps)[0]]))
try:
    LA122 = p.Pump(chain, sorted(pumps)[1], pumps[sorted(pumps)[1]])
    pumps_active["LA122"] = True
except p.PumpError:
    p.logger_pump.info("{} is not responding at address {}.".format(sorted(pumps)[1],
                                                                   pumps[sorted(pumps)[1]]))
try:
    LA160 = p.Pump(chain, sorted(pumps)[2], pumps[sorted(pumps)[2]])
    pumps_active["LA160"] = True
except p.PumpError:
    p.logger_pump.info("{} is not responding at address {}.".format(sorted(pumps)[2],
                                                                   pumps[sorted(pumps)[2]]))

def washing():
    """
    This function needs to be called in the beginning and end of each program to
    wash the channel. The program assumes that all inlets of the chosen channel
    from select_channel() are connected to the same syringe type from
    select_syringe_washing(). Each pump will run with the max.max_flowrate /
    number of inlets. After washing has finished, syringes need to be changed.
    """
    number_of_active_pumps = sum(value == True for value in pumps_active.values())
    channel = c.Channel(c.channel_dict[selected_channel])
    volume_tubing_total = 0
    for key in channel.tubing_x:
        volume_tubing_total += channel.volume_tubing(key)
    volume_per_syr = (channel.volume_total + volume_tubing_total) * 2 / channel.inlets_number # wash twice channel volume
    rate = max_flowrate / channel.inlets_number

    try:
        LA120.status == True
        LA120.diameter(syringes.syringes[syringe_for_washing])
        LA120.volume(volume_per_syr)
        LA120.rate(rate, "ul/h")
        LA120.start()
    except NameError:
        pass

    try:
        LA122.status == True
        LA122.diameter(s.Syringes.syringes[syringe_for_washing])
        LA122.volume(volume_per_syr)
        LA122.rate(rate, "ul/h")
        LA122.start()
    except NameError:
        pass

    try:
        LA160.status == True
        LA160.diameter(s.Syringes.syringes[syringe_for_washing])
        LA160.volume(volume_per_syr)
        LA160.rate(rate, "ul/h")
        LA160.start()
    except NameError:
        pass
    # TODO: if pumps are starting at different times, put "pump.start()" ans Ende bzw versuche es mit broadcast start.
    # TODO: needs some way to assign a phase number to each step -> list?
def select_syringe_mixing():
    pass
    # TODO: hier müssen noch die syringes (v.a. diameters) für den nächsten Schritt eingetragen werden

def ramping ():
    """
    This function asks the configuration of each pump (which syringe?, how many?,
    final flow rate? [that means what is the flow rate of the first mixing exp?])
    and ramps each pump's flow rate up (or down) to have each educt at the same
    time at the mixing zone.
    """
    pump_max_syr = {"LA120": 2, "LA122": 2, "LA160": 8} # max number of syringes target pump can hold.
    # get the number of syringes in each pump.
    for key in sorted(pumps_active):
        if pumps_active[key] == True:
            print("How many syringes are in pump {}?".format(key))
            number = input("> ")
            try:
                if int(number) <= pump_max_syr[key]:
                    pump_configuration_n[key] = int(number)
                    p.logger_pump.info("{} holds {} syringe(s).".format(key, number))
                else:
                    print("Pump {} cannot hold {} syringes.".format(key, number))
                    return ramping()
            except ValueError:
                print("'{}' is not a valid number of syringes.".format(number))
                return ramping()
        else:
            pass
    # get the type of syringes in each pump.
    for key in pump_configuration_n.keys():
        print("Which syringe type is in pump {}?".format(key))
        for syr in sorted(syringes.syringes):
            print("{}: {}.".format(sorted(syringes.syringes).index(syr) + 1, syr))
        number = input("> ")
        try:
            if int(number) <=  len(sorted(syringes.syringes)):
                pump_configuration_syr[key] = sorted(syringes.syringes)[int(number) - 1]
                p.logger_pump.info("{} is equipped with syringe {}.".format(key, pump_configuration_syr[key]))
            else:
                print("There is no syringe with number {}.".format(number))
                return ramping()
        except ValueError:
                print("Please select a number between 1 and {}.".format(len(sorted(syringes.syringes))))
                return ramping()
    # alternative: log only the final result: which pumps, which and number of syringes.
    for key in pump_configuration_syr.keys():
        p.logger_pump.info("{} holds {} syringe(s). Type: {}".format(key,
                                                                  pump_configuration_n[key],
                                                                  pump_configuration_syr[key]))
    # get the volume of each tubing.
    channel = c.Channel(c.channel_dict[selected_channel])
    dict_tubing_volume = {}
    for key in channel.tubing_x.keys():
        if channel.tubing_x[key] > 0:
            dict_tubing_volume[key] = channel.volume_tubing(key)
        else:
            pass
    # get the connection: Which tubing is connected to which pump?
    dict_inlets_pumps = {}
    for inlet in sorted(dict_tubing_volume)[:-1]:
        print("The inlet {} is connected to which pump?".format(inlet))
        for pump in sorted(pump_configuration_syr):
            print("{}: {}".format(sorted(pump_configuration_syr).index(pump) + 1, pump))
        pump = input("> ")
        try:
            if int(pump) <=  len(sorted(pump_configuration_syr)):
                dict_inlets_pumps[inlet] = sorted(pump_configuration_syr)[int(pump) - 1]
                p.logger_pump.info("{} is routed to pump {}.".format(inlet, dict_inlets_pumps[inlet]))
            else:
                print("There is no pump with number {}.".format(pump))
                return ramping()
        except ValueError:
                print("Please select a number between 1 and {}.".format(len(sorted(pump_configuration_syr))))
                return ramping()
    # TODO: activate following lines when working with > 1 pumps.
    # if len(dict_inlets_pumps) == sum(pump_configuration_n.values()):
    #     pass
    # else:
    #     p.logger_pump.warning("""There are {} inlets connected to {} syringes.
    #                           Please repeat the selection process.
    #                           """.format(len(dict_inlets_pumps), sum(pump_configuration_n.values())))
    #     ramping()
        # TODO: ggf besser, für all die einzelnen schritte eine eigene def. zu schreiben und die dann hier nurnoch abzuarbeiten?
    possible_units = ["\u03BCl/min", "\u03BCl/h", "ml/min", "ml/h" ]
    # get the flow rate and its unit that is used for the first mixing experiment.
    # This FR is the last flow rate of the ramping funciton.
    for pump in sorted(pump_configuration_n):
        print("What is the first flow rate for pump {}?".format(sorted(pump_configuration_n)))
        rate = input("> ").replace(",", ".")
        try:
            dict_rates_pumps[pump] = float(rate)
            p.logger_pump.info("{}'s rate is {}.".format(pump, dict_rates_pumps[pump]))
        except ValueError:
                print("Please choose a number.")
                return ramping()
        print("Select the flow rate's unit:")
        for unit in possible_units:
            print("{}: {}".format(possible_units.index(unit) + 1, unit))
        unit = input("> ")
        try:
            if int(unit) <=  len(possible_units):
                dict_units_pumps[pump] = (possible_units)[int(unit) - 1]
                p.logger_pump.info("{}'s unit is {}.".format(pump, dict_units_pumps[pump]))
            else:
                print("There is no unit with number {}.".format(unit))
                return ramping()
        except ValueError:
                print("Please select a number between 1 and {}.".format(len(possible_units)))
                return ramping()
#start ramping.py

    steps = 10
    total_flowrate = 0 # total flowrate: syringes * their flow rates

    for key in pump_configuration_n:
        total_flowrate += pump_configuration_n[key] * dict_rates_pumps[key]
    # calculate mean flowrate
    highest_rate = max(j for i,j in dict_rates_pumps.items() if j > 0)
    list = []
    list.append(total_flowrate * 0.25)
    while len(list) < steps:
        list.append(list[-1] + (highest_rate-list[0])/9)
    mean_flowrate = sum(list)/float(len(list))
    # hier muss ich mir die Einheiten aus dict_units_pumps besorgen und daraus dann die Dauer in Sekunden Berechnen.
    # ggf. in Abhängigkeit von tubing volume? Hätte dann aber den Nachteil, dass die Rektanten zu unterschiedlichen
    # Zeiten in der mixing zone sind. -> Wenn unterschiedliches volume darauf Hinweise, dass sie gleich lang sein
    # müssen. oder mean fr anpassen über Faktor inlet_1/inlet_2
    ramping_time = channel.volume_tubing("inlet_1-1")/mean_flowrate
    # decide if ramping increases flow rate or decreases flow rate to reach the final flow rate
    # append the flow rate to the flow rate list for each step
    for key in dict_rates_pumps.keys():
        if "LA120" in key:
            if dict_rates_pumps[key] > total_flowrate / sum(pump_configuration_n.values()):
                rates_LA120.append(total_flowrate * 0.25)
                while len(rates_LA120) < steps:
                    rates_LA120.append(round(rates_LA120[-1] + (dict_rates_pumps[key]-rates_LA120[0])/9, 3))
            else:
                if dict_rates_pumps[key] < total_flowrate / sum(pump_configuration_n.values()):
                    rates_LA120.append(mean_flowrate * 2 - dict_rates_pumps[key])
                    while len(rates_LA120) < steps:
                        rates_LA120.append(round(rates_LA120[-1] + (dict_rates_pumps[key]-rates_LA120[0])/9, 3))
                else:
                    pass
        elif "LA122" in key:
            if dict_rates_pumps[key] > total_flowrate / sum(pump_configuration_n.values()):
                rates_LA122.append(total_flowrate * 0.25)
                while len(rates_LA122) < steps:
                    rates_LA122.append(round(rates_LA122[-1] + (dict_rates_pumps[key]-rates_LA122[0])/9, 3))
            else:
                if dict_rates_pumps[key] < total_flowrate / sum(pump_configuration_n.values()):
                    rates_LA122.append(round(mean_flowrate * 2 - dict_rates_pumps[key], 3))
                    while len(rates_LA122) < steps:
                        rates_LA122.append(round(rates_LA122[-1] + (dict_rates_pumps[key]-rates_LA122[0])/9, 3))
                else:
                    pass
        elif "LA160" in key:
            if dict_rates_pumps[key] > total_flowrate / sum(pump_configuration_n.values()):
                rates_LA160.append(total_flowrate * 0.25)
                while len(rates_LA160) < steps:
                    rates_LA160.append(round(rates_LA160[-1] + (dict_rates_pumps[key]-rates_LA160[0])/9, 3))
            else:
                if dict_rates_pumps[key] < total_flowrate / sum(pump_configuration_n.values()):
                    rates_LA160.append(mean_flowrate * 2 - dict_rates_pumps[key])
                    while len(rates_LA160) < steps:
                        rates_LA160.append(round(rates_LA160[-1] + (dict_rates_pumps[key]-rates_LA160[0])/9, 3))
                else:
                    pass
        else:
            pass
    # calculate volume per step and write it into a list
    time_per_step = ramping_time / steps # make sure, that this has the same time unit as rate
    if len(rates_LA120) > 0:
        for rate in rates_LA120:
            vol_LA120.append(round(rate * time_per_step, 3))
    else:
        pass
    if len(rates_LA122) > 0:
        for rate in rates_LA122:
            vol_LA122.append(round(rate * time_per_step, 3))
    else:
        pass
    if len(rates_LA160) > 0:
        for rate in rates_LA160:
            vol_LA160.append(round(rate * time_per_step, 3))
    else:
        pass
    # write rate and volume to target pump and store rate and associated phase number in dict.
    if len(rates_LA120) > 0 and len(vol_LA120) > 0:
        dict_phase_number_LA120 = {}
        for rate in rates_LA120:
            phn_LA120 = rates_LA120.index(rate) + 1
            dict_phase_number_LA120[phn_LA120] = rate
            LA120.phase_number(phn_LA120)
            LA120.rate(rate, dict_units_pumps["LA120"])
            LA120.volume(vol_LA120[rates_LA120.index(rate)])
        # I am not sure if I need the following lines.
        # if phn_global == 0:
        #     phn_global= len(dict_phase_number_LA120)
        # elif phn_global!= 0 and phn_global!= len(dict_phase_number_LA120):
        #     p.logger_pump.warning("Global phase number ({}) is different from LA120's phase number ({})".format(phn, len(dict_phase_number_LA120)))
        # else:
        #     pass
        p.logger_pump.info("Pump LA120 ramps from {} to {} {} in {} s.".format(
                           rates_LA120[0], rates_LA120[-1],
                           dict_units_pumps["LA120"], round(ramping_time*3600, 1))) # sollte ramping time oben in sekunden geändert werden, bitte hier 3600 entfernen.
    else:
        passLA120.
    # write rate and volume to target pump and store rate and associated phase number in dict.
    if len(rates_LA122) > 0 and len(vol_LA122) > 0:
        dict_phase_number_LA122 = {}
        for rate in rates_LA122:
            phn_LA122 = rates_LA122.index(rate) + 1
            dict_phase_number_LA122[phn_LA122] = rate
            LA122.phase_number(phn_LA122)
            LA122.rate(rate, dict_units_pumps["LA122"])
            LA122.phase_number(phn_LA122) # ist das notwendig?
            LA122.volume(vol_LA122[rates_LA122.index(rate)])
        # if phn_global== 0:
        #     phn_global= len(dict_phase_number_LA122)
        # elif phn_global!= 0 and phn_global!= len(dict_phase_number_LA122):
        #     p.logger_pump.warning("Global phase number ({}) is different from LA122's phase number ({})".format(phn, len(dict_phase_number_LA122)))
        # else:
        #     pass
        p.logger_pump.info("Pump LA122 ramps from {} to {} {} in {} s.".format(
                           rates_LA122[0], rates_LA122[-1],
                           dict_units_pumps["LA122"], round(ramping_time*3600, 1))) # sollte ramping time oben in sekunden geändert werden, bitte hier 3600 entfernen.
    else:
        pass

    if len(rates_LA160) > 0 and len(vol_LA160) > 0:
        dict_phase_number_LA160 = {}
        for rate in rates_LA160:
            phn_LA160 = rates_LA160.index(rate) + 1
            dict_phase_number_LA160[phn_LA160] = rate
            LA160.phase_number(phn_LA160)
            LA160.rate(rate, dict_units_pumps["LA160"])
            LA160.phase_number(phn_LA160) # ist das notwendig?
            LA160.volume(vol_LA160[rates_LA160.index(rate)])
        # if phn_global== 0:
        #     phn_global= len(dict_phase_number_LA160)
        # elif phn_global!= 0 and phn_global!= len(dict_phase_number_LA160):
        #     p.logger_pump.warning("Global phase number ({}) is different from LA160's phase number ({})".format(phn, len(dict_phase_number_LA160)))
        # else:
        #     pass
        p.logger_pump.info("Pump LA160 ramps from {} to {} {} in {} s.".format(
                           rates_LA160[0], rates_LA160[-1],
                           dict_units_pumps["LA160"], round(ramping_time*3600, 1))) # sollte ramping time oben in sekunden geändert werden, bitte hier 3600 entfernen.
    else:
        pass

#stop ramping.py
# TODO: anstatt bei jedem Fehler wieder die ramping methode zu callen, sollte die methode aus vielen untermethoden bestehen, die bei input fehlern wieder neu starten.
    # TODO: depending on the number of syringes, makes sure that
    # TODO: the total flow rate does not exceed 1300? ul/h
    # TODO: asks for final flowrate
    # TODO: takes the volume of each inlet from 'channels' and calculates
    # TODO: a 10 step ramp to final flow rate
    # TODO: write commands to list (== assign phase number)

def mixing ():
    dict_volume_pumps = {}
    # get volume as input to first flow rate.
    for key in dict_rates_pumps:
        print("The first flow rate on pump {} is {} {}.".format(key,
                                                         dict_rates_pumps[key],
                                                         dict_units_pumps[key]))
        print("Which volume is associated with this flow rate?")
        volume = input("> ").replace(",", ".")
        try:
            dict_volume_pumps[key] = float(volume)
            p.logger_pump.info("Mixing step one on {}: {} {} for {} {}.".format(key,
                                                            dict_rates_pumps[key],
                                                            dict_units_pumps[key],
                                                            dict_volume_pumps[key],
                                                            re.findall(r'^.+l', dict_units_pumps[key])
                                                            ))
        except ValueError:
                print("Please choose a number.")
                return mixing()
    print("How many more runs do you want to make?")
    try:
        runs = int(input("> "))
    except ValueError:
        print("Please choose a number.")
        return mixing()
    p.logger_pump.debug("Number of selected runs: {}".format(runs))

    runs_rates_LA120 = []
    runs_rates_LA122 = []
    runs_rates_LA160 = []
    runs_volumes_LA120 = []
    runs_volumes_LA122 = []
    runs_volumes_LA160 = []
    # den Absatz brauchts für jede Pumpe.
    for key in dict_rates_pumps.keys():
        if "LA120" in key:
            i = 0
            runs_LA120 = runs
            while runs_LA120:
                print("Pump {}: What is the flow rate of run number {}?".format(key, 2 + i))
                fr = input("> ").replace(",", ".")
                try:
                    runs_rates_LA120.append(float(fr))
                    p.logger_pump.info("{}'s rate is {}.".format(key, runs_rates_LA120[-1]))
                except ValueError:
                        print("Please choose a number.")
                        return mixing()
                print("Pump {}: What is the volume of run number {}?".format(key, 2 + i))
                vol = input("> ").replace(",", ".")
                try:
                    runs_volumes_LA120.append(float(vol))
                    p.logger_pump.info("{}'s volume is {} {}.".format(key,
                                                        runs_volumes_LA120[-1],
                                                        re.findall(r'^.+l', dict_units_pumps[key])))
                except ValueError:
                        print("Please choose a number.")
                        return mixing()
                runs_LA120 -= 1
                i += 1
        elif "LA122" in key:
            i = 0
            runs_LA122 = runs
            while runs_LA122:
                print("Pump {}: What is the flow rate of run number {}?".format(key, 2 + i))
                fr = input("> ").replace(",", ".")
                try:
                    runs_rates_LA122.append(float(fr))
                    p.logger_pump.info("{}'s rate is {}.".format(key, runs_rates_LA122[-1]))
                except ValueError:
                        print("Please choose a number.")
                        return mixing()
                print("Pump {}: What is the volume of run number {}?".format(key, 2 + i))
                vol = input("> ").replace(",", ".")
                try:
                    runs_volumes_LA122.append(float(vol))
                    p.logger_pump.info("{}'s volume is {} {}.".format(key,
                                                        runs_volumes_LA122[-1],
                                                        re.findall(r'^.+l', dict_units_pumps[key])))
                except ValueError:
                        print("Please choose a number.")
                        return mixing()
                runs_LA122 -= 1
                i += 1
        elif "LA160" in key:
            i = 0
            runs_LA160 = runs
            while runs_LA160:
                print("Pump {}: What is the flow rate of run number {}?".format(key, 2 + i))
                fr = input("> ").replace(",", ".")
                try:
                    runs_rates_LA160.append(float(fr))
                    p.logger_pump.info("{}'s rate is {}.".format(key, runs_rates_LA160[-1]))
                except ValueError:
                        print("Please choose a number.")
                        return mixing()
                print("Pump {}: What is the volume of run number {}?".format(key, 2 + i))
                vol = input("> ").replace(",", ".")
                try:
                    runs_volumes_LA160.append(float(vol))
                    p.logger_pump.info("{}'s volume is {} {}.".format(key,
                                                        runs_volumes_LA160[-1],
                                                        re.findall(r'^.+l', dict_units_pumps[key])))
                except ValueError:
                        print("Please choose a number.")
                        return mixing()
                runs_LA160 -= 1
                i += 1
        else:
            pass
    # write rates and volumes to target pump
    # TODO: include overlap!
    overlap_volume = 8
    if len(runs_rates_LA120) > 0 and len(runs_volumes_LA120) > 0:
        for rate in runs_rates_LA120:
            if runs_rates_LA120.index(rate) == 0:
                phn_LA120 = len(dict_phase_number_LA120) + runs_rates_LA120.index(rate) + 1
                dict_phase_number_LA120[phn_LA120] = rate
                LA120.phase_number(phn_LA120)
                LA120.rate(rate, dict_units_pumps["LA120"])
                LA120.volume(runs_volumes_LA120[runs_rates_LA120.index(rate)])

            else:
                phn_LA120 = len(dict_phase_number_LA120)+ runs_rates_LA120.index(rate) * 2 + 1
                dict_phase_number_LA120[phn_LA120 - 1] = rate
                dict_phase_number_LA120[phn_LA120] = rate
                LA120.phase_number(phn_LA120 - 1)
                LA120.rate(rate, dict_units_pumps["LA120"])
                LA120.volume(overlap_volume)
                LA120.phase_number(phn_LA120)
                LA120.rate(rate, dict_units_pumps["LA120"])
                LA120.volume(runs_volumes_LA120[runs_rates_LA120.index(rate)])
        # TODO: assign and track phn_global over the whole program.
        # if phn_global == 0:
        #     phn_global = len(dict_phase_number_LA120)
        # elif phn_global!= 0 and phn_global!= len(dict_phase_number_LA120):
        #     p.logger_pump.warning("Global phase number ({}) is different from LA120's phase number ({})".format(phn, len(dict_phase_number_LA120)))
        # else:
        #     pass
        run_number = 2
        for rate in runs_rates_LA120:
            p.logger_pump.info("Run {}: Pump LA120 pumps {} for {} {} in {} s.".format(
                           run_number, runs_volumes_LA120[run_number - 2],
                           runs_rates_LA120[run_number - 2],
                           dict_units_pumps["LA120"],
                           round(runs_volumes_LA120[run_number - 2] /
                           runs_rates_LA120[run_number - 2] * 3600, 1)
                           )) # There might be a shorter way to do this.
    else:
        pass
    if len(runs_rates_LA122) > 0 and len(runs_volumes_LA122) > 0:
        for rate in runs_rates_LA122:
            if runs_rates_LA122.index(rate) == 0:
                phn_LA122 = len(dict_phase_number_LA122) + runs_rates_LA122.index(rate) + 1
                dict_phase_number_LA122[phn_LA122] = rate
                LA122.phase_number(phn_LA122)
                LA122.rate(rate, dict_units_pumps["LA122"])
                LA122.volume(runs_volumes_LA122[runs_rates_LA122.index(rate)])
            else:
                phn_LA122 = len(dict_phase_number_LA122) + runs_rates_LA122.index(rate) * 2 + 1
                dict_phase_number_LA122[phn_LA122 - 1] = rate
                dict_phase_number_LA122[phn_LA122] = rate
                LA122.phase_number(phn_LA122 - 1)
                LA122.rate(rate, dict_units_pumps["LA122"])
                LA122.volume(overlap_volume)
                LA122.phase_number(phn_LA122)
                LA122.rate(rate, dict_units_pumps["LA122"])
                LA122.volume(runs_volumes_LA122[runs_rates_LA122.index(rate)])
        # if phn_global == 0:
        #     phn_global = len(dict_phase_number_LA122)
        # elif phn_global!= 0 and phn_global!= len(dict_phase_number_LA122):
        #     p.logger_pump.warning("Global phase number ({}) is different from LA122's phase number ({})".format(phn, len(dict_phase_number_LA122)))
        # else:
        #     pass
        run_number = 2
        for rate in runs_rates_LA122:
            p.logger_pump.info("Run {}: Pump LA122 pumps {} for {} {} in {} s.".format(
                           run_number, runs_volumes_LA122[run_number - 2],
                           runs_rates_LA122[run_number - 2],
                           dict_units_pumps["LA122"],
                           round(runs_volumes_LA122[run_number - 2] /
                           runs_rates_LA122[run_number - 2] * 3600, 1)
                           )) # There might be a shorter way to do this.
    else:
        pass
    if len(runs_rates_LA160) > 0 and len(runs_volumes_LA160) > 0:
        for rate in runs_rates_LA160:
            if runs_rates_LA160.index(rate) == 0:
                phn_LA160 = len(dict_phase_number_LA160) + runs_rates_LA160.index(rate) + 1
                dict_phase_number_LA160[phn_LA160] = rate
                LA160.phase_number(phn_LA160)
                LA160.rate(rate, dict_units_pumps["LA160"])
                LA160.volume(runs_volumes_LA160[runs_rates_LA160.index(rate)])
            else:
                phn_LA160 = len(dict_phase_number_LA160) + runs_rates_LA160.index(rate) * 2 + 1
                dict_phase_number_LA160[phn_LA160 - 1] = rate
                dict_phase_number_LA160[phn_LA160] = rate
                LA160.phase_number(phn_LA160 - 1)
                LA160.rate(rate, dict_units_pumps["LA160"])
                LA160.volume(overlap_volume)
                LA160.phase_number(phn_LA160)
                LA160.rate(rate, dict_units_pumps["LA160"])
                LA160.volume(runs_volumes_LA160[runs_rates_LA160.index(rate)])
        # if phn_global== 0:
        #     phn_global= len(dict_phase_number_LA160)
        # elif phn_global!= 0 and phn_global!= len(dict_phase_number_LA160):
        #     p.logger_pump.warning("Global phase number ({}) is different from LA160's phase number ({})".format(phn, len(dict_phase_number_LA160)))
        # else:
        #     pass
        run_number = 2
        for rate in runs_rates_LA160:
            p.logger_pump.info("Run {}: Pump LA160 pumps {} for {} {} in {} s.".format(
                           run_number, runs_volumes_LA160[run_number - 2],
                           runs_rates_LA160[run_number - 2],
                           dict_units_pumps["LA160"],
                           round(runs_volumes_LA160[run_number - 2] /
                           runs_rates_LA160[run_number - 2] * 3600, 1)
                           )) # There might be a shorter way to do this.
    else:
        pass
    # TODO: takes starting flow rates from 'ramping'
selected_channel = select_channel()
#syringe_for_washing = select_syringe_washing()
#washing()
ramping()
mixing()
