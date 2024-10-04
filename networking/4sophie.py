from networking import Networking
import time
from machine import Pin, SoftI2C, PWM, ADC
import ssd1306

# Initiate display
i2c = SoftI2C(scl = Pin(7), sda = Pin(6))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
oled.fill(0)
oled.show()
oled.text("boop-o-meter 400",0, 28, 1)
oled.show()
print("boop-o-meter 400")
print("Initialising!")

#Initialise network
networking = Networking(True, False) #First bool is for network info messages, second for network debug messages
broadcast_mac = b'\xff\xff\xff\xff\xff\xff'
networking.aen.add_peer(broadcast_mac, "All")
networking.name = "MyName"#Set your own device name (this will overwrite the default name gotten from the config.py)

#Variables
hindex = 0
last_press_time = time.ticks_ms()
display_list = []
keyname_dict = {}

def show_list():
    oled.fill_rect(0, 20, 128, 1, 1)
    oled.fill_rect(0, 21, 128, 44, 0)
    pos = 23
    max_displayed_items = 4
    
    key_list = list(networking.aen.peers().keys())
    name_list = [inner_dict['name'] for inner_dict in networking.aen.peers().values()]
    # Replace None values in name_list with corresponding key_list item
    global display_list, keyname_dict
    display_list = [name if name is not None else key_list[i] for i, name in enumerate(name_list)]
    for i in range(len(display_list)):
        keyname_dict[display_list[i]] = key_list[i]
    
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
    print(f"Cooldown: {time.ticks_ms()-last_press_time}")
    return (time.ticks_ms() - last_press_time) < cooldown #prevent the scan function from being spammed

def up(pin):
    if is_cooldown(100):
        return
    global last_press_time, hindex, display_list
    last_press_time = time.ticks_ms()
    hindex = (hindex - 1) % len(display_list)  # Wrap around
    show_list()

def down(pin):
    if is_cooldown(100):
        return
    global last_press_time, hindex, display_list
    last_press_time = time.ticks_ms()
    hindex = (hindex + 1) % len(display_list)  # Wrap around
    show_list()

#Send function
def send(pin):
    global last_press_time
    if(time.ticks_ms()-last_press_time>500):
        last_press_time = time.ticks_ms()
        message = "Hello!"
        networking.aen.send(keyname_dict[display_list[hindex]], message)
        
#Buttons
switch_down = Pin(8, Pin.IN, Pin.PULL_UP)
switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
switch_up= Pin(10, Pin.IN, Pin.PULL_UP)
# Set up interrupt handlers for button presses
switch_up.irq(trigger=Pin.IRQ_FALLING, handler=down)
switch_down.irq(trigger=Pin.IRQ_FALLING, handler=up)
switch_select.irq(trigger=Pin.IRQ_FALLING, handler=send)

#Receive function that displays any received message
def receive():
    for mac, message, rtime in networking.aen.return_messages(): #You can directly iterate over the function
        print(mac, message, rtime)

#Interrupt handler that calls the receive function once a message has been received
networking.aen.irq(receive)

#Sends out a ping every 5 seconds so that other devices know it is around
while True:
    networking.aen.ping(broadcast_mac)
    show_list()
    time.sleep(5)

