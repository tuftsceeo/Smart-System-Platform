from machine import Pin
import machine
from config import config
import time
import gc

gc.collect()

import network

print("Running boot.py")

# just to be safe
sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
sta.active(True)
ap.active(True)
sta.active(False)
ap.active(False)

from ssp_networking import SSP_Networking

# Network
infmsg = True
dbgmsg = False
errmsg = True
global timer
peer_mac = b'\xff\xff\xff\xff\xff\xff'
configuration = config["configuration"]
hive = config["hive"]
if configuration == "AM1":
    infmsg = True

networking = SSP_Networking(infmsg, dbgmsg, errmsg)

print("{:.3f} Name: {}, ID: {}, Configuration: {}, Sta mac: {}, Ap mac: {}, Version: {}".format(
    (time.ticks_ms() - networking.inittime) / 1000,
    networking.config["name"],
    networking.config["id"],
    networking.config["configuration"],
    networking.config["ap_mac"],
    networking.config["sta_mac"],
    networking.config["version"]
))

def idle():
    lastPressed = 0
    message = "Boop!"

    def boop(pin):
        global lastPressed
        if (time.ticks_ms() - lastPressed > 1000):
            lastPressed = time.ticks_ms()
            networking.ping(peer_mac)
            networking.echo(peer_mac, message)
            networking.send(peer_mac, message)
            print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool: Sent {message} to {peer_mac}")
            print(
                f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool: RSSI table: {networking.rssi()}")

    # Buttons
    switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
    switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)

    def heartbeat(timer):
        print("")
        print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool Heartbeat: {gc.mem_free()} bytes")
        print("")
        gc.collect()

    timer = machine.Timer(0)
    timer.init(period=5000, mode=machine.Timer.PERIODIC, callback=heartbeat)

def run_config_module(module_name):
    try:
        with open(module_name + ".py") as f:
            code = f.read()
        exec(code)
    except Exception as e:
        print(f"Error running {module_name}: {e}")

# cases for different configurations
if not hive:
    if configuration == "AM1":
        print("am1")
        idle()
    elif configuration == "SM3":
        print("sm3")
        run_config_module("sm3")
    elif configuration == "SL1":
        print("sl1")
        run_config_module("sl1")
    else:
        print("idle")
        idle()
else:
    run_config_module("hm1")
    # insert code here to run in case of hive motor!

