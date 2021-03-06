import ramping_class as r_c
import mixing_class as m_c
import setup
# -- Program: --
# Usage: E.g., Formulation of core nanoparticles from two components.
# The Single meander channel is washed with 1.0 ml Tuberkulin syringes in pumps LA120 and LA122.
# Afterwards, LA122 is equipped with one Hamilton 0.5 ml and LA120 is equipped with two Hamilton 1.0 ml syringes.
# Three mixing runs are executed with Flow_rates_LA120 = [63.2, 126.3, 189.5] ul/h, and
# Flow_rates_LA120 = [600, 600, 600] ul/h. Respective volumes are volumes_LA122 = [5, 10, 15] ul, and
# volumes_LA120 = [47.5, 47.5, 47.5] ul. Overlap between runs is 8 ul.
# Pump LA120 is used to purge the product from the channel.
# In the end, the user is asked to wash the channel again.

# --------------------------------------------------------------------------------------
# list of variables passed to the functions below.

# -- Prepare the channel --
# select a syringe type from the syringes.py module for washing your channel.
# All active pumps must be equipped with this syringe type.
selected_syringe_washing = "NormJect_tuberkulin_1ml"
# select a channel type from the channels.py module.
selected_channel_washing = "Single meander channel"

# -- ramp your educts to the mixing zone and formulate your products. --
# number of syringes in each pump.
LA120_syringes = 2
LA122_syringes = 1
# type of syringes in each pump (select a name from the syringes.py module)
LA120_syringes_type = "Hamilton_1750TLL-XL_0.5ml"
LA122_syringes_type = "Hamilton_1001TLL_1ml"
# mapping of inlets to pumps
inlet1 = "LA120"
inlet2 = "LA122"
inlet3 = "LA120"
# number of runs
number_of_runs = 3
# Flow rates of the mixing process
Flow_rates_LA122 = [63.2, 126.3, 189.5]
Flow_rates_LA120 = [600, 600, 600]
# Units of the flow rates of the mixing process
Units_LA120 = "\u03BCl/h"  # ul/h
Units_LA122 = "\u03BCl/h"  # ul/h
# volumes of the mixing process
volumes_LA122 = [5, 10, 15]
volumes_LA120 = [47.5, 47.5, 47.5]
# overlap between runs
overlap_runs = 8
# pumps purging the channel after the last run
pumps_for_purging = ['LA120']

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
                        LA122=LA122_syringes)
ramping.syringes_type(pumps_setup.dict_pump_instances,
                      pumps_setup.pumps_active,
                      LA120=LA120_syringes_type,
                      LA122=LA122_syringes_type)
ramping.tubing_connections(inlet_1_1=inlet1,
                           inlet_1_2=inlet2,
                           inlet_1_3=inlet3)
ramping.first_rate(LA120_rate=Flow_rates_LA120[0],
                   LA122_rate=Flow_rates_LA122[0],
                   LA120_unit=Units_LA120,
                   LA122_unit=Units_LA122)
ramping.calc_mean_flowrate(pumps_setup.channel)
ramping.ramping_calc()
ramping.writing(phase_number,
                LA120=pumps_setup.dict_pump_instances["LA120"],
                LA122=pumps_setup.dict_pump_instances["LA122"])

# -- mixing --
mixing = m_c.Mixing(ramping_instance=ramping, setup_instance=pumps_setup)
mixing.number_of_runs(runs=number_of_runs)
mixing.rate(pumps_setup.pumps_active,
            LA120_rate=Flow_rates_LA120,
            LA122_rate=Flow_rates_LA122,
            LA120_unit=Units_LA120,
            LA122_unit=Units_LA122)
mixing.volume(pumps_setup.pumps_active,
              LA120=volumes_LA120,
              LA122=volumes_LA122)
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
