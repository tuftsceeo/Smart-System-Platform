import config
import utime as time
from machine import Pin
import machine

print("Running boot.py")

try:
    time.sleep(3)
except Exception as e:
    print(f"Error {e}")

import gc

gc.collect()

import network

# just to be safe
sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
sta.active(True)
ap.active(True)
sta.active(False)
ap.active(False)

from ssp_networking import SSP_Networking
import ssp_networking

# Network
infmsg = True
dbgmsg = False
errmsg = True
configuration = config.config["configuration"]

config.networking = SSP_Networking(infmsg, dbgmsg, errmsg)
networking = config.networking

print("{:.3f} Name: {}, ID: {}, Configuration: {}, Type: {}, Sta mac: {}, Sta channel: {}, Ap mac: {}, Ap channel: {}, Version: {}".format(
        (time.ticks_ms() - networking.inittime) / 1000,
        networking.config["name"],
        networking.config["id"],
        networking.config["configuration"],
        networking.config["type"],
        networking.config["sta_mac"],
        networking.config["sta_channel"],
        networking.config["ap_mac"],
        networking.config["ap_channel"],
        networking.config["version"]
    ))

def deinit():
    networking.cleanup()
    try:
        timer.deinit()
    except Exception as e:
        print(e)
    machine.reset()

try:
    with open(config.config["configuration"].lower() + ".py") as f:
        code = f.read()
    exec(code, {"networking": networking, "configuration": configuration, "__name__": "__main__"})
except Exception as e:
    print(f"Error running {config.config['configuration']}: {e}")
