import config
import time
from machine import Pin
import machine

print("Running boot.py")

try:
    time.sleep(3)
except Exception as e:
    print(f"Error {e}")

module_name = config.config["configuration"].lower()

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

peer_mac = b'\xff\xff\xff\xff\xff\xff'

import time

global timer

print("{:.3f} Name: {}, ID: {}, Configuration: {}, Sta mac: {}, Sta channel: {}, Ap mac: {}, Ap channel: {}, Version: {}".format(
        (time.ticks_ms() - networking.inittime) / 1000,
        networking.config["name"],
        networking.config["id"],
        networking.config["configuration"],
        networking.config["sta_mac"],
        networking.config["sta_channel"],
        networking.config["ap_mac"],
        networking.config["ap_channel"],
        networking.config["version"]
    ))

def am1():
    lastPressed = 0

    message = "Boop!"

    networking.ping(peer_mac)

    def boop(pin):
        global lastPressed
        if (time.ticks_ms() - lastPressed > 1000):
            # lastPressed = time.ticks_ms()
            networking.ping(peer_mac)
            # networking.echo(peer_mac, message)
        # networking.send(peer_mac, time.ticks_ms())
        print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool: Sent {message} to {peer_mac}")
        # print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool: RSSI table: {networking.rssi()}")

    # Buttons
    switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
    switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)

    def heartbeat(timer):
        print("")
        boop(None)
        print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool Heartbeat: {gc.mem_free()} bytes")
        print("")
        gc.collect()

    timer = machine.Timer(0)
    timer.init(period=5000, mode=machine.Timer.PERIODIC, callback=heartbeat)


def deinit():
    networking.cleanup()
    try:
        timer.deinit()
    except Exception as e:
        print(e)
    machine.reset()


try:
    if configuration == "AM1":
        am1()
    else:
        with open(module_name + ".py") as f:
            code = f.read()
        exec(code, {"networking": networking, "configuration": configuration, "__name__": "__main__"})
except Exception as e:
    print(f"Error running {module_name}: {e}")