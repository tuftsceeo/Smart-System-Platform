#LED
from variableLED import VariableLED
from machine import Pin
pin_clk = Pin(7, Pin.OUT)
pin_data = Pin(6, Pin.OUT)
variableLED = VariableLED(pin_clk, pin_data, 1)
variableLED.reset()

variableLED[0] = (255,255,255)
variableLED.write()
