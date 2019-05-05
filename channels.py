import math
import re

class Channel(object):
    def __init__(self):
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
        # channel_volume = 0: kann man berechnen
        # volume_total = 0: kann man berechnen

    def volume_tubing (self, tubing):
        volume = self.tubing_x[tubing] * (self.inlet_diameter / 2) ** 2 * math.pi

    def volume_channel(self): #, section):
        # volume = self.channel_x[section] * self.channel_y[section] * self.channel_z
        interface_volume = (self.inlets_number + self.outlets_number) * math.pi * self.interface_diameter ** 2
        channel_volume = 0
        for i in self.channel_x.keys():
            volume = self.channel_x[i] * self.channel_y[i] * self.channel_z
            channel_volume += volume
        total_volume = channel_volume + interface_volume
        print(total_volume)

    def read_channel (self, filename):
        specs = open(filename, "r")
        specs_list = specs.read().split("\n")

        for i in specs_list:
            if "inlets_number" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall(r'\d+\.*\d*', s)]
                self.inlets_number = digit[0]
            elif "outlets_number" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall(r'\d+\.*\d*', s)]
                self.outlets_number = digit[0]
            elif "meanders_number" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall(r'\d+\.*\d*', s)]
                self.meanders_number = digit[0]
            elif "inlet_diameter" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall(r'\d+\.*\d*', s)]
                self.inlet_diameter = digit[0]
            elif "outlet_diameter" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall(r'\d+\.*\d*', s)]
                self.outlet_diameter = digit[0]
            elif "channel_z" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall(r'\d+\.*\d*', s)]
                self.channel_z = digit[0]
            elif "interface_diameter" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall(r'\d+\.*\d*', s)]
                self.interface_diameter = digit[0]
            elif "tubing_x" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall(r'^\d+\.?\d*', s)]
                for j in self.tubing_x.keys():
                    if j in i:
                        self.tubing_x[j] = digit[0]
                    else:
                        pass
            elif "channel_x" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall( r'^\d+\.?\d*', s )]
                for j in self.channel_x.keys():
                    if j in i:
                        self.channel_x[j] = digit[0]
                    else:
                        pass
            elif "channel_y" in i:
                digit = [float(s.replace(",", ".")) for s in i.split() if re.findall( r'^\d+\.?\d*', s )]
                for j in self.channel_y.keys():
                    if j in i:
                        self.channel_y[j] = digit[0]
                    else:
                        pass
            else:
                pass
