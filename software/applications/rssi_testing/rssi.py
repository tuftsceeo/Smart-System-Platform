import network
import espnow
import time

#Set up the network and espnow
staif = network.WLAN(network.STA_IF)
staif.active(True)
aen = espnow.ESPNow()
aen.active(True)
#add the send to all mac address to esp now (maximum of 20 peers can be added)
peer = b'\xff\xff\xff\xff\xff\xff'
aen.add_peer(peer)

start = time.ticks_ms()

durations = {}

#callback function that retrieves the last message from the message buffer
def irq_receive(aen):
    tpl = aen.irecv() #returns a tuple of mac and message
    mac, msg = tpl
    try: #This only works in a non message saturated environment as I'm only ever retrieving the last received message
        numb = int.from_bytes(msg, 'big')
        dur = time.ticks_ms()-numb
        tim = f"{(time.ticks_ms() - start) / 1000:.3f}"
        
        print(f"At {(tim)} from: {mac}: {aen.peers_table[mac]}") #prints the time from since the message was originally sent until the echo has been received back
        durations[tim] = dur
    except Exception as e:
        print(f"Error: {e}")
        
aen.irq(irq_receive)#IRQ Trigger which is called as soon as as possible after a message is received

while True and time.ticks_ms()-start < 10000:
    num = time.ticks_ms()
    aen.send(peer, num.to_bytes(4, 'big'))
    time.sleep(1)
    
print(durations)
