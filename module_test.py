import Module_pumps
chain = Module_pumps.Chain("/dev/ttyUSB0")
chain.isOpen()
pump = Module_pumps.Pump(chain, "LA120", "01")
pump.start()
pump.stop()
