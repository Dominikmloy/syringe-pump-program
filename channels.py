import math
import re

# channel_dict maps the file name of the specification file to the channel's name.
channel_dict = {"Single meander channel": "single_meander.txt",
                "Double meander channel": "double_meander.txt"}


class Channel(object):
    def __init__(self, filename):
        """
        :param filename: path to config file
        """
        self.volume_total = 0
        self.channel_volume = 0
        self.interface_volume = 0

        def _volume_channel():  # , section):
            # volume = self.channel_x[section] * self.channel_y[section] * self.channel_z
            if self.volume_total != 0:
                return self.volume_total
            else:
                self.interface_volume = (self.inlets_number + self.outlets_number) * math.pi * self.interface_diameter ** 2
                for key in self.channel_x:
                    volume = self.channel_x[key] * self.channel_y[key] * self.channel_z
                    self.channel_volume += volume
                volume_total = self.channel_volume + self.interface_volume
                return volume_total

        self.inlets_number = 0
        self.outlets_number = 0
        self.meanders_number = 0
        self.inlet_diameter = 0
        self.outlet_diameter = 0
        self.interface_diameter = 0
        self.tubing_x = {"inlet_1-1": 0, "inlet_1-2": 0, "inlet_1-3": 0,
                         "inlet_2-1": 0, "inlet_2-2": 0, "outlet": 0}
        self.channel_x = {"inlet_1-1-mixing_1": 0, "inlet_1-2-mixing_1": 0,
                          "inlet_1-3-mixing_1": 0, "mixing_1-meander_1": 0,
                          "meander_1-meander_1": 0, "meander_1-outlet": 0, "meander_1-mixing_2": 0,
                          "inlet_2-1-mixing_2": 0, "inlet_2-2-mixing_2": 0,
                          "mixing_2-meander_2": 0, "meander_2-meander_2": 0, "meander_2-outlet": 0}
        self.channel_y = {"inlet_1-1-mixing_1": 0, "inlet_1-2-mixing_1": 0,
                          "inlet_1-3-mixing_1": 0, "mixing_1-meander_1": 0,
                          "meander_1-meander_1": 0, "meander_1-outlet": 0, "meander_1-mixing_2": 0,
                          "inlet_2-1-mixing_2": 0, "inlet_2-2-mixing_2": 0,
                          "mixing_2-meander_2": 0, "meander_2-meander_2": 0, "meander_2-outlet": 0}
        self.channel_z = 0
        self._set_from_spec_file(filename)
        self.volume_total = _volume_channel()  # Annahme: aendert sich nicht und wird nur einmal berechnet sobald channels gelesen wurden

    def volume_tubing(self, tubing):
        return self.tubing_x[tubing] * (self.inlet_diameter / 2) ** 2 * math.pi

    def volume_channel_section(self, section):
        return self.channel_x[section] * self.channel_y[section] * self.channel_z

    def volume_to_mixing_2(self):
        sections = ["inlet_1-1-mixing_1", "inlet_1-2-mixing_1",
                    "inlet_1-3-mixing_1", "mixing_1-meander_1",
                    "meander_1-meander_1", "meander_1-mixing_2"]
        volume = 0
        for section in sections:
            volume += self.volume_channel_section(section)
        return volume

    def _set_from_spec_file(self, filename):
        """ This function opens the file specified in filename. If/elif statements are used
        to detect keywords. If a keyword is detected, regex is used to extract the desired
        information. The information is stored in variables defined in __init__.
        """

        with open(filename, "r") as file:  # file is closed automatically when scope is exited.
            for line in file:
                if "inlets_number" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'\d+\.*\d*', s)]
                    self.inlets_number = digit[0]
                elif "outlets_number" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'\d+\.*\d*', s)]
                    self.outlets_number = digit[0]
                elif "meanders_number" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'\d+\.*\d*', s)]
                    self.meanders_number = digit[0]
                elif "inlet_diameter" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'\d+\.*\d*', s)]
                    self.inlet_diameter = digit[0]
                elif "outlet_diameter" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'\d+\.*\d*', s)]
                    self.outlet_diameter = digit[0]
                elif "channel_z" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'\d+\.*\d*', s)]
                    self.channel_z = digit[0]
                elif "interface_diameter" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'\d+\.*\d*', s)]
                    self.interface_diameter = digit[0]
                elif "tubing_x" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'^\d+\.?\d*', s)]
                    for j in self.tubing_x.keys():
                        if j in line:
                            self.tubing_x[j] = digit[0]
                            # break  falls es nur einen Treffer pro zeile geben kann, aber ist wohl nicht so?
                        else:
                            pass
                elif "channel_x" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'^\d+\.?\d*', s)]
                    for j in self.channel_x.keys():
                        if j in line:
                            self.channel_x[j] = digit[0]
                            # break  falls es nur einen Treffer pro zeile gibt
                        else:
                            pass
                elif "channel_y" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'^\d+\.?\d*', s)]
                    for j in self.channel_y.keys():
                        if j in line:
                            self.channel_y[j] = digit[0]
                        else:
                            pass
                else:
                    pass  # warning ausgeben wenn du eigentlich erwartest dass jede zeile geparst wird, aber ist ja vermutlich nicht so
