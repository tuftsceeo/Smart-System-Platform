from networking import Networking
import time

#Initialise
networking = Networking()

#Example code
recipient_mac = b'\xff\xff\xff\xff\xff\xff'
message =  b'Boop'
#print own mac
print(networking.mac())

#Ping, calculates the time until you receive a response from the peer
networking.aen.ping(recipient_mac)

#Echo, sends a message that will be repeated back by the recipient
networking.aen.echo(recipient_mac, message)

#Message, sends the specified message to the recipient, supported formats are bytearrays, bytes, int, float, strings, bool, lists and dicts, max 242 bytes
networking.aen.message(recipient_mac, message)

#Check if there are any messages in the message buffer
print(networking.aen.check_messages())

#Get Last Received Message
print(networking.aen.return_message())

#Get All Recieved Messages
messages = networking.aen.return_messages()
for mac, message, rtime in messages:
    print(mac, message, rtime)

while True:
    print("Mark")
    time.sleep(5)
    
    
#Outputs
    
#Set up an interrupt which runs a function as soon as possible after receiving a message
def receive():
    for mac, message, rtime in messages:
        print(mac, message, rtime)

self.aen.irq(receive)#interrupt handler

#OLED
#import ssd1306
#oled = ssd1306.SSD1306_I2C(128, 64, i2c)
#oled.fill(0)
#oled.show()
#oled.text("boop-o-meter 200",0, 28, 1)

#LED
#from variableLED import VariableLED
#from machine import Pin
#pin_clk = Pin(7, Pin.OUT)
#pin_data = Pin(6, Pin.OUT)
#variableLED = VariableLED(pin_clk, pin_data, 1)
#variableLED.reset()

#variableLED[0] = (255,255,255)
#variableLED.write()

#variableLED.fill((255,255,255))

#Buttons
#from machine import Pin
#switch_down = Pin(8, Pin.IN, Pin.PULL_UP)
#switch_select = Pin(9, Pin.IN, Pin.PULL_UP)
#switch_up= Pin(10, Pin.IN, Pin.PULL_UP)

#switch_up.irq(trigger=Pin.IRQ_FALLING, handler=action_function)
#switch_down.irq(trigger=Pin.IRQ_FALLING, handler=action_function)
#switch_select.irq(trigger=Pin.IRQ_FALLING, handler=action_function)

#def action_function():
    #Do something here when a button is pressend

#servo
#import servo
#s = servo.Servo(Pin(2))

#I2C
#from machine import SoftI2C, PWM, ADC
#i2c = SoftI2C(scl = Pin(7), sda = Pin(6))
#devices = i2c.scan()
#for device in devices:
#    print("I2C device found at address:", hex(device))
