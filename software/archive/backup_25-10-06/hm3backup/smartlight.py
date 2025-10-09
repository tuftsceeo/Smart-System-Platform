from machine import Pin, ADC
from neopixel import NeoPixel
import time
import micropython

class SmartLight:
    def __init__(self, neo_pin, resolution=700):
        self.np = NeoPixel(Pin(neo_pin, Pin.OUT), 12)
        self.resolution = resolution
        self.colors = self.build_rainbow(self.resolution)
        self.resolution = len(self.colors)-1   # get the actual number of colors, differs from desired due to rounding
        self.cycling_color = True     # if false, cycling brightness
        
        self.color = [255, 0, 0]
        self.brightness = 1000        # brightness values from 0 to 1000
        self.num_leds = 12
        self.LED = [255, 0, 0]     # led value which combines color and brightness
        
        
    def build_rainbow(self, resolution):
        rainbow = []
        num = int(255/(resolution/3))
        
        for i in range(0, 255, num):
            rainbow.append((255-i, i, 0))           
        for i in range(0, 255, num):
            rainbow.append((0, 255-i, i))           
        for i in range(0, 255, num):
            rainbow.append((i, 0, 255-i))
            
        return rainbow

    
    def write_LED(self, color, brightness, number):
        for i in range(3):
            self.LED[i] = int(color[i] * (brightness / 1000))      # set LED value to determined color and brightness
        LED = tuple(self.LED)
        for i in range(12):
            if (i<=number):
                self.np[i] = LED    # set each LED value
            else: self.np[i] = (0,0,0)
        self.np.write()
        
    def update(self):
        self.write_LED(self.color, self.brightness, self.num_leds)
        
    def write_color(self, color):
        self.color = self.colors[int((color * self.resolution)/1000)]
        self.write_LED(self.color, self.brightness, self.num_leds)
        
    def write_brightness(self, brightness):
        self.brightness = brightness
        self.write_LED(self.color, self.brightness, self.num_leds)
        
    def write_number(self, number):
        self.num_leds = int((number * 12)/1000)
        self.write_LED(self.color, self.brightness, self.num_leds)
    
    def get_resolution(self):
        '''returns length of colors array'''
        return self.resolution
    
    def get_parameter(self):
        self.parameter = self.parameters[self.param_num]
        return self.parameter
        
    def set_brightness(self, b):
        self.brightness = b
        
    def set_number(self, num):
        self.num_leds = int((num * 12)/1000)
        
    def set_color(self, color):
        self.color = self.colors[int((color * self.resolution)/1000)]
        
    def set_white(self):
        self.color = (255, 255, 255)
        self.num_leds = 12
        self.brightness = 1000