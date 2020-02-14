import Module_pumps as p


class Syringes(object):
    """
    This class holds the specifications of all syringes. New syringes can be added to the
    dictionary on the fly with the import_syringes function.
    """
    def __init__(self):
        # this dictionary maps the name of the syringe to its diameter in mm.
        self.syringes = {"Hamilton_1001TLL_1ml": 4.61, "Hamilton_1750TLL-XL_0.5ml": 3.26,
                         "Hamilton_1710TLL-XL_0.1ml": 1.46, "NormJect_tuberkulin_1ml": 4.7}

    def import_syringes(self, name, diameter):
        # this function adds a new syringe to the dictionary 'self.syringes'.
        try:
            assert 0.1 < float(diameter) < 30.0
            self.syringes[name] = float(diameter)
        except AssertionError:
            p.logger_pump.warning("Diameter out of range. Accepted values: 0.1 - 30.0 cm. Syringe not imported.")
