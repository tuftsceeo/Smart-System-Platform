import network
import espnow
import time

#setup
staif = network.WLAN(network.STA_IF)
staif.active(True)
aen = espnow.ESPNow()
aen.active(True)

peers = []

#waits for a message to be received and then sends the same message back
while True:
    tpl = aen.irecv()
    mac, msg = tpl
    print(f"Echoing {msg} to {mac}")
    if mac != None and mac not in peers: #check if the peer has already been added
        peers.append(mac)
        aen.add_peer(mac)
    aen.send(mac, msg)