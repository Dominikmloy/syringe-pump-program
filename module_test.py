#!/usr/bin/python
# -*- coding: ascii -*-

import Module_pumps
import time
chain = Module_pumps.Chain("/dev/ttyUSB0")
chain.isOpen()
pump = Module_pumps.Pump(chain, "LA120", "01")
pump.diameter(1.50)
pump.rate(40, "ul/h")
pump.start()
time.sleep(5)
pump.stop()
time.sleep(5)
pump.stop()
