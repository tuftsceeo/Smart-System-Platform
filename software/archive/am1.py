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

from networking import Networking

#Network
infmsg = False
dbgmsg = False
errmsg = True
configuration = config["configuration"]
if configuration == "AM1":
    infmsg = True
    
networking = Networking(infmsg, dbgmsg, errmsg)

peer_mac = b'\xff\xff\xff\xff\xff\xff'

import time

print("{:.3f} Name: {}, ID: {}, Configuration: {}, Sta mac: {}, Ap mac: {}, Version: {}".format(
    (time.ticks_ms() - networking.inittime) / 1000,
    networking.config["name"],
    networking.config["id"],
    networking.config["configuration"],
    networking.sta.mac(),
    networking.ap.mac(),
    networking.config["version"]
))

if configuration == "AM1":
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
    timer.deinit()
    machine.reset()
