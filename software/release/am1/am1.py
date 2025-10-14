import time
import gc
import machine
from machine import Pin, Timer

print("running am1.py")

lastPressed = 0
message = "Boop!"
peer_mac = b'\xff\xff\xff\xff\xff\xff'

try:
    networking
except NameError:
    from config import networking

# Ping once at startup
networking.ping(peer_mac)

# Button handler
def boop(pin):
    global lastPressed
    if (time.ticks_ms() - lastPressed > 1000):
        lastPressed = time.ticks_ms()
        networking.ping(peer_mac)
        # networking.echo(peer_mac, message)
    # networking.send(peer_mac, time.ticks_ms())
    print(f"{(time.ticks_ms() - networking.inittime)/1000:.3f} "
          f"Networking Tool: Sent {message} to {peer_mac}")
    # print(f"{(time.ticks_ms() - networking.inittime)/1000:.3f} Networking Tool RSSI: {networking.rssi()}")

# Setup button interrupt
switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)

# Heartbeat called by timer
def heartbeat(timer):
    print("")
    boop(None)  # safely call boop from timer
    print(f"{(time.ticks_ms() - networking.inittime)/1000:.3f} "
          f"Networking Tool Heartbeat: {gc.mem_free()} bytes")
    print("")
    gc.collect()

# Periodic timer
timer = Timer(0)
timer.init(period=5000, mode=Timer.PERIODIC, callback=heartbeat)
