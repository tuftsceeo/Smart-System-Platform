import time


# Network
from ssp_networking import SSP_Networking

# Initialise
infmsg = True
dbgmsg = False
errmsg = True
networking = SSP_Networking(infmsg, dbgmsg, errmsg)

print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Example: Running example.py")
print()


###Example code###

recipient_mac = b'\xff\xff\xff\xff\xff\xff'  # This mac sends to all
message = b'Boop'

# Print device networking configuration
print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Example: Config: {networking.config}")
print()


#Command Types:
# Ping, calculates the time until you receive a response from the peer and adds their infor to the networking address book
networking.ping(recipient_mac)
print()

# Echo, sends a message that will be repeated back by the recipient
networking.echo(recipient_mac, message)
print()

# There are a bunch of more command types, the complete list can be found in the config.py or ssp_networking.py


#Message Type
# Message, sends the specified message to the recipient, supported formats are bytearrays, bytes, int, float, string, bool, list and dict, if above 241 bytes, it will send in multiple packages: max 60928 bytes
networking.send(recipient_mac, message)
print()

# Check if there are any messages in the message buffer, returns True or False
print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Example: {networking.check_messages()}")
print()

# Get Last Received Message
print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Example: {networking.return_message()}")  # Returns none, none, none if there are no messages
print()


#Other
# Get the RSSI table
print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Example: {networking.rssi()}")
print()


#IRQ
# Set up an interrupt which runs a function as soon as possible after receiving a new message
def receive():
    for mac, message, rtime in networking.return_messages():  # You can directly iterate over the function
        print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Example: Received {message} from {peer_mac} at {rtime}")

networking.irq(receive)  # interrupt handler


#Send trigger
#You could set up a function that sends a message to all and is called when the select button on the dahal board is pressed
from machine import Pin
import machine

lastPressed = 0

def boop(pin):
    global lastPressed
    if (time.ticks_ms() - lastPressed > 1000): #prevents button to be called multiple times within 1 second
        lastPressed = time.ticks_ms()
        networking.send(peer_mac, "Hewwo!")
        print(f"{(time.ticks_ms() - networking.inittime) / 1000:.3f} Networking Example: Sent {message} to {peer_mac}")

switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)


#print something on the screen

#set up servo

#set up sensor

