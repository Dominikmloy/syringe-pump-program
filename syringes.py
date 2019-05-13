

class Syringes(object):
    def __init__(self):
        self.syringes = {"Hamilton_1001TLL_1ml": 4.61, "Hamilton_1750TLL-XL_0.5ml": 3.26,
                         "Hamilton_1710TLL-XL_0.1ml": 1.46, "NormJect_tuberkulin_1ml": 4.7}

    def import_syringes(self, name, diameter):
        try:
            assert 0.1 < float(diameter) < 30.0
            self.syringes[name] = float(diameter)
        except AssertionError:
            print("Diameter out of range. Accepted values: 0.1 - 30.0 cm. Syringe not imported.")
            # logger_pump.warning("Diameter out of range. Accepted values: 0.1 - 30.0 cm. Syringe not imported.")
            # logger would be better, dont know yet how to integrate in this module.
