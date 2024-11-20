import os
from machine import Pin
import gc
gc.collect()

import time

from networking import Networking

#Network
networking = Networking(True, False, True)
peer_mac = b'\xff\xff\xff\xff\xff\xff'

print("Running pyscript networking tool")
print(f"Name: {networking.name}, ID: {networking.id}, config: {networking.config}, Sta mac: {networking.sta.mac()}, Ap mac: {networking.ap.mac()}, Version: {networking.version_n}")


lastPressed = 0
start_time = time.ticks_ms()

message="Boop!"

def boop(pin):
    global lastPressed
    if(time.ticks_ms()-lastPressed>1000):
        lastPressed = time.ticks_ms()
        networking.aen.ping(peer_mac)
        networking.aen.echo(peer_mac, message)
        networking.aen.send(peer_mac, message)
        print(f"Sent {message} to {peer_mac}")
        print(networking.aen.rssi())

switch_select = Pin(9, Pin.IN, Pin.PULL_UP)

#Buttons
switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)

while True:
    print(f"{int(time.ticks_ms()-start_time)/1000}: {gc.mem_free()} bytes")
    time.sleep(1)
    gc.collect()


