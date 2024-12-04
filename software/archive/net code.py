from machine import Pin
import machine
import gc
gc.collect()

import network

print("Running pyscript networking tool")

sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
sta.active(True)
ap.active(True)
sta.active(False)
ap.active(False)

from networking import Networking

#Network
networking = Networking(True, True, True, True)
