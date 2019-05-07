import math
import re


class Channel(object):
    def __init__(self, filename):
        """
        :param filename: path to config file
        """

        def _volume_channel(self):  # , section):
            # volume = self.channel_x[section] * self.channel_y[section] * self.channel_z
            if self.volume_total:
                return self.volume_total

            interface_volume = (self.inlets_number + self.outlets_number) * math.pi * self.interface_diameter ** 2
            channel_volume = 0
            for key in self.channel_x:
                volume = self.channel_x[key] * self.channel_y[key] * self.channel_z
                channel_volume += volume
            total_volume = channel_volume + interface_volume
            print(total_volume)
            return total_volume

        self.inlets_number = 0
        self.outlets_number = 0
        self.meanders_number = 0
        self.inlet_diameter = 0
        self.outlet_diameter = 0
        self.interface_diameter = 0
        self.tubing_x = {"inlet_1-1": 0, "inlet_1-2": 0, "inlet_1-3": 0,
                         "outlet": 0}
        self.channel_x = {"inlet_1-1-mixing_1": 0, "inlet_1-2-mixing_1": 0,
                          "inlet_1-3-mixing_1": 0, "mixing_1-meander_1": 0,
                          "meander_1:": 0, "meander_1-outlet": 0, "meander_1-mixing_2": 0,
                          "inlet_2-1-mixing_2": 0, "inlet_2-2-mixing_2": 0,
                          "mixing_2-meander": 0, "meander_2:": 0, "meander_2-outlet": 0}
        self.channel_y = {"inlet_1-1-mixing_1": 0, "inlet_1-2-mixing_1": 0,
                          "inlet_1-3-mixing_1": 0, "mixing_1-meander_1": 0,
                          "meander_1:": 0, "meander_1-outlet": 0, "meander_1-mixing_2": 0,
                          "inlet_2-1-mixing_2": 0, "inlet_2-2-mixing_2": 0,
                          "mixing_2-meander": 0, "meander_2:": 0, "meander_2-outlet": 0}
        self.channel_z = 0
        self._set_from_spec_file(filename)
        self.volume_total = _volume_channel()  # Annahme: aendert sich nicht und wird nur einmal berechnet sobald channels gelesen wurden

    def volume_tubing(self, tubing):
        return self.tubing_x[tubing] * (self.inlet_diameter / 2) ** 2 * math.pi

    def _set_from_spec_file(self, filename):
        #specs = open(filename, "r")
        #specs_list = specs.read().split("\n")
        #for i in specs_list:

        with open(filename, "r") as file:  # file wird automatisch geclosed wenn der with scope verlassen wird
            for line in file:  # stil tipp: benutze i nur wenn es wirklich nur eine zahl ist. Wenn es eine zeile ist, nenne es auch so.
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

