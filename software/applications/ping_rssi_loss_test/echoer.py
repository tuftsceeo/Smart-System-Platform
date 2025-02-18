import network
import espnow
import time
import asyncio
import math
import gc

gc.collect()
from machine import Pin, SoftI2C, PWM, ADC
import machine

# Set up the network and ESP-NOW
staif = network.WLAN(network.STA_IF)
staif.active(True)
aen = espnow.ESPNow()
aen.active(True)

print(time.ticks_ms())
print(time.time_ns())
last_press_time = 0

s = Pin(9, Pin.IN)

# Add the send to all MAC addresses to ESP-NOW (maximum of 20 peers can be added)
all = b'\xff\xff\xff\xff\xff\xff'
try:
    macinpeers = False
    peers = aen.get_peers()
    for peer in peers:
        if peer[0] == all:
            macinpeers = True
            break
    if not macinpeers:
        aen.add_peer(all)
except Exception as e:
    print(f"Error adding peer: {e}")

start = time.ticks_ms()
last_press_time = 0

dictionary = {}
sender = True


# Callback function that retrieves the last message from the message buffer
def irq_receive(aen):
    print("IRQ triggered")
    if aen.any():
        for mac, msg in aen:
            recv_time_abs = time.time_ns()
            recv_time = time.ticks_ms()
            if mac is None:  # mac, msg will equal (None, None) on timeout
                break
            if msg:
                print(f'MAC: {mac}, message: {msg}')
                try:  # This only works in a non-message saturated environment
                    i = int.from_bytes(msg, 'big')
                    if i <= 100:
                        if not sender:
                            dictionary[i] = {}
                        dictionary[i]["received"] = True
                        dictionary[i]["abs_recv_time"] = recv_time_abs
                        dictionary[i]["recv_time"] = recv_time
                        dictionary[i]["rssi"] = aen.peers_table[mac][0]
                        dictionary[i]["rssi_time"] = aen.peers_table[mac][1]
                        if sender:
                            dictionary[i]["ping"] = recv_time - dictionary[i]["send_time"]
                        print(f"Received {i}")
                        if not sender:
                            try:
                                macinpeers = False
                                peers = aen.get_peers()
                                for peer in peers:
                                    if peer[0] == mac:
                                        macinpeers = True
                                        break
                                if not macinpeers:
                                    aen.add_peer(mac)
                            except Exception as e:
                                print(f"Error adding peer: {e}")
                            dictionary[i]["abs_send_time"] = time.time_ns()
                            aen.send(mac, msg)
                            print(f"Echoed {i}")
                except Exception as e:
                    print(f"Error processing message: {e}")
            if not aen.any():  # This is necessary as the for loop gets stuck and does not exit properly.
                break


# IRQ Trigger which is called as soon as possible after a message is received
aen.irq(irq_receive)


async def send():
    global aen, all, dictionary
    print("Sending messages")
    for i in range(1, 101):
        dictionary[i] = {"received": False, "send_time": time.ticks_ms(), "abs_send_time": time.time_ns()}
        aen.send(all, i.to_bytes(4, 'big'))
        print(f"Sent {i}")
        await asyncio.sleep(0.1)  # Use asyncio.sleep for non-blocking sleep


def calculate_stats(values):
    if values == []:
        return {}
    values = [x for x in values if x != 'NA']
    n = len(values)
    mean = sum(values) / n
    sorted_values = sorted(values)
    median = sorted_values[n // 2] if n % 2 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    max_val = max(values)
    min_val = min(values)
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = math.sqrt(variance)
    return {
        'mean': round(mean, 2),
        'median': median,
        'max': max_val,
        'min': min_val,
        'std_dev': round(std_dev, 2)
    }


async def save():
    global dictionary
    # print(dictionary)
    try:
        time_ticks = time.ticks_ms()
        rssi_values = ['NA' if i not in dictionary or 'rssi' not in dictionary[i] else dictionary[i]['rssi'] for i in
                       range(1, 101)]
        abs_recv_time_values = [
            'NA' if i not in dictionary or 'abs_recv_time' not in dictionary[i] else dictionary[i]['abs_recv_time'] for
            i in range(1, 101)]
        abs_send_time_values = [
            'NA' if i not in dictionary or 'abs_send_time' not in dictionary[i] else dictionary[i]['abs_send_time'] for
            i in range(1, 101)]
        if sender:
            ping_values = ['NA' if i not in dictionary or 'ping' not in dictionary[i] else dictionary[i]['ping'] for i
                           in range(1, 101)]
            ping_stats = calculate_stats(ping_values)
            print(ping_stats)
            false_count = sum(1 for key in dictionary if dictionary[key]["received"] == False)
        else:
            false_count = 100 - len(dictionary)
        print({false_count})
        rssi_stats = calculate_stats(rssi_values)
        print(rssi_stats)

    except Exception as e:
        print(f"Error calculating: {e}")
    try:
        with open(f'rssi_ping_data_{time_ticks}.txt', 'a') as file:
            file.write(f"Packet Loss: {false_count} %\n")
            file.write(f"RSSI: {rssi_stats}\n")
            if sender:
                file.write(f"Ping: {ping_stats}\n")
    except Exception as e:
        print(f"Error writing to file: {e}")
    try:
        with open(f'raw_rssi_ping_data_{time_ticks}.csv', 'a') as file:
            file.write(f"{dictionary}\n")
    except Exception as e:
        print(f"Error writing dict to file: {e}")
    try:
        with open(f'rssi_ping_data_{time_ticks}.csv', 'a') as file:
            if sender:
                file.write("RSSI,Ping,send_time_sender,recv_time_sender\n")
            else:
                file.write("RSSI,Ping,send_time_echoer,recv_time_echoer\n")
            for i in range(0, 100):
                rssi = rssi_values[i]
                if sender:
                    ping = ping_values[i]
                else:
                    ping = 'NA'
                abs_send_time = abs_send_time_values[i]
                abs_recv_time = abs_recv_time_values[i]
                file.write(f"{rssi},{ping},{abs_send_time},{abs_recv_time}\n")
    except Exception as e:
        print(f"Error writing to file: {e}")
    dictionary = {}
    print(f"Successfully wrote files at {time_ticks}")


def is_cooldown(cooldown):
    global last_press_time
    # print(time.time_ns()//1000000-last_press_time)
    return (time.time_ns() // 1000000 - last_press_time) < cooldown  # prevent the scan function from being spammed


def action(pin):
    print("pressed")
    if is_cooldown(1000):
        return
    global last_press_time
    last_press_time = time.time_ns() // 1000000
    asyncio.run(save())


s.irq(trigger=Pin.IRQ_FALLING, handler=action)


# Run the send and save functions asynchronously
async def main():
    global dictionary
    dictionary = {}
    await send()
    # await asyncio.sleep(10)  # Wait for some time before saving
    # await save()

# Entry point to run the main function
# if __name__ == "__main__":
#    asyncio.run(main())
# asyncio.run(save())

