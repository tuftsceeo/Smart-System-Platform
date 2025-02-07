from machine import Pin, SoftI2C, PWM, ADC
import machine
from config import config

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
if configuration == "AM1":
    infmsg = True

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
    machine.reset()


print("Hello")

from config import hive_config

if hive_config["hive"]:
    try:
        import ssd1306

        i2c = SoftI2C(scl=Pin(7), sda=Pin(6))
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)
        oled.fill(0)
        oled.show()
        oled.text("hive-motor v4.2", 0, 28, 1)
        oled.show()
        print("hive-motor v4.2")
        print("Initialising!")

        import sensors

        sens = sensors.SENSORS()

        # buttons
        switch_down = Pin(8, Pin.IN)
        switch_select = Pin(9, Pin.IN)
        switch_up = Pin(10, Pin.IN)


        def get_sensor_data(timer):
            # print(f"getting data (timer)")
            if not hive_config["hive"]:
                timer.deinit()
            sensor_data = {}
            try:
                if hive_config["recipients"]:
                    point = sens.readpoint()
                    sensor_data["sensor"] = point[0]
                    sensor_data["potentiometer"] = point[1]
                    sensor_data["select"] = int(switch_select.value())
                    sensor_data["up"] = int(switch_up.value())
                    sensor_data["down"] = int(switch_down.value())
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
                    point = sens.readpoint()
                    sensor_data["sensor"] = point[0]
                    sensor_data["potentiometer"] = point[1]
                    if pin == switch_down:
                        sensor_data["down"] = 1
                    else:
                        sensor_data["down"] = 0

                    if pin == switch_down:
                        sensor_data["select"] = 1
                    else:
                        sensor_data["select"] = 0

                    if pin == switch_down:
                        sensor_data["up"] = 1
                    else:
                        sensor_data["up"] = 0
            except Exception as e:
                print(e)
            send_sensor_data(sensor_data)


        import servo

        s = servo.Servo(Pin(2))
        from config import sensor_dict


        def handle_data():
            recv_sensor_data = networking.return_data()
            print(f"Received sensor data: {recv_sensor_data}")
            # do some logic here! servo, screen, lights etc.
            if hive_config["mode"] == "logic":
                try:
                    receive_list = hive_config["sender_sensor_list"]
                    output = 0
                    for entry in receive_list:
                        output += recv_sensor_data[entry[0]][entry[1]] / (
                                    sensor_dict[entry[1]][1] - sensor_dict[entry[1]][0])
                    output = output / len(receive_list)
                    output = bool(int(output))
                    # print(f"Value: {output}")
                    oled.fill(0)
                    oled.show()
                    oled.text("hive mode", 0, 28, 1)
                    oled.text(f"{output}", 0, 42, 1)
                    oled.show()
                except Exception as e:
                    print(e)
            elif hive_config["mode"] == "continuous":
                try:
                    receive_list = hive_config["sender_sensor_list"]
                    output = 0
                    for entry in receive_list:
                        output += recv_sensor_data[entry[0]][entry[1]] / (
                                    sensor_dict[entry[1]][1] - sensor_dict[entry[1]][0])
                    output = output / len(receive_list)
                    output = int(output * 180)
                    # print(f"Value: {output}")
                    s.write_angle(output)
                except Exception as e:
                    print(e)


        switch_down.irq(trigger=Pin.IRQ_FALLING, handler=send_button_data)
        switch_select.irq(trigger=Pin.IRQ_FALLING, handler=send_button_data)
        switch_up.irq(trigger=Pin.IRQ_FALLING, handler=send_button_data)

        if hive_config["refreshrate"] > 0:
            timer = machine.Timer(0)
            timer.init(period=hive_config["refreshrate"], mode=machine.Timer.PERIODIC, callback=get_sensor_data)

        oled.fill(0)
        oled.show()
        oled.text("hive mode", 0, 28, 1)
        oled.show()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        timer.deinit()
        deinit()
print("Hello End")

try:
    with open("sm3.py") as f:
        code = f.read()
    exec(code)
except Exception as e:
    print(f"Error running sm3.py: {e}")