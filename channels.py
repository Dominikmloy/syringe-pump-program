import math
import re

# channel_dict maps the file name of the specification file to the channel's name.
channel_dict = {"Single meander channel": "single_meander.txt",
                "Double meander channel": "double_meander.txt"}


class Channel(object):
    """
    This class holds the variables associated with target channel. It reads the target channel's specifications
    from a text file using regex. The specifications are stored in the variables defined in __init__. Additionally,
    functions for calculating the volume of any segment of the channel and its tubing are defined.
    """
    def __init__(self, filename):
        """
        Holds all variables associated with the target channel. It automatically calculates the total volume
        of the channel + the volume of all inlets and outlets and stores it in the variable self.volume_total.
        """
        self.volume_total = 0
        self.channel_volume = 0
        self.interface_volume = 0  # e.g. the tubing's volume leading to the channels

        def _volume_channel():
            # volume = self.channel_x[section] * self.channel_y[section] * self.channel_z
            if self.volume_total != 0:
                return self.volume_total
            else:
                # calculate total interface volume
                self.interface_volume = (self.inlets_number + self.outlets_number) * \
                                        math.pi * self.interface_diameter ** 2
                # Calculate the volume of each segment of the channel.
                # Sum them up to get the total channel volume
                for key in self.channel_x:
                    volume = self.channel_x[key] * self.channel_y[key] * self.channel_z
                    self.channel_volume += volume
                # add the channel volume to the interface volume for the total volume of the chip
                volume_total = self.channel_volume + self.interface_volume
                return volume_total
        # variables
        self.inlets_number = 0
        self.outlets_number = 0
        self.meanders_number = 0
        self.inlet_diameter = 0
        self.outlet_diameter = 0
        self.interface_diameter = 0
        # dictionaries mapping the length in x, y, z direction of a section [mm] to
        # the respective name of the section. name1-name2 denotes the section between the two names
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
        # reads the channel's specifications from the spec file and stores them in the variables
        # defined under __init__.
        self._set_from_spec_file(filename)
        self.volume_total = _volume_channel()

    def volume_tubing(self, tubing):
        """
        calculates the volume of one inlet or outlet, under the assumption that inlet and outlet
        have the same diameter
        """
        return self.tubing_x[tubing] * (self.inlet_diameter / 2) ** 2 * math.pi

    def volume_channel_section(self, section):
        """calculate the volume of one section of the channel. Assumption: channel height does not change."""
        return self.channel_x[section] * self.channel_y[section] * self.channel_z

    def volume_to_mixing_2(self):
        """
        Calculate the volume of the channels from the inlets to the mixing zone 2.
        This function is only needed for the double meander channel.
        """
        sections = ["inlet_1-1-mixing_1", "inlet_1-2-mixing_1",
                    "inlet_1-3-mixing_1", "mixing_1-meander_1",
                    "meander_1-meander_1", "meander_1-mixing_2"]
        volume = 0
        for section in sections:
            volume += self.volume_channel_section(section)
        return volume

    def _set_from_spec_file(self, filename):
        """
        This function opens the file specified in filename. If/elif statements are used
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
                        else:
                            pass
                elif "channel_x" in line:
                    digit = [float(s.replace(",", ".")) for s in line.split() if re.findall(r'^\d+\.?\d*', s)]
                    for j in self.channel_x.keys():
                        if j in line:
                            self.channel_x[j] = digit[0]
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
                    print('No information was extracted from this line: {}'.format(line))
