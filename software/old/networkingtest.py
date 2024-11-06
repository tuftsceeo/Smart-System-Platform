gc.collect()
print(gc.mem_free())

import time
from machine import Pin
from networking import Networking

import urandom
import os

#Network
networking = Networking()
peer_mac = b'\xff\xff\xff\xff\xff\xff'

message_str = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
print(f"String: {message_str}")
message_int = int(''.join(str(urandom.getrandbits(4)) for _ in range(300)))
print(f"Int: {message_int}")
message_float = float(str(message_int) + ".0123456789")
print(f"Float: {message_float}")
message_dict = {f"key_{i}": urandom.getrandbits(16) for i in range(50)}
print(f"Dict: {message_dict}")
message_list = [urandom.getrandbits(16) for _ in range(75)]
print(f"List: {message_list}")
message_bytes = os.urandom(1000)
print(f"Bytes: {message_bytes}")
message_bytearray = bytearray(os.urandom(1000))
print(f"Bytearray: {message_bytearray}")

lastPressed = 0
start_time = time.ticks_ms()

message = "Boop!"


test = True
waiting = False

if test:
    
    def receive():
        global waiting
        for mac, message, rtime in messages:
            print(f"\033[34mMessage received: {mac, message, rtime}\033[0m")
        waiting = False
        
    networking.aen.irq(receive)
    
    try:
        networking.aen.add_peer(peer_mac)
        print("\033[32mTest add_peer passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest add_peer failed: {e}\033[0m")
    try:
        networking.aen.update_peer(peer_mac)
        print("\033[32mTest update_peer passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest update_peer failed: {e}\033[0m")
    try:    
        networking.aen.remove_peer(peer_mac)
        print("\033[32mTest remove_peer passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest remove_peer failed: {e}\033[0m")
    
    try:
        print(networking.aen.peers())
        print("\033[32mTest peers passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest peersfailed: {e}\033[0m")
    try:
        print(networking.aen.rssi())
        print("\033[32mTest rssi passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest rssifailed: {e}\033[0m")
        
    try:
        networking.aen.ping(peer_mac)
        print("\033[34mWaiting for pong\033[0m")
        time.sleep(0.02)
        print("\033[32mTest ping passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest ping failed: {e}\033[0m")
    try:
        networking.aen.echo(peer_mac, message)
        print("\033[34mWaiting for echo\033[0m")
        time.sleep(0.02)
        print("\033[32mTest echo passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest echo failed: {e}\033[0m")
    try:
        networking.aen.broadcast(message)
        print("\033[32mTest broadcast passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest broadcast failed: {e}\033[0m")
        
    try:
        networking.aen.echo(peer_mac, message_str)
        print("\033[34mWaiting for echo\033[0m")
        time.sleep(2)
        print("\033[32mTest long string passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest long string failed: {e}\033[0m")
    try:
        networking.aen.echo(peer_mac, message_int)
        print("\033[34mWaiting for echo\033[0m")
        time.sleep(2)
        print("\033[32mTest long int passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest long int failed: {e}\033[0m")
    try:
        networking.aen.echo(peer_mac, message_float)
        print("\033[34mWaiting for echo\033[0m")
        time.sleep(2)
        print("\033[32mTest long float passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest long float failed: {e}\033[0m")
    try:
        networking.aen.echo(peer_mac, message_dict)
        print("\033[34mWaiting for echo\033[0m")
        time.sleep(2)
        print("\033[32mTest long dict passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest long dict failed: {e}\033[0m")
    try:
        networking.aen.echo(peer_mac, message_list)
        print("\033[34mWaiting for echo\033[0m")
        time.sleep(2)
        print("\033[32mTest long list passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest long list failed: {e}\033[0m")
    try:
        networking.aen.echo(peer_mac, message_bytes)
        print("\033[34mWaiting for echo\033[0m")
        time.sleep(3)
        print("\033[32mTest long bytes passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest long bytes failed: {e}\033[0m")
    try:
        networking.aen.echo(peer_mac, message_bytearray)
        print("\033[34mWaiting for echo\033[0m")
        time.sleep(3)
        print("\033[32mTest long bytearray passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest long bytearray failed: {e}\033[0m")
    
    try:
        print(networking.aen.check_messages())
        print("\033[32mTest check_messages passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest check_messages failed: {e}\033[0m")
    try:
        print(networking.aen.return_message())
        print("\033[32mTest return_message passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest return_message failed: {e}\033[0m")
    try:        
        print(networking.aen.return_messages())
        print("\033[32mTest return_messages passed\033[0m")
    except Exception as e:
        print(f"\033[31mTest return_messages failed: {e}\033[0m")

    networking.aen.irq(None)


def boop(pin):
    global lastPressed
    if(time.ticks_ms()-lastPressed>1000):
        lastPressed = time.ticks_ms()
        networking.aen.send(peer_mac, message)
#         print(f"Sent {random_bytes} to {peer_mac}")

switch_select = Pin(9, Pin.IN, Pin.PULL_UP)

#Buttons
switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=boop)

print(networking.aen.rssi())

while True:
    print(f"{int(time.ticks_ms()-start_time)/1000}: {gc.mem_free()}")
    #networking.aen.ping(peer_mac)
    #print(f"Sent ping to {peer_mac}")
    time.sleep(0.1)
    if networking.aen.check_messages():
        print("Received the following messages:")
        n = 1
        for mac, message, rtime in networking.aen.return_messages():
            print(f"{n}. At: {rtime} From: {mac} Length: {len(message)} Message: {message}")
            n += 1
    gc.collect()
