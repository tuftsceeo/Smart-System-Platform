import network
import espnow
import time
import asyncio

# Set up the network and ESP-NOW
staif = network.WLAN(network.STA_IF)
staif.active(True)
aen = espnow.ESPNow()
aen.active(True)

# Add the send to all MAC addresses to ESP-NOW (maximum of 20 peers can be added)
peer = b'\xff\xff\xff\xff\xff\xff'
try:
    aen.add_peer(peer)
except Exception as e:
    print(f"Error adding peer: {e}")

start = time.time_ns()
last_press_time = 0

dictionary = {}
sender = False

# Callback function that retrieves the last message from the message buffer
def irq_receive(aen):
    print("IRQ triggered")
    if aen.any():
        for mac, msg in aen:
            recv_time = time.time_ns()
            if mac is None:  # mac, msg will equal (None, None) on timeout
                break
            if msg:
                print(f'MAC: {mac}, message: {msg}')
                try:  # This only works in a non-message saturated environment
                    i = int.from_bytes(msg, 'big')
                    if i <= 100:
                        dictionary[i] = {"Received": True, "recv_time": recv_time, "rssi": aen.peers_table[mac]}
                        print(f"Received {i}")
                        if not sender:
                            try:
                                aen.add_peer(mac)
                            except Exception as e:
                                print(f"Error adding peer: {e}")
                            aen.send(mac, msg)
                            print(f"Echoed {i}")
                except Exception as e:
                    print(f"Error processing message: {e}")
            if not aen.any():  # This is necessary as the for loop gets stuck and does not exit properly.
                break

# IRQ Trigger which is called as soon as possible after a message is received
aen.irq(irq_receive)

async def send():
    global aen, peer, dictionary
    print("Sending messages")
    for i in range(1, 101):
        dictionary[i] = {"Received": False, "send_time": time.time_ns()}
        aen.send(peer, i.to_bytes(4, 'big'))
        print(f"Sent {i}")
        await asyncio.sleep(0.1)  # Use asyncio.sleep for non-blocking sleep

async def save():
    global dictionary
    try:
        with open('log.txt', 'a') as file:
            file.write(f"{time.time()}\n")
            file.write(f"{dictionary}\n")
            false_count = sum(1 for key in dictionary if dictionary[key]["Received"] == False)
            file.write(f"Packet Loss: {false_count/100}\n")
        print("Successfully wrote to log.txt")
    except IOError as e:
        print(f"Error writing to file: {e}")

# Run the send and save functions asynchronously
async def main():
    await send()
    await asyncio.sleep(10)  # Wait for some time before saving
    await save()

# Entry point to run the main function
if __name__ == "__main__":
    asyncio.run(main())
