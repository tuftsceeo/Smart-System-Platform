import network
import machine
from config import mysecrets#HERE
import time
import ubinascii
import urequests
import espnow
import gc
import asyncio
import struct
import json
import random

# Unique identifier for the device
id = ubinascii.hexlify(machine.unique_id()).decode()
boottime = time.time_ns()

class Networking:
    
    def __init__(self, verbose=False):
        self.staif = network.WLAN(network.STA_IF)
        self.apif = network.WLAN(network.AP_IF)
        self.staif.active(True)
        self.ap = self.Ap(self.apif)
        self.aen = self.Aen()
        self.sta = self.Sta(self.staif)
        self.verbose = verbose
        
    def vprint(self, message):
        if self.verbose:
            print(message)

    def set_channel(self, number):
        if number > 14 or number < 0:
            number = 0
        self.staif.config(channel=number)
        self.vprint(f"Channel set to {number}")
        #This will override the channel that was set as part of the add_peer function ???
    
    def channel(self):
        return self.staif.config('channel')

    def mac(self):
        return bytes(self.staif.config('mac'))
    
    def mac_decoded(self): 
        return ubinascii.hexlify(self.sta.config('mac'), ':').decode()
    
    def ip(self):
        return self.staif.ifconfig()
    
    class Sta:
        def __init__(self, sta_interface):
            self.sta = sta_interface

        def scan(self):
            scan_result = self.sta.scan()
            if self.verbose:
                for ap in scan_result:
                    print("SSID:%s BSSID:%s Channel:%d Strength:%d RSSI:%d Auth:%d " % (ap))
            return scan_result
    
        async def connect(self, ssid, key="", timeout=10):
            self.sta.connect(ssid, key)
            stime = time.time()
            while time.time() - stime < timeout:
                if self.sta.ifconfig()[0] != '0.0.0.0':
                    self.vprint("Connected to WiFi")
                    return True
                await asyncio.sleep(1)
            self.vprint("Failed to connect to WiFi")
            return False
        
        def get_joke(self):
            try:
                reply = urequests.get('https://v2.jokeapi.dev/joke/Programming')
                if reply.status_code == 200:
                    joke = reply.json()
                    return joke.get('setup', '') + '\n' + joke.get('delivery', joke.get('joke', ''))
            except Exception as e:
                print('Error fetching joke:', str(e))
            return None
    
    class Ap:
        def __init__(self, ap_interface):
            self.ap = ap_interface
        
        def set_ap(self, name, password="", max_clients=10):
            self.ap.active(True)
            self.ap.config(essid=name)
            if password:
                self.ap.config(authmode=network.AUTH_WPA_WPA2_PSK, password=password)
            self.ap.config(max_clients=max_clients)
            self.vprint(f"Access Point {name} set with max clients {max_clients}")
        
        def deactivate(self):
            self.ap.active(False)
            self.vprint("Access Point deactivated")

    class Aen:
        def __init__(self):
            self.aen = espnow.ESPNow()
            self.aen.active(True)
            self.peers = {}
            #self.received_messages = []
            self.saved_messages = []
            self.long_buffer = {}
            self.long_sent_buffer = {}
            self.running = True
            self.boops = 0
            
            self.aen.irq(self.irq_receive_task)#Processes the messages asap after receiving them
            #start_loop()#this would start the async loop
            self.vprint("ESP-NOW initialized and ready")

        def add_peer(self, peer_mac, channel=0, ifidx=0): #ifidx can be 0 or 1, sending data via network.STA_IF or network.AP_IF respectively
            if peer_mac not in self.peers:
                try:
                    self.peers[peer_mac] = {'channel': channel, 'ifidx': ifidx}
                    self.vprint(f"Peer {peer_mac} added with channel {channel} and ifidx {ifidx}")
                except OSError as e:
                    print(f"Error adding peer {peer_mac}: {e}")
            else:
                self.vprint(f"Peer {peer_mac} already exists")

        def remove_peer(self, peer_mac):
            if peer_mac in self.peers:
                try:
                    del self.peers[peer_mac]
                    self.vprint(f"Peer {peer_mac} removed")
                except OSError as e:
                    print(f"Error removing peer {peer_mac}: {e}")
                    
        def update_peer(self, peer_mac, new_channel=None, new_ifidx=None):
            for peer in self.peers:
                if peer[0] == peer_mac:
                    updated_peer = (
                        peer[0],
                        new_channel if new_channel is not None else peer[1],
                        new_ifidx if new_ifidx is not None else peer[2]
                    )
                    self.peers.remove(peer)
                    self.peers.add(updated_peer)
                    self.vprint(f"Peer {peer_mac} updated to channel {updated_peer[1]} and ifidx {updated_peer[2]}")
                return
            self.vprint(f"Peer {peer_mac} not found")

        def list_peers(self):
            return self.peers
        
        def get_buffer_peer_count(self):
            return peer_count() #This should always return 1 & 0 as peers are only added in a send command and then removed
        
        def get_buffer_peers(self):
            return self.aen.get_peers() #This should always return only the broadcast address (if any at all) as other MACs are continously removed after sending
        
        def get_rssi_table(self):
            return self.aen.peers_table
        
        def broadcast(self, msg, channel=None, ifidx=None):
            broadcast_mac = b'\xff\xff\xff\xff\xff\xff'
            try:
                if channel != None and ifidx != None:
                    self.aen.add_peer(broadcast_mac, channel=channel, ifidx=ifidx)
                elif broadcast_mac in self.peers:
                    self.aen.add_peer(broadcast_mac, channel=self.peers[broadcast_mac]['channel'], ifidx=self.peers[broadcast_mac]['ifidx'])
                else:
                    self.aen.add_peer(broadcast_mac, channel=0, ifidx=0)
            except Exception as e:
                print(f"Error adding {peer_mac} to buffer: {e}")
            try:
                self.aen.send(peer_mac, msg)
                self.vprint(f"Sent to {peer_mac}: {msg}")
            except Exception as e:
                print(f"Error sending to {peer_mac}: {e}")
            try:
                self.aen.del_peer(peer_mac)
            except Exception as e:
                self.vprint(f"Error removing {peer_mac} from buffer: {e}")
            
        def send_multiple(self, peers_mac, msg, channels=None, ifidxs=None):
            for peer_mac, channel, ifidxs in peers_mac, channels, ifidxs:
                try:
                    if channel != None and ifidx != None:
                        self.aen.add_peer(peer_mac, channel=channel, ifidx=ifidx)
                    elif peer_mac in self.peers:
                        self.aen.add_peer(peer_mac, channel=self.peers[peer_mac]['channel'], ifidx=self.peers[peer_mac]['ifidx'])
                    else:
                        self.aen.add_peer(peer_mac, channel=0, ifidx=0)
                except Exception as e:
                    print(f"Error adding {peer_mac} to buffer: {e}")
            try:    
                self.aen.send(None, msg)
                self.vprint(f"Sent to multiple: {msg}")
            except Exception as e:
                print(f"Error sending to all: {e}")
            for peer_mac in peers_mac:
                try:    
                    self.aen.del_peer(peer_mac)
                except Exception as e:
                    print(f"Error removing {peer_mac} from buffer: {e}")
                
        def send(self, peer_mac, msg, msg_type=0x02, subtype=0x22, channel=None, ifidx=None):
            messages = self.create_message(msg_type, subtype, msg, channel, ifidx)
            self.__send(peer_mac, messages, channel, ifidx)
                    
        def __send(self, peer_mac, message, channel=None, ifidx=None):
                message = bytes(message) #only necessary if create function returns bytearray which it doesn't, conversion already done in create_message
                try:
                    if channel != None and ifidx != None:
                        self.aen.add_peer(peer_mac, channel=channel, ifidx=ifidx)
                    elif peer_mac in self.peers:
                        self.aen.add_peer(peer_mac, channel=self.peers[peer_mac]['channel'], ifidx=self.peers[peer_mac]['ifidx'])
                    else:
                        self.aen.add_peer(peer_mac, channel=0, ifidx=0)
                except Exception as e:
                    print(f"Error adding {peer_mac} to buffer: {e}")
                try:
                    for message in messages:
                        self.aen.send(peer_mac, message)
                    print(f"Sent to {peer_mac}: {message}")
                except Exception as e:
                    print(f"Error sending to {peer_mac}: {e}")
                try:    
                    self.aen.del_peer(peer_mac)
                except Exception as e:
                    print(f"Error removing {peer_mac} from buffer: {e}")

        def receive_task(self): #Processes all the messages in the buffer
#             while self.running:
                #msg = self.aen.recv(random.randint(1, 10))
                #msg = self.aen.irecv()#BEWARE!!!!!!!!!!!!!!
                #    if msg:
                #        rtimestamp = time.ticks_ms()
                #        sender_mac, data = msg
                #        if sender_mac != None and data != None:
                #            self.received_messages.append((sender_mac, data, rtimestamp))
                #            print(f"Received from {sender_mac}: {data}")
                #            self.process_message(sender_mac, data, rtimestamp)
                if self.aen.any(): #this is necessary as the for loop gets stuck and does not exit properly.
                    for sender_mac, data in self.aen:
                        if verbose:
                            print(f"Received {sender_mac, data}")
                        if sender_mac is None:   # mac, msg will equal (None, None) on timeout
                            break
                        if data:
                            rtimestamp = time.ticks_ms()
                            if sender_mac != None and data != None:
                                #self.received_messages.append((sender_mac, data, rtimestamp))#Messages will be saved here, this is only for debugging purposes
                                #print(f"Received from {sender_mac}: {data}")
                                self.process_message(sender_mac, data, rtimestamp)
                        if not self.aen.any():
                            break
                #await asyncio.sleep(0.1)
                
        def encode_payload(self, payload):
            if payload is None: #No payload type
                return b'\x00', b''
            elif isinstance(payload, bytearray): #bytearray
                return (b'\x01', bytes(payload))
            elif isinstance(payload, bytes): #bytes
                return (b'\x01', payload)
            elif isinstance(payload, bool): #bool
                return (b'\x02', (b'\x01' if payload else b'\x00'))
            elif isinstance(payload, int): #int
                return (b'\x03', struct.pack('>i', payload))
            elif isinstance(payload, float): #float
                return (b'\x04', struct.pack('>f', payload))
            elif isinstance(payload, str): #string
                return (b'\x05', payload.encode('utf-8'))
            elif isinstance(payload, dict) or isinstance(payload, list): #json dict or list
                json_payload = json.dumps(payload)
                return (b'\x06', json_payload.encode('utf-8'))
            else:
                raise ValueError("Unsupported payload type")
            
        def decode_payload(self, payload_type, payload_bytes):
            if payload_type == b'\x00': #None
                return None
            elif payload_type == b'\x01': #bytearray or bytes
                return bytes(payload_bytes)
            elif payload_type == b'\x02': #bool
                return payload_bytes[0:1] == b'\x01'
            elif payload_type == b'\x03': #int
                return struct.unpack('>i', payload_bytes)[0]
            elif payload_type == b'\x04': #float
                return struct.unpack('>f', payload_bytes)[0]
            elif payload_type == b'\x05': #string
                return payload_bytes.decode('utf-8')
            elif payload_type == b'\x06': #json dict or list
                return json.loads(payload_bytes.decode('utf-8'))  
            elif payload_type == b'\x07': #Long byte array
                return bytes(payload_bytes)
            else:
                print(f"Unsupported payload type: {payload_type} Message: {payload_bytes}")
                return None
        
        def create_message(self, msg_type, subtype, payload=None, channel=None, ifidx=None):
            payload_type, payload_bytes = self.encode_payload(payload)
            payload_chunks = []
            total_chunk_number = 0
            if len(payload_bytes) < 242:
                payload_chunks.append(payload_bytes)
            else:
                max_size = 239
                total_chunk_number = len(((payload_bytes)//max_size)+1)
                payload_type = b'\x07' #Long byte array
                if total_chunk_number > 256:
                    raise ValueError("More than 256 chunks, unsupported")
                for chunk_index in range(0, total_chunk_number):
                    chunk_bytes = payload_bytes[chunk_index*max_size:chunk_index*max_size + max_payload_size]
                    payload_chunks.append(bytes([chunk_index]) + bytes([total_chunk_number]) + payload_type + chunk_bytes)
            messages = []
            for payload_chunk in payload_chunks:
                total_length = 1 + 1 + 1 + 4 + 1 + len(payload_chunk) + 1
                timestamp = time.ticks_ms()
                identifier = 0x2a
                message = bytearray()
                message.append(identifier)
                message.append(msg_type)
                message.append(subtype)
                message.extend(timestamp.to_bytes(4, 'big'))
                message.extend(payload_type)
                message.extend(payload_chunk)
                checksum = sum(message) % 256
                message.append(checksum)
                messages.append(message)
            if total_chunk_number > 1:
                key = message[1:8]
                key.append(total_chunk_numberto_bytes(1, 'big'))
                self.long_sent_buffer[bytes(key)] = (messages, (channel,ifidx))
            return [bytes(message) for message in messages] #returns bytes
            #return messages #returns bytearray
            
        def process_message(self, sender_mac, message, rtimestamp):
            if message[0] != 0x2a:  # Uniqe Message Identifier Check
                self.vprint("Invalid message: Message ID Fail")
                return None
            if len(message) < 9:  # Min size
                self.vprint("Invalid message: too short")
                return None

            msg_type = bytes(message[1:2])
            subtype = bytes(message[2:3])
            stimestamp = int.from_bytes(message[3:7], 'big')
            payload_type = bytes(message[7:8])
            payload = message[8:-1]
            checksum = message[-1]
            self.vprint(f"{type(msg_type)}: {msg_type}, {type(subtype)}: {subtype}, {type(stimestamp)}: {stimestamp}, {type(payload_type)}: {payload_type},  {type(payload)}: {payload},  {type(checksum)}: {checksum}")
            
            #Checksum
            if checksum != sum(message[:-1]) % 256:
                self.vprint("Invalid message: checksum mismatch")
                return None
            
            if sender_mac not in self.peers:
                self.add_peer(sender_mac)
            
            if payload_type == b'0x07':
                self.vprint("Long message received, no logic to handle implemented just yet")
                part_n = int.from_bytes(payload[0:1])
                total_n = int.from_bytes(payload[1:2])
                payload_type = bytes(payload[2:3])
                payload = payload[3:]
                
                key = (msg_type, subtype, stimestamp, payload_type, total_n)
                if key in self.long_buffer:
                    if self.long_buffer[key][part_n] is None:
                        self.long_buffer[key][part_n] = payload
                        self.vprint("Long message received, no logic to handle implemented just yet")
                        if any(value is None for value in self.long_buffer[key]):
                            return
                else:
                    payloads = [None] * total_n
                    payloads[part_n] = payload
                    self.long_buffer[key] = payloads
                    if any(value is None for value in self.long_buffer[key]):
                        self.vprint("Long message: There are still parts of the message missing")
                        #create an async task to run in 3 seconds, it checks if the message is still in the buffer and requests the messages to be resent, it does this for a maximum of N times
                        #The message should be a bytearray with all the key elements, followed by the indexes of the missing messages
                        #value])
                        none_indexes = [index for index, value in enumerate(self.long_buffer[key]) if value is None]
                        message = []
                        message.append(msg_type)
                        message.append(subtype)
                        message.append(stimestamp.to_bytes(4, 'big'))
                        message.append(payload_type)
                        message.append(total_n.to_bytes(1, 'big'))
                        for none_index in none_indexes:
                            message.append(none_index.to_bytes(1, 'big'))
                        return

                    if any(value is None for value in self.long_buffer[key]):
                        
                        
        
                
                
                
                if 
                self.long_buffer.append(((), ( , payloads)))
              
            if msg_type == b'\x01':  # Command Message
                self.handle_cmd(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
            elif msg_type == b'\x02':  # Informational Message
                self.handle_inf(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
            elif msg_type == b'\x03':  # Acknowledgement Message
                self.handle_ack(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
            else:
                self.vprint(f"Unknown message type from {sender_mac}: {message}")

        def handle_cmd(self, sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
            if subtype == b'\x10': #Ping
                self.vprint(f"Ping command received from {sender_mac}")
                self.send(sender_mac, stimestamp, 0x03, 0x10)
            elif subtype == b'\x11': #Pair
                self.vprint(f"Pairing command received from {sender_mac}")
                # Insert pairing logic here
            elif subtype == b'\x12': #Change Mode to Firmware Update
                self.vprint(f"Update command received from {sender_mac}")
                # Insert update logic here
            elif subtype == b'\x13': #RSSI Boop
                self.boops = self.boops + 1
                self.vprint(f"Boop command received from {sender_mac}, Received total of {self.boops} boops!")
                #self.send(sender_mac, self.peers_table, 0x02, 0x20)
            elif subtype == b'\x14': #Reboot
                self.vprint(f"Reboot command received from {sender_mac}")
                machine.reset()
            elif subtype == b'\x15': #Echo
                self.vprint(f"Echo command received from {sender_mac}: {payload}")
                self.send(sender_mac, self.decode_payload(payload_type, payload), 0x03, 0x15)
            elif subtype == b'\x16': #Run file
                filename = self.decode_payload(payload_type, payload)
                self.vprint(f"Run command received from {sender_mac}: {filename}")    
                #try:    
                #    task = asyncio.create_task(run_script(filename))
                    #Needs
                    #async def execute_script(script_path):
                    # Load and execute the script
                    #with open(script_path) as f:
                    #    script_code = f.read()
                    #
                    #exec(script_code)  # This executes the script in the current namespace
                    #
                    # Alternatively, if you want to run this in a separate function scope
                    #exec(script_code, {'__name__': '__main__'})
                    #            except Exception as e:
                    #                print(f"Error running {filename}: {e}")
            elif subtype == b'\x17': #Resend lost long messages
                payload = self.decode_payload(payload_type, payload)
                self.vprint(f"Received resend long message command, checking buffer for lost message")
                key = payload[0:8]
                indexes_b = [8:]
                indexes = []
                for i in range(0, len(indexes_b)):
                    indexes.append(int.from_bytes(indexes_b[i], 'big'))
                if key in self.long_sent_buffer:
                    channel = self.long_sent_buffer[key][1][0]
                    ifidx = self.long_sent_buffer[key][1][1]
                    for index in indexes:
                        message.append(self.long_sent_buffer[key][0][index])
                    self.__send(sender_mac, messages, channel, ifidx)
                    #resend the message from the message buffer
                    self.vprint(f"Resent all requested messages")
                else:
                    self.vprint(f"Message not found in the buffer")

            else:
                self.vprint(f"Unknown command subtype from {sender_mac}: {subtype}")

        def handle_inf(self, sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
            if subtype == b'\x21': #Sensor Data
                self.vprint(f"Sensor data received from {sender_mac}: {payload}")
                # Process sensor data
            elif subtype == b'\x20': #RSSI
                self.vprint(f"RSSI data received from {sender_mac}: {payload}")
                # Process RSSI data
            elif subtype == b'\x22': #Other
                print(f"Message received from {sender_mac}: {payload}")
                self.vself.saved_messages.append((sender_mac, payload, rtimestamp))
            else:
                self.vprint(f"Unknown info subtype from {sender_mac}: {subtype}")
                
        def handle_ack(self, sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
            if subtype == b'\x10': #Pong
                self.vprint(f"Pong received from {sender_mac}, {rtimestamp-self.decode_payload(payload_type, payload)}")
            elif subtype == b'\x15': #Echo
                self.vprint(f"Echo received from {sender_mac}, {self.decode_payload(payload_type, payload)}")
            else:    
                self.vprint(f"Unknown ack subtype from {sender_mac}: {subtype}, Payload: {payload}")
            # Insert more acknowledgement logic here add message to acknowledgement buffer
                
        async def boop_task(self): #Remove
            while self.running:
                broadcast(b'Boop')
                await asyncio.sleep(1)
                
        def ping(self, mac):
            self.send(mac, "", 0x01, 0x10)
        
        def echo(self, mac, message):
            self.send(mac, message, 0x01, 0x15)
        
        def message(self, mac, message):
            self.send(mac, message, 0x02, 0x22)
            
        def check_messages(self):
            return len(self.saved_messages) > 0
        
        def return_message(self):
            if self.saved_messages:
                return self.saved_messages-pop()
            return None
        
        def return_messages(self):
            messages = self.saved_messages[:]
            self.saved_messages.clear()
            return messages

        def stop(self):
            self.running = False
            self.aen.active(False)
            self.vprint("ESP-NOW stopped")
            
        def resume(self):
            self.running = True
            self.aen.active(True)
            self.vprint("ESP-NOW resumed")
            
        async def start(self, sleep=0.1):
            while is_running:
                self.receive_task()
                await asyncio.sleep(sleep)
                
        async def start_loop(self, sleep=0.1):
            loop = asyncio.get_event_loop()
            loop.create_task(start(sleep))
            loop.run_forever()
            
        def irq_receive_task(self, espnow):
            self.vprint("IRQ")
            self.receive_task()
            return
            
#message structure (what kind of message types do I need?: Command which requires me to do something (ping, pair, change state(update, code, mesh mode, run a certain file), Informational Message (Sharing Sensor Data and RSSI Data)
#| Header (1 byte) | Type (1 byte) | Subtype (1 byte) | Timestamp(ms ticks) (4 bytes) | Payload type (1) | Payload (variable) | Checksum (1 byte) |
