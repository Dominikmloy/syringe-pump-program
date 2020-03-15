import ramping_class as r_c
import mixing_class as m_c
import setup
# -- Program: --
# Usage: E.g., Formulation of core nanoparticles with the subsequent addition of an additional component.
# The Double meander channel is washed with 1.0 ml Tuberkulin syringes in pumps LA120, LA122, and LA160.
# LA160 is feeding the outer inlet (inlet1_1) before the first mixing zone,
# while LA120 is feeding the inner inlet (inlet1_2).
# LA122 feeds both inlets before the second mixing zone (inlet2_1 and inlet2_2)
# LA120 is equipped with one Hamilton 0.5 ml syringe, LA160 is equipped with one Hamilton 1.0 ml syringe,
# and LA122 is equipped with two Hamilton 0.1 ml syringes.
# Three mixing runs are executed with Flow_rates_LA120 = [100, 100, 100] ul/h, Flow_rates_LA122 = [25, 50, 75] ul/h
# and Flow_rates_LA160 = [900, 900, 900] ul/h. Respective volumes are volumes_LA120 = [10, 10, 10] ul,
# volumes_LA122 = [3, 6, 9] ul, and volumes_LA160 = [90, 90, 90] ul. Overlap between runs is 8 ul.
# Pump LA160 is used to purge the product from the channel.
# In the end, the user is asked to wash the channel again.

# --------------------------------------------------------------------------------------
# list of variables passed to the functions below.

# -- Prepare the channel --
# select a syringe type from the syringes.py module for washing your channel.
# All active pumps must be equipped with this syringe type.
selected_syringe_washing = "NormJect_tuberkulin_1ml"
# select a channel type from the channels.py module.
selected_channel_washing = "Double meander channel"

# -- ramp your educts to the mixing zone and formulate your products. --
# number of syringes in each pump.
LA120_syringes = 1
LA122_syringes = 2
LA160_syringes = 1
# type of syringes in each pump (select a name from the syringes.py module)
LA120_syringes_type = "Hamilton_1750TLL-XL_0.5ml"
LA122_syringes_type = "Hamilton_1710TLL-XL_0.1ml"
LA160_syringes_type = "Hamilton_1001TLL_1ml"
# mapping of inlets to pumps
inlet1_1 = "LA160"
inlet1_2 = "LA120"
inlet2_1 = "LA122"
inlet2_2 = "LA122"
# number of runs
number_of_runs = 3
# Flow rates of the mixing process
Flow_rates_LA120 = [100, 100, 100]
Flow_rates_LA122 = [25, 50, 75]
Flow_rates_LA160 = [900, 900, 900]
# Units of the flow rates of the mixing process
Units_LA120 = "\u03BCl/h"
Units_LA122 = "\u03BCl/h"
Units_LA160 = "\u03BCl/h"
# volumes of the mixing process
volumes_LA120 = [10, 10, 10]
volumes_LA122 = [3, 6, 9]
volumes_LA160 = [90, 90, 90]
# overlap between runs
overlap_runs = 8
# pumps purging the channel after the last run
pumps_for_purging = ['LA160']

# ------------------------------------------------------------------------------------
# ---- functions ----
# -- setup --
# Define Name and address of all pumps:
pumps = {"LA120": "01", "LA122": "02", "LA160": "03"}
# instantiate global phase number
phase_number = setup.GlobalPhaseNumber()
# make sure which pumps are active, select the channel and the syringes for washing
pumps_setup = setup.Setup(pumps)

# -- washing --
pumps_setup.select_syringe_washing(syringe_washing=selected_syringe_washing)
pumps_setup.select_channel(channel=selected_channel_washing)
pumps_setup.washing()

# -- ramping --
# Interrupt the program until the enter key is pressed in order to allow for time to change the syringes.
input("Press Enter when you are ready to start the ramping and mixing process.")
# ramp your educts to the mixing zone
ramping = r_c.Ramping(pumps_setup.channel_used)
ramping.syringes_number(pumps_setup.pumps_active,
                        LA120=LA120_syringes,
                        LA122=LA122_syringes,
                        LA160=LA160_syringes)
ramping.syringes_type(pumps_setup.dict_pump_instances,
                      pumps_setup.pumps_active,
                      LA120=LA120_syringes_type,
                      LA122=LA122_syringes_type,
                      LA160=LA160_syringes_type)
ramping.tubing_connections(inlet_1_1=inlet1_1,
                           inlet_1_2=inlet1_2,
                           inlet_2_1=inlet2_1,
                           inlet_2_2=inlet2_2)
ramping.first_rate(LA120_rate=Flow_rates_LA120[0],
                   LA122_rate=Flow_rates_LA122[0],
                   LA160_rate=Flow_rates_LA160[0],
                   LA120_unit=Units_LA120,
                   LA122_unit=Units_LA122,
                   LA160_unit=Units_LA160)
ramping.calc_mean_flowrate(pumps_setup.channel)
ramping.ramping_calc()
ramping.writing(phase_number,
                LA120=pumps_setup.dict_pump_instances["LA120"],
                LA122=pumps_setup.dict_pump_instances["LA122"],
                LA160=pumps_setup.dict_pump_instances["LA160"])

# -- mixing --
mixing = m_c.Mixing(ramping_instance=ramping, setup_instance=pumps_setup)
mixing.number_of_runs(runs=number_of_runs)
mixing.rate(pumps_setup.pumps_active,
            LA120_rate=Flow_rates_LA120,
            LA122_rate=Flow_rates_LA122,
            LA160_rate=Flow_rates_LA160,
            LA120_unit=Units_LA120,
            LA122_unit=Units_LA122,
            LA160_unit=Units_LA160)
mixing.volume(pumps_setup.pumps_active,
              LA120=volumes_LA120,
              LA122=volumes_LA122,
              LA160=volumes_LA160)
mixing.overlap_calc(overlap=overlap_runs)
mixing.end_process(pumps_setup.channel,
                   pumps_setup.pumps_active,
                   purging_pumps=pumps_for_purging)

mixing.writing(pumps_setup.dict_pump_instances,
               pumps_setup.pumps_active,
               phase_number)
mixing.mixing(pumps_setup.channel_used,
              setup.countdown,
              pumps_setup.dict_pump_instances,
              pumps_setup.channel,
              pumps_setup.pumps_active,
              pumps,
              ramping_time=ramping.ramping_time,
              dict_rate_pumps=ramping.dict_rates_pumps)

input("Press Enter when you are ready to wash your channel.")
# -- washing --
pumps_setup.select_syringe_washing(syringe_washing=selected_syringe_washing)
pumps_setup.select_channel(channel=selected_channel_washing)
pumps_setup.washing()
