from machine import Pin
import machine
import gc
gc.collect()

import time

print("Running pyscript networking tool")

from networking import Networking

#Network
networking = Networking(True, False, True)
peer_mac = b'\xff\xff\xff\xff\xff\xff'

print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Name: {networking.name}, ID: {networking.id}, config: {networking.config}, Sta mac: {networking.sta.mac()}, Ap mac: {networking.ap.mac()}, Version: {networking.version_n}")

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

switch_select = Pin(9, Pin.IN, Pin.PULL_UP)

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
