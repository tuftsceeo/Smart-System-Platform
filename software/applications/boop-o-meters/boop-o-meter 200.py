from machine import Pin, SoftI2C, PWM, ADC


#custom libraries
from networking import Networking
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
oled.text("boop-o-meter 200",0, 28, 1)
oled.show()
print("boop-o-meter 200")
print("Initialising!")

# Scan I2C devices
devices = i2c.scan()
for device in devices:
    print("I2C device found at address:", hex(device))

#servo
s = servo.Servo(Pin(2))

#unique name
ID = ubinascii.hexlify(machine.unique_id()).decode()

#Variables
hindex = 0
mindex = 0
clist = []
mainmenu = ["Scan", "Boop"]
boopn = 0
boopedn = 0
message_id = 0
last_press_time = 0
won = False

#Network
networking = Networking()
peer_mac = b'\xff\xff\xff\xff\xff\xff'
networking.aen.add_peer(peer_mac)
#networking.aen.send(peer_mac, b'Boop')
message = b'Boop'
# networking.aen.send(peer_mac, message)
networking.aen.ping(peer_mac)
#networking.aen.remove_peer(peer_mac)

def ping():
    networking.aen.ping(peer_mac)
    print(f" RSSI Table at {time.ticks_ms()}: {networking.aen.rssi()}")

async def main():
    global boopedn
    #last_check_time = 0
    last_ping_time = 0
    while True:
        print(f"Loop at {time.time()}")
        if time.time()-last_ping_time > 5:
            print("Ping")
            last_ping_time = time.time()
            ping()
        #networking.aen.receive_task()
        #if networking.aen.received_messages:
        #    for sender_mac, data, timestamp in networking.aen.received_messages:
        #        if timestamp > last_check_time:
        #            print(f"Processed received message from {sender_mac}: {data}")
        #    last_check_time = time.time_ns()  
        #print(f"boopedn: {boopedn}, boops: {networking.aen.boops}")
        if boopedn != networking.aen.boops:
            boopedn = networking.aen.boops
            show_message(f"Boop!")
            show_count()
        await asyncio.sleep(0.01)
        
# Initialize the event loop
def loops():
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
    
async def clear_message(current_id, delay=2.5):
    await asyncio.sleep(delay)
    if current_id == message_id:
        oled.fill_rect(0, 10, 128, 9, 0)
        oled.show()    

# Menu management
def show_count():
    limit = 99
    oled.fill_rect(0, 0, 128, 9, 0)
    if boopedn > limit and boopn > limit:
        oled.text(f"Rx: uwu; Tx: wow", 0, 0, 1)
        winning()
    elif boopn > limit:
        oled.text(f"Rx: {boopedn}; Tx: wow", 0, 0, 1)
    elif boopedn > limit:
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
    if hindex/4+1 < len(display_list)//4:
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
    print(f"Cooldown: {time.time_ns()//1000000-last_press_time}")
    return (time.time_ns()//1000000 - last_press_time) < cooldown #prevent the scan function from being spammed

def update_last_press_time():
    global last_press_time
    last_press_time = time.time_ns()//1000000 #ms for accuracy
    print(f"Last Press Time: {last_press_time}")

def up(pin):
    if is_cooldown(100) or won:
        return
    update_last_press_time()
    global hindex, clist
    hindex = (hindex - 1) % len(clist)  # Wrap around
    show_list(clist, hindex)

def down(pin):
    if is_cooldown(100) or won:
        return
    update_last_press_time()
    global hindex, clist
    hindex = (hindex + 1) % len(clist)  # Wrap around
    show_list(clist, hindex)

def action(pin):
    if is_cooldown(100) or won:
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
            show_message(f" {len(networking.aen.rssi())} peers found!")
            asyncio.create_task(clear_message(message_id))
            show_list(clist, hindex)
        elif hindex == 1:
            clist = list(networking.aen.peers().keys()) + ["Back"]
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
            networking.aen.echo(peer_mac, message)
            boopn += 1
            show_list(clist, hindex)
            show_message(f"Booping {selected_peer}!")
            asyncio.create_task(clear_message(message_id))

def winning():
    global won
    won = True
    while True:
        networking.aen.send(b'\xff\xff\xff\xff\xff\xff', "I win!", 0x01, 0x13)
        oled.fill(0)
        oled.show()
        oled.text("You win!",0, 28, 1)
        oled.show()
        time.sleep(5)

# Main code
time.sleep(3)
#Initialisation

# Set up interrupt handlers for button presses
switch_up.irq(trigger=Pin.IRQ_FALLING, handler=down)
switch_down.irq(trigger=Pin.IRQ_FALLING, handler=up)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=action)

clist = mainmenu
show_list(clist, hindex)

loops()



