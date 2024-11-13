from machine import Pin, SoftI2C, PWM, ADC


#custom libraries
import network
from secrets import codes

#libraries
import espnow
import asyncio
import time
import random
import ubinascii

#hardware support
import ssd1306
import servo
import machine


#Initialisation
#define buttons , sensors and motors
#nav switches
switch_down = Pin(8, Pin.IN, Pin.PULL_UP)
switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
switch_up= Pin(10, Pin.IN, Pin.PULL_UP)

i2c = SoftI2C(scl = Pin(7), sda = Pin(6))

# Initiate display
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
oled.fill(0)
oled.show()
oled.text("boop-o-meter 300",0, 28, 1)
oled.show()
print("boop-o-meter 300")
print("Initialising!")

# Scan I2C devices
devices = i2c.scan()
for device in devices:
    print("I2C device found at address:", hex(device))

#servo
s = servo.Servo(Pin(2))

#unique name
ID = ubinascii.hexlify(machine.unique_id()).decode()

# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)  # Or network.AP_IF
sta.active(True)
#sta.disconnect()  # For ESP8266

# Initialize ESP-NOW
e = espnow.ESPNow()
e.active(True)

# Define the MAC addresses of the receiving ESP32s
peer = [b'\xff\xff\xff\xff\xff\xff']
peer_check = []

for p in peer:
    e.add_peer(p)
    
#Variables
hindex = 0
mindex = 0
clist = []
mainmenu = ["Scan", "Boop"]
boopn = 0
boopedn = 0
message_id = 0
last_press_time = 0

def pairing(timeout, buffer):
    stime = time.time()
    
    while time.time() - stime < timeout:
        #print("Sending Pairing Codeword: " + str(codes['0']))
        e.send(peer[0], codes['0'])
        for i in range(buffer):
            rsp = e.recv(random.randint(1, 10))
            if rsp:
                mac, data = rsp
                print(f"Received: {mac}, {data}")
                if data == bytearray(codes['1'] + str(sta.config('mac'))):
                    print(f"{mac} has me on their list")
                    if mac not in peer_check:
                        peer_check.append(mac)
                    try:
                        e.add_peer(mac)
                        peer.append(mac)
                        print(f"{mac} added to my list")
                    except OSError as error:
                        if error.args[0] == -12395:  # ESP_ERR_ESPNOW_EXIST
                            print(f"Peer {mac} already exists, skipping addition.")
                        else:
                            raise
                    e.send(mac, codes['2'] + str(mac))
                    break
                elif data == bytearray(codes['0']):
                    if mac not in peer:
                        e.add_peer(mac)
                        peer.append(mac)
                        print(f"{mac} added to my list")
                    e.send(mac, codes['1'] + str(mac))
                    stime = time.time()
                    while time.time() - stime < timeout + 0.1:
                        rsp = e.recv(random.randint(1, 10))
                        if rsp:
                            rmac, rdata = rsp
                            print(f"Received response: {rmac}, {rdata}")
                            if rdata == bytearray(codes['2'] + str(sta.config('mac'))) and rmac == mac:
                                print(f"{rmac} has me on their list")
                                if rmac not in peer_check:
                                    peer_check.append(rmac)
                                break
    
    #Summary of MACs in list
    print(f"{len(peer)} peers added:", peer)            
    print(f"Added by {len(peer_check)} peers:", peer_check) 
    #Check if I have received a confirmation from all the MACs I have added:
    added = [item for item in peer if item not in peer_check]
    if added:
            print("Peers I have added but that have not added me:", added)
    #Check if I have added all the MACs from which I have received a confirmation (There really should not be any possible case where this returns a result...)
    added2 = [item for item in peer_check if item not in peer]
    if added2:
        print("Peers who have added me but I have not added them:", added2)

async def receive(timeout):
    global boopedn
    stime = time.time()
    n = 0
    while True:
        rsp = e.recv(random.randint(1, 10))
        if rsp:
            mac, data = rsp
            if data == b'Boop':
                print(f"Received from {mac}: {data}")
                boopedn += 1
                show_list(clist, hindex)
                show_message(f"Boop!")
                asyncio.create_task(clear_message(message_id))
            elif data == bytearray(codes['0']):
                if mac not in peer:
                    e.add_peer(mac)
                    peer.append(mac)
                    print(f"{mac} added to my list")
                e.send(mac, codes['1'] + str(mac))
                stime = time.time()
                while time.time() - stime < timeout:
                    rsp = e.recv(random.randint(1, 10))
                    if rsp:
                        rmac, rdata = rsp
                        print(f"Received response: {rmac}, {rdata}")
                        if rdata == bytearray(codes['2'] + str(sta.config('mac'))) and rmac == mac:
                            print(f"{rmac} has me on their list")
                            peer_check.append(rmac)
                            break
        await asyncio.sleep(0.1)
        print(f"Loop {n} at {time.time_ns()//1000000}") #ms for accuracy
        n += 1
        
async def clear_message(current_id, delay=2.5):
    await asyncio.sleep(delay)
    if current_id == message_id:
        oled.fill_rect(0, 10, 128, 9, 0)
        oled.show()

async def main():
    asyncio.create_task(receive(0.6))
    
# Initialize the event loop
def loop():
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
    
# Menu management
def show_count():
    oled.fill_rect(0, 0, 128, 9, 0)
    if boopedn > 999 and boopn > 999:
        oled.text(f"Rx: uwu; Tx: wow", 0, 0, 1)
    elif boopn > 999:
        oled.text(f"Rx: {boopedn}; Tx: wow", 0, 0, 1)
    elif boopedn > 999:
        oled.text(f"Rx: uwu; Tx: {boopn}", 0, 0, 1)
    else:
        oled.text(f"Rx: {boopedn}; Tx: {boopn}", 0, 0, 1)
    oled.show()

def show_message(message):
    global message_id
    message_id += 1
    oled.fill_rect(0, 10, 128, 9, 0)
    oled.text(message, 0, 10, 1)
    oled.show()
    asyncio.create_task(clear_message(message_id))

def show_list(display_list, hindex):
    oled.fill_rect(0, 20, 128, 1, 1)
    oled.fill_rect(0, 21, 128, 44, 0)
    pos = 23
    show_count()
    max_displayed_items = 4
    
    if hindex >= 4:
        oled.text("^", 0, 23, 1)
    if hindex/4 < len(display_list)//4:
        rotated_caret = [0b00000000,
                         0b00011000,
                         0b00111100,
                         0b01100110,
                         0b00000000,
                         ]
        for row in range(len(rotated_caret)):
            for col in range(8):
                if rotated_caret[row] & (1 << col):
                    oled.pixel(0 + col, 57 + (3 - row), 1)
        #oled.text("v", 0, 53, 1)  # Arrow for items below
        
    start_index = max(0, (hindex//4)*4)    
    for index in range(start_index, min(len(display_list), start_index+4)):
        if index == hindex:
            oled.fill_rect(8, pos-1, 128, 9, 1)  # Highlight selected item
            oled.text(str(display_list[index]), 8, pos, 0)  # Display selected item
        else:
            oled.text(str(display_list[index]), 8, pos, 1)  # Display unselected item
        pos += 10  # Move position down for the next item
    oled.show()

def is_cooldown(cooldown):
    global last_press_time
    print(time.time_ns()//1000000-last_press_time)
    return (time.time_ns()//1000000 - last_press_time) < cooldown #prevent the scan function from being spammed

def update_last_press_time():
    global last_press_time
    last_press_time = time.time_ns()//1000000 #ms for accuracy
    print(last_press_time)

def up(pin):
    if is_cooldown(100):
        return
    update_last_press_time()
    global hindex, clist
    hindex = (hindex - 1) % len(clist)  # Wrap around
    show_list(clist, hindex)

def down(pin):
    if is_cooldown(100):
        return
    update_last_press_time()
    global hindex, clist
    hindex = (hindex + 1) % len(clist)  # Wrap around
    show_list(clist, hindex)

def action(pin):
    if is_cooldown(100):
        return
    global hindex, clist, mindex, boopn
    if not (mindex == 0 and hindex == 0):
        update_last_press_time() 
    if mindex == 0:
        if hindex == 0:
            if is_cooldown(1100):
                return  #Prevent Scan from being spammed
            update_last_press_time()
            show_message(" Scanning...")
            pairing(1,32)
            show_message(f" {len(peer)} peers found!")
            asyncio.create_task(clear_message(message_id))
        elif hindex == 1:
            clist = peer[:] + ["Back"]
            mindex = 1
            hindex = 0
            show_list(clist, hindex)
    elif mindex == 1:
        if hindex == len(clist) - 1:
            print("Going Back")
            clist = mainmenu[:]
            mindex = 0
            hindex = 0
            show_list(clist, hindex)
        else:
            selected_peer = clist[hindex]
            print(f" Booping: {selected_peer}")
            e.send(selected_peer, "Boop")
            boopn += 1
            show_list(clist, hindex)
            show_message(f"Booping {selected_peer}!")
            asyncio.create_task(clear_message(message_id))

# Main code
time.sleep(3)
#Initialisation
print("Finding peers...")
pairing(1, 32)

# Set up interrupt handlers for button presses
switch_up.irq(trigger=Pin.IRQ_FALLING, handler=down)
switch_down.irq(trigger=Pin.IRQ_FALLING, handler=up)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=action)

clist = mainmenu
show_list(clist, hindex)

loop()