import channels as c
import Module_pumps as p
import syringes as s
import ramping_class as r_c
import mixing_class as m_c
import setup
import re

# Define Name and address of all pumps:
pumps = {"LA120": "01", "LA122": "02", "LA160": "03"}
# instantiate global phase number
phase_number = setup.GlobalPhaseNumber()
# make sure which pumps are active, select the channel and the syringes for washing
pumps_setup = setup.Setup(pumps)
pumps_setup.select_syringe_washing()
pumps_setup.select_channel()
#pumps_setup.washing()
#LA160=pumps_setup.dict_pump_instances["LA160"]
#LA160.start()
#setup.countdown(5, "wait")

#LA160.stop()

# ramp your educts to the mixing zone
ramping = r_c.Ramping(pumps_setup.channel_used)
ramping.syringes_number(pumps_setup.pumps_active)
ramping.syringes_type(pumps_setup.dict_pump_instances)
ramping.tubing_connections()
ramping.first_rate()
ramping.calc_mean_flowrate(pumps_setup.channel)
ramping.ramping_calc()
ramping.writing(phase_number,
                LA120=pumps_setup.dict_pump_instances["LA120"],
                LA122=pumps_setup.dict_pump_instances["LA122"],
                LA160=pumps_setup.dict_pump_instances["LA160"])
mixing = m_c.Mixing(ramping_instance=ramping)
mixing.number_of_runs()
mixing.rate(pumps_setup.pumps_active)
mixing.volume(pumps_setup.pumps_active)

mixing.writing(pumps_setup.dict_pump_instances,
               pumps_setup.channel,
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
# La160 = pumps_setup.dict_pump_instances["LA160"]
# La160.start()
