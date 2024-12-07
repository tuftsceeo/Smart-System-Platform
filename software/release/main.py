from machine import Pin
import machine
from config import config

import gc
gc.collect()

import network

print("Running pyscript main")

#just to be safe
sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
sta.active(True)
ap.active(True)
sta.active(False)
ap.active(False)

from ssp_networking import SSP_Networking

#Network
infmsg = False
dbgmsg = False
errmsg = True
configuration = config["configuration"]
if configuration == "AM1":
    infmsg = True
    
networking = SSP_Networking(infmsg, dbgmsg, errmsg)

peer_mac = b'\xff\xff\xff\xff\xff\xff'

import time
global timer

print("{:.3f} Name: {}, ID: {}, Configuration: {}, Sta mac: {}, Ap mac: {}, Version: {}".format(
    (time.ticks_ms() - networking.inittime) / 1000,
    networking.config["name"],
    networking.config["id"],
    networking.config["configuration"],
    networking.sta.mac(),
    networking.ap.mac(),
    networking.config["version"]
))


def idle():
    lastPressed = 0

    message="Boop!"

    def boop(pin):
        global lastPressed
        if(time.ticks_ms()-lastPressed>1000):
            lastPressed = time.ticks_ms()
            networking.aen.ping(peer_mac)
            networking.aen.echo(peer_mac, message)
            networking.aen.send(peer_mac, message)
            print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool: Sent {message} to {peer_mac}")
            print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool: RSSI table: {networking.aen.rssi()}")
            
    #Buttons
    switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
    switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)

    def heartbeat(timer):
        print("")
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

def run_config_module(module_name):
    try:
        with open(module_name + ".py") as f:
            code = f.read()
        exec(code)
    except Exception as e:
        print(f"Error running {module_name}: {e}")

# cases for different configurations
if configuration == "AM1":
    print("idle")
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
