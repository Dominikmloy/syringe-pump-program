import setup
# -- Program: --
# This program stops all pumps.

# ------------------------------------------------------------------------------------
# ---- functions ----
# -- setup --
# Define Name and address of all pumps:
pumps = {"LA120": "01", "LA122": "02", "LA160": "03"}
# make sure which pumps are active, select the channel and the syringes for washing
pumps_setup = setup.Setup(pumps)

# -- issue stop command --
pumps_setup.LA120.stop()
pumps_setup.LA122.stop()
pumps_setup.LA160.stop()
print("all pumps stopped")
