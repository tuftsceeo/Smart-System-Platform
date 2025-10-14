import time
import gc
import machine
from machine import Pin, Timer

print("Running am1.py")

try:
    networking
except NameError:
    print("Trying to load networking from config.py")
    from config import networking
    if networking is None:
        print("Error loading networking, reseting machine")
        machine.reset()

peer_mac = b'\xff\xff\xff\xff\xff\xff'  # Replace with actual MAC
lastPressed = 0
message = "Boop!"

networking.ping(peer_mac)

def boop(pin):
    global lastPressed
    if (time.ticks_ms() - lastPressed > 1000):
        lastPressed = time.ticks_ms()
        networking.ping(peer_mac)
        # networking.echo(peer_mac, message)
        # networking.send(peer_mac, time.ticks_ms())
        print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool: Sent {message} to {peer_mac}")
        # print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool: RSSI table: {networking.rssi()}")

# Button interrupt
switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)

def heartbeat(timer):
    print("")
    boop(None)
    print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Tool Heartbeat: {gc.mem_free()} bytes")
    print("")
    gc.collect()

# Periodic heartbeat timer (every 10 s)
timer = Timer(0)
timer.init(period=10000, mode=Timer.PERIODIC, callback=heartbeat)
