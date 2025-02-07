from machine import Pin, SoftI2C, PWM, ADC
import machine
from config import config
import random

import gc

gc.collect()

import network

print("Running boot.py")

# just to be safe
sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
sta.active(True)
ap.active(True)
sta.active(False)
ap.active(False)

from ssp_networking import SSP_Networking

# Network
infmsg = True
dbgmsg = False
errmsg = True
configuration = config["configuration"]

networking = SSP_Networking(infmsg, dbgmsg, errmsg)

peer_mac = b'\xff\xff\xff\xff\xff\xff'

import time
global timer

if config["sta_channel"]:
    networking.networking._staif.config(channel=config["sta_channel"])
if config["ap_channel"]:
    networking.networking._apif.config(channel=config["ap_channel"])

print(
    "{:.3f} Name: {}, ID: {}, Configuration: {}, Sta mac: {}, Sta channel: {}, Ap mac: {}, Ap channel: {}, Version: {}".format(
        (time.ticks_ms() - networking.inittime) / 1000,
        networking.config["name"],
        networking.config["id"],
        networking.config["configuration"],
        networking.config["sta_mac"],
        networking.config["sta_channel"],
        networking.config["ap_mac"],
        networking.config["ap_channel"],
        networking.config["version"]
    ))

def deinit():
    networking.cleanup()
    try:
        timer.deinit()
    except Exception as e:
        print(e)
    # machine.reset()


print("Hello")

from config import hive_config

if hive_config["hive"]:
    print("hive-motor v4.2")
    print("Initialising!")

    try:
        from splat import Splat

        s = Splat('1')


        def get_sensor_data(timer):
            # print(f"getting data (timer)")
            if not hive_config["hive"]:
                timer.deinit()
            sensor_data = {}
            try:
                if hive_config["recipients"]:
                    sensor_data["sw1"] = int(s.sw1.value())
                    sensor_data["sw2"] = int(s.sw2.value())
                    sensor_data["sw3"] = int(s.sw3.value())
                    sensor_data["sw4"] = int(s.sw4.value())
            except Exception as e:
                print(e)
            send_sensor_data(sensor_data)
            handle_data()


        def send_sensor_data(sensor_data):
            # print(f"sending data: {sensor_data}")
            # try:
            networking.send_data(hive_config["recipients"], sensor_data)
            # except Exception as e:
            #    print(e)
            datatime = time.ticks_ms()
            sensor_data["time_sent"] = datatime
            sensor_data["time_recv"] = datatime
            mac = networking.networking.sta.mac()
            if mac in networking.networking.aen.received_sensor_data:
                networking.networking.aen.received_sensor_data[b'prev_' + mac] = \
                networking.networking.aen.received_sensor_data[mac]
            networking.networking.aen.received_sensor_data[mac] = sensor_data


        last_press_time = 0


        def is_cooldown(cooldown):
            global last_press_time
            return (
                        time.time_ns() // 1000000 - last_press_time) < cooldown  # prevent the scan function from being spammed


        def send_button_data(pin):
            # print(f"getting data (button_irq)")
            if is_cooldown(1000):
                return
            global last_press_time
            last_press_time = time.time_ns() // 1000000
            sensor_data = {}
            try:
                if hive_config["recipients"]:
                    sensor_data["sw1"] = int(s.sw1.value())
                    sensor_data["sw2"] = int(s.sw2.value())
                    sensor_data["sw3"] = int(s.sw3.value())
                    sensor_data["sw4"] = int(s.sw4.value())
                    if pin == s.sw1:
                        sensor_data["sw1"] = 0
                    if pin == s.sw2:
                        sensor_data["sw2"] = 0
                    if pin == s.sw3:
                        sensor_data["sw3"] = 0
                    if pin == s.sw4:
                        sensor_data["sw4"] = 0
            except Exception as e:
                print(e)
            send_sensor_data(sensor_data)


        from config import sensor_dict


        def handle_data():
            recv_sensor_data = networking.return_data()
            # print(f"Received sensor data: {recv_sensor_data}")
            # do some logic here! servo, screen, lights etc.
            try:
                receive_list = hive_config["sender_sensor_list"]
                output = 0
                for entry in receive_list:
                    output += recv_sensor_data[entry[0]][entry[1]] / (
                                sensor_dict[entry[1]][1] - sensor_dict[entry[1]][0])
                output = output / len(receive_list)
                output = int(output * 7 + 1)
                # print(f"Value: {output}")
                s.set_color(output)
            except Exception as e:
                print(e)


        s.sw1.irq(trigger=Pin.IRQ_RISING, handler=send_button_data)
        s.sw2.irq(trigger=Pin.IRQ_RISING, handler=send_button_data)
        s.sw3.irq(trigger=Pin.IRQ_RISING, handler=send_button_data)
        s.sw4.irq(trigger=Pin.IRQ_RISING, handler=send_button_data)

        if hive_config["refreshrate"] > 0:
            timer = machine.Timer(0)
            timer.init(period=hive_config["refreshrate"], mode=machine.Timer.PERIODIC, callback=get_sensor_data)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        timer.deinit()
        deinit()
print("Hello End")

