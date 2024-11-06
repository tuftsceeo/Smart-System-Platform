import time
from machine import Pin
from networking import Networking

#Network
networking = Networking()
peer_mac = b'\xff\xff\xff\xff\xff\xff'
message = b'Boop'
random_bytes = os.urandom(300)
print(random_bytes)
lastPressed = 0

def boop(pin):
    global lastPressed
    if(time.ticks_ms()-lastPressed>1000):
        lastPressed = time.ticks_ms()
        networking.aen.message(peer_mac, random_bytes)
        print(f"Sent {random_bytes} to {peer_mac}")

switch_select = Pin(9, Pin.IN, Pin.PULL_UP)

#def receive():
#    for mac, message, rtime in messages:
#        print(mac, message, rtime)
        
#aen.irq(irq_receive)

#Buttons
switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)

while True:
    num = time.ticks_ms()
    #networking.aen.ping(peer_mac)
    print(f"Sent ping to {peer_mac}")
    time.sleep(2)
    if networking.aen.check_messages():
        print("Received the following messages:")
        n = 1
        for mac, message, rtime in networking.aen.return_messages():
            print(f"{n}. At: {rtime} From: {mac} Length: {len(message)} Message: {message}")
            n += 1