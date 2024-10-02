import network
import machine
from config import mysecrets, configname
import time
import ubinascii
import urequests
import espnow
import gc
import asyncio
import struct
import json
import random


boottime = time.time_ns()

class Networking:       
    def __init__(self):
        self.master = self
        self.infmsg = False
        self.dbgmsg = False
        self.admin = False
        self.id = ubinascii.hexlify(machine.unique_id()).decode()
        self.name = configname
        if self.name == "":
            self.name = str(self.id)
        self.staif = network.WLAN(network.STA_IF)
        self.apif = network.WLAN(network.AP_IF)
        self.staif.active(True)#Should these be here????
        self.apif.active(True)#Should these be here????
        self.ap = self.Ap(self, self.apif)
        self.aen = self.Aen(self)
        self.sta = self.Sta(self, self.staif)
        
    #Should the following be in sta ap respectively?
    def iprint(self, message):
        if self.infmsg:
            print(message)
            
    def dprint(self, message):
        if self.dbgmsg:
            print(message)

    def set_channel(self, number):
        self.master.dprint("sta.set_channel")
        if number > 14 or number < 0:
            number = 0
        self.staif.config(channel=number)
        self.vprint(f"Channel set to {number}")
        #This will override the channel that was set as part of the add_peer function ???
    
    def channel(self):
        self.master.dprint("sta.channel")
        return self.staif.config('channel')

    def mac(self):
        self.master.dprint("mac")
        return bytes(self.staif.config('mac'))
    
    def mac_decoded(self):#Necessary?
        self.master.dprint("mac_Decode")
        return ubinascii.hexlify(self.sta.config('mac'), ':').decode()
    
    def ip(self):
        self.master.dprint("ip")
        return self.staif.ifconfig()
    #Should the above be in sta ap respectively?
    
    class Sta:
        def __init__(self, master, sta_interface):
            self.master = master
            self.iprint = self.master.iprint
            self.master.dprint = self.master.dprint
            self.sta = sta_interface
            
        def scan(self):
            self.master.dprint("sta.scan")
            scan_result = self.sta.scan()
            if self.infmsg:
                for ap in scan_result:
                    self.iprint("SSID:%s BSSID:%s Channel:%d Strength:%d RSSI:%d Auth:%d " % (ap))
            return scan_result
    
        def connect(self, ssid, key="", timeout=10):
            self.master.dprint("sta.connect")
            self.sta.connect(ssid, key)
            stime = time.time()
            #self.sta.status() returns the current wlan status, update below functions with it
            while time.time() - stime < timeout:
                if self.sta.ifconfig()[0] != '0.0.0.0':
                    self.iprint("Connected to WiFi")
                    return
                time.sleep(1)
            self.iprint(f"Failed to connect to WiFi: {self.sta.status()}")
        
        def disconnect(self):
            self.master.dprint("sta.disconnect")
            self.sta.disconnect()
        
        def get_joke(self):
            self.master.dprint("sta.get_joke")
            try:
                reply = urequests.get('https://v2.jokeapi.dev/joke/Programming')
                if reply.status_code == 200:
                    joke = reply.json()
                    return joke.get('setup', '') + '\n' + joke.get('delivery', joke.get('joke', ''))
            except Exception as e:
                print('Error fetching joke:', str(e))
            return None
    
    class Ap:
        def __init__(self, master, ap_interface):
            self.master = master
            self.iprint = self.master.iprint
            self.master.dprint = self.master.dprint
            self.ap = ap_interface
        
        def set_ap(self, name="", password="", max_clients=10):
            self.master.dprint("ap.setap")
            if name == "":
                name = self.name
            self.ap.active(True)
            self.ap.config(essid=name)
            if password:
                self.ap.config(authmode=network.AUTH_WPA_WPA2_PSK, password=password)
            self.ap.config(max_clients=max_clients)
            self.iprint(f"Access Point {name} set with max clients {max_clients}")
        
        def deactivate(self):
            self.master.dprint("ap.deactivate")
            self.ap.active(False)
            self.iprint("Access Point deactivated")

    class Aen:
        def __init__(self, master):
            self.master = master
            self.iprint = self.master.iprint
            self.master.dprint = self.master.dprint
            self.aen = espnow.ESPNow()
            self.aen.active(True)
            self.peers = {}
            #self.received_messages = []
            self.saved_messages = []
            self.long_buffer = {}
            self.long_sent_buffer = {}
            self.running = True
            self.boops = 0
            if self.master.admin:
                try:
                    self.aen.irq(self.irq_receive_task)#Processes the messages asap after receiving them
                except KeyboardInterrupt:#Trigger should be disabled when ctrl. C-ing
                    self.aen.irq(trigger=0)
                    self.aen.irq(handler=None)
            else:
                self.aen.irq(self.irq_receive_task)#Processes the messages asap after receiving them, this will not be interrupted by doing ctrl c
            
            #start_loop()#this would start the async loop
            self.iprint("ESP-NOW initialized and ready")

        def add_peer(self, peer_mac, channel=0, ifidx=0, name=""): #ifidx can be 0 or 1, sending data via network.STA_IF or network.AP_IF respectively
            self.master.dprint("aen.add_peer")
            if peer_mac not in self.peers:
                try:
                    self.peers[peer_mac] = {'channel': channel, 'ifidx': ifidx, 'name': ""}
                    self.iprint(f"Peer {peer_mac} added with channel {channel} and ifidx {ifidx}")
                except OSError as e:
                    print(f"Error adding peer {peer_mac}: {e}")
            else:
                self.master.dprint(f"Peer {peer_mac} already exists")

        def remove_peer(self, peer_mac):
            self.master.dprint("aen.remove_peers")
            if peer_mac in self.peers:
                try:
                    del self.peers[peer_mac]
                    self.iprint(f"Peer {peer_mac} removed")
                except OSError as e:
                    print(f"Error removing peer {peer_mac}: {e}")
                    
        def update_peer(self, peer_mac, new_channel=None, new_ifidx=None):
            self.master.dprint("aen.update_peer")
            for peer in self.peers:
                if peer[0] == peer_mac:
                    updated_peer = (
                        peer[0],
                        new_channel if new_channel is not None else peer[1],
                        new_ifidx if new_ifidx is not None else peer[2]
                    )
                    self.peers.remove(peer)
                    self.peers.add(updated_peer)
                    self.iprint(f"Peer {peer_mac} updated to channel {updated_peer[1]} and ifidx {updated_peer[2]}")
                return
            self.iprint(f"Peer {peer_mac} not found")

        def peers(self):
            self.master.dprint("aen.peers")
            return self.peers
        
        def espeers_n(self):#Necessary?
            self.master.dprint("aen.espeers_n")
            return peer_count() #This should always return 1 & 0 as peers are only added in a send command and then removed
        
        def espeers(self):#Necessary?
            self.master.dprint("aen.espeers")
            return self.aen.get_peers() #This should always return only the broadcast address (if any at all) as other MACs are continously removed after sending
        
        def rssi(self):
            self.master.dprint("aen.rssi")
            return self.aen.peers_table
        
        def broadcast(self, msg, channel=None, ifidx=None):#needed?
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
                self.iprint(f"Sent to {peer_mac}: {msg}")
            except Exception as e:
                print(f"Error sending to {peer_mac}: {e}")
            try:
                self.aen.del_peer(peer_mac)
            except Exception as e:
                print(f"Error removing {peer_mac} from buffer: {e}")
            
        def send_multiple(self, peers_mac, msg, channels=None, ifidxs=None):#needed?
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
                self.iprint(f"Sent to multiple: {msg}")
            except Exception as e:
                print(f"Error sending to all: {e}")
            for peer_mac in peers_mac:
                try:    
                    self.aen.del_peer(peer_mac)
                except Exception as e:
                    print(f"Error removing {peer_mac} from buffer: {e}")
                
        def send(self, peer_mac, msg, msg_type=0x02, subtype=0x22, channel=None, ifidx=None):
            self.master.dprint("aen.send")
            messages = self.create_payload(msg_type, subtype, msg, channel, ifidx)
            self.__send(peer_mac, messages, channel, ifidx)
                    
        def __send(self, peer_mac, messages, channel=None, ifidx=None):
            self.master.dprint("aen.__send")
            try:
                if channel != None and ifidx != None:
                    self.aen.add_peer(peer_mac, channel=channel, ifidx=ifidx)
                elif peer_mac in self.peers:
                    self.aen.add_peer(peer_mac, channel=self.peers[peer_mac]['channel'], ifidx=self.peers[peer_mac]['ifidx'])
                else:
                    self.aen.add_peer(peer_mac, channel=0, ifidx=0)
            except Exception as e:
                print(f"Error adding {peer_mac} to buffer: {e}")
            
            for message in messages:
                message = bytes(message) #only necessary if create function returns bytearray which it doesn't, conversion already done in create_payload
                try:
                    self.aen.send(peer_mac, message)
                    self.iprint(f"Sent to {peer_mac}: {message}")
                except Exception as e:
                    print(f"Error sending to {peer_mac}: {e}")
            try:    
                self.aen.del_peer(peer_mac)
            except Exception as e:
                    print(f"Error removing {peer_mac} from buffer: {e}")

        def receive_task(self): #Processes all the messages in the buffer
            self.master.dprint("aen.receive_task")
            if self.aen.any(): #this is necessary as the for loop gets stuck and does not exit properly.
                for sender_mac, data in self.aen:
                    self.master.dprint(f"Received {sender_mac, data}")
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
            self.master.dprint("aen.encode_payload")
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
            self.master.dprint("aen.decode_payload")
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
                iprint(f"Unsupported payload type: {payload_type} Message: {payload_bytes}")
                return None
        
        def create_payload(self, msg_type, subtype, payload=None, channel=None, ifidx=None):
            self.master.dprint("aen.create_payload")#rename to create_payload
            payload_type, payload_bytes = self.encode_payload(payload)
            payload_chunks = []
            total_chunk_number = 0
            if len(payload_bytes) < 242: #250-9=241=max_length
                payload_chunks.append(payload_bytes)
            else:
                self.master.dprint("Long message: Splitting!")
                max_size = 238 #241-3
                total_chunk_number = (-(-len(payload_bytes)//max_size)) #Round up division
                payload_type = b'\x07' #Long byte array
                if total_chunk_number > 256:
                    raise ValueError("More than 256 chunks, unsupported")
                for chunk_index in range(0, total_chunk_number):
                    chunk_bytes = bytearray()
                    chunk_bytes.extend(chunk_index.to_bytes(1, 'big'))
                    chunk_bytes.extend(total_chunk_number.to_bytes(1, 'big'))
                    chunk_bytes.extend(payload_type)
                    chunk_bytes.extend(payload_bytes[chunk_index*max_size:min((chunk_index+1)*max_size,len(payload_bytes))]) #Check bytes vs. bytearrays and bytearray.append vs bytearray.extend
                    payload_chunks.append(bytes(chunk_bytes))
            messages = []
            timestamp = time.ticks_ms()
            for payload_chunk in payload_chunks:
                total_length = 1 + 1 + 1 + 4 + 1 + len(payload_chunk) + 1
                identifier = 0x2a
                message = bytearray() #Make this prettier and consistent, especially check bytes vs. bytearrays and bytearray.append vs bytearray.extend
                message.append(identifier)
                message.append(msg_type)
                message.append(subtype)
                message.extend(timestamp.to_bytes(4, 'big'))
                message.extend(payload_type)
                message.extend(payload_chunk)
                checksum = sum(message) % 256
                message.append(checksum)
                self.master.dprint(len(message))
                self.master.dprint(message)
                messages.append(message)
            if total_chunk_number > 1:
                key = message[1:8]
                key.extend(total_chunk_number.to_bytes(1, 'big'))
                self.long_sent_buffer[bytes(key)] = (messages, (channel,ifidx))
            return [bytes(message) for message in messages] #returns bytes
            #return messages #returns bytearray
            
        def process_message(self, sender_mac, message, rtimestamp):
            self.master.dprint("aen.process_message")
            if message[0] != 0x2a:  # Uniqe Message Identifier Check
                self.master.dprint(" Invalid message: Message ID Fail")
                return None
            if len(message) < 9:  # Min size
                self.master.dprint(" Invalid message: too short")
                return None

            msg_type = bytes(message[1:2])
            subtype = bytes(message[2:3])
            stimestamp = int.from_bytes(message[3:7], 'big')
            payload_type = bytes(message[7:8])
            payload = message[8:-1]
            checksum = message[-1]
            self.master.dprint(f"{type(msg_type)}: {msg_type}, {type(subtype)}: {subtype}, {type(stimestamp)}: {stimestamp}, {type(payload_type)}: {payload_type},  {type(payload)}: {payload},  {type(checksum)}: {checksum}")
            
            #Checksum
            if checksum != sum(message[:-1]) % 256:
                self.master.dprint(" Invalid message: checksum mismatch")
                return None
            
            if sender_mac not in self.peers:
                self.add_peer(sender_mac)
            
            if payload_type == b'\x07':
                self.iprint("Long message received, processing")
                part_n = int.from_bytes(payload[0:1], 'big')
                total_n = int.from_bytes(payload[1:2], 'big')
                payload_type = bytes(payload[2:3])
                payload = payload[3:]
                
                key = (msg_type, subtype, stimestamp, payload_type, total_n)
                self.master.dprint(f"Key: {key}")
                if key in self.long_buffer:
                    if self.long_buffer[key][part_n] is None:
                        self.long_buffer[key][part_n] = payload
                        self.master.dprint(f"Long message: Key found, message added to entry in long_message_buffer, {sum(1 for item in self.long_buffer[key] if item is not None)} out of {total_n} packages received")
                        if any(value is None for value in self.long_buffer[key]):
                            return
                else:
                    payloads = [None] * total_n
                    payloads[part_n] = payload
                    self.long_buffer[key] = payloads
                    self.master.dprint(f"Long message: Key not found and new entry created in long_message_buffer, {sum(1 for item in self.long_buffer[key] if item is not None)} out of {total_n} packages received")
                    if any(value is None for value in self.long_buffer[key]):
                        #create an async task to run in 3 seconds, it checks if the message is still in the buffer and requests the messages to be resent, it does this for a maximum of N times
                        #The message should be a bytearray with all the key elements, followed by the indexes of the missing messages
                        #value])
                        none_indexes = [index for index, value in enumerate(self.long_buffer[key]) if value is None]
                        #the thing below is a list!
                        message = []
                        message.append(msg_type)
                        message.append(subtype)
                        message.append(stimestamp.to_bytes(4, 'big'))
                        message.append(payload_type)
                        message.append(total_n.to_bytes(1, 'big'))
                        for none_index in none_indexes:
                            message.append(none_index.to_bytes(1, 'big'))
                        return
                if not any(value is None for value in self.long_buffer[key]):
                    payload = bytearray()
                    for i in range(0, total_n):
                        payload.extend(self.long_buffer[key][i])
                    del self.long_buffer[key]
                    self.master.dprint(f"Long message: All packages received!")
                else:
                    self.master.dprint("Long Message: Safeguard triggered, code should not have gotten here")
                    return
              
            if msg_type == b'\x01':  # Command Message
                self.handle_cmd(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
            elif msg_type == b'\x02':  # Informational Message
                self.handle_inf(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
            elif msg_type == b'\x03':  # Acknowledgement Message
                self.handle_ack(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
            else:
                self.master.dprint(f"Unknown message type from {sender_mac}: {message}")

        def handle_cmd(self, sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
            self.master.dprint("aen.handle_cmd")
            if subtype == b'\x10': #Ping
                self.iprint(f"Ping command received from {sender_mac}")
                info = self.decode_payload(payload_type, payload)
                self.add_peer(sender_mac, info[0], info[1], info[2])
                channel = self.master.channel()#Make sure to account for sta send and ap send
                ifidx = 0
                response = [channel, ifidx, self.master.name, stimestamp]
                self.send(sender_mac, response, 0x03, 0x10)
            elif subtype == b'\x11': #Pair
                self.iprint(f"Pairing command received from {sender_mac}")
                # Insert pairing logic here
            elif subtype == b'\x12': #Change Mode to Firmware Update
                self.iprint(f"Update command received from {sender_mac}")
                # Insert update logic here
            elif subtype == b'\x13': #RSSI Boop
                self.boops = self.boops + 1
                self.iprint(f"Boop command received from {sender_mac}, Received total of {self.boops} boops!")
                #self.send(sender_mac, self.peers_table, 0x02, 0x20)
            elif subtype == b'\x14': #Reboot
                self.iprint(f"Reboot command received from {sender_mac}")
                machine.reset()
            elif subtype == b'\x15': #Echo
                self.iprint(f"Echo command received from {sender_mac}: {payload}")
                self.send(sender_mac, self.decode_payload(payload_type, payload), 0x03, 0x15)
            elif subtype == b'\x16': #Run file
                filename = self.decode_payload(payload_type, payload)
                self.iprint(f"Run command received from {sender_mac}: {filename}")    
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
                self.iprint(f"Received resend long message command, checking buffer for lost message")
                key = payload[0:8]
                indexes_b = payload[8:]
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
                    self.iprint(f"Resent all requested messages")
                else:
                    self.iprint(f"Message not found in the buffer")
            elif subtype == b'\x18': #Connect to WiFi
                payload = self.decode_payload(payload_type, payload) #should return a list of ssid and password
                self.iprint(f"Received connect to wifi command")
                self.connect(payload[0], payload[1])
            elif subtype == b'\x19': #Disconnect from WiFi
                self.iprint(f"Received disconnect from wifi command")
                self.disconnect()
            elif subtype == b'\x20': #Enable AP
                payload = self.decode_payload(payload_type, payload) #should return a list of desired name, password an max clients
                self.iprint(f"Received setup AP command")
                ssid = payload[0]
                if ssid == "":
                    ssid = self.name
                password = payload[1]
                self.setap(ssid, password)
            elif subtype == b'\x21': #Disable AP
                self.iprint(f"Received disable AP command")
                #disaple ap command
            elif subtype == b'\x22': #Set Admin Bool
                payload = self.decode_payload(payload_type, payload) #should return a bool
                self.iprint(f"Received set admin command: self.admin set to {payload}")
                self.master.admin = payload
            else:
                self.vprint(f"Unknown command subtype from {sender_mac}: {subtype}")

        def handle_inf(self, sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
            self.master.dprint("aen.inf")
            if subtype == b'\x21': #Sensor Data
                self.iprint(f"Sensor data received from {sender_mac}: {payload}")
                # Process sensor data
            elif subtype == b'\x20': #RSSI
                self.iprint(f"RSSI data received from {sender_mac}: {payload}")
                # Process RSSI data
            elif subtype == b'\x22': #Other
                self.iprint(f"Message received from {sender_mac}: {payload}")
                self.saved_messages.append((sender_mac, payload, rtimestamp))
            else:
                self.iprint(f"Unknown info subtype from {sender_mac}: {subtype}")
                
        def handle_ack(self, sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
            self.master.dprint("aen.handle_ack")
            if subtype == b'\x10': #Pong
                info = self.decode_payload(payload_type, payload)
                self.add_peer(sender_mac, info[0], info[1], info[2])
                self.iprint(f"Pong received from {sender_mac}, {rtimestamp-info[3]}")
            elif subtype == b'\x15': #Echo
                self.iprint(f"Echo received from {sender_mac}, {self.decode_payload(payload_type, payload)}")
            else:    
                self.iprint(f"Unknown ack subtype from {sender_mac}: {subtype}, Payload: {payload}")
            # Insert more acknowledgement logic here add message to acknowledgement buffer
                
        def ping(self, mac):
            self.master.dprint("aen.ping")
            channel = self.master.channel()#make sure to account for sta send and ap send
            ifidx = 0
            self.send(mac, [channel,ifidx,self.master.name], 0x01, 0x10) #sends channel, ifidx and name
            self.iprint(f"Sent ping to {mac}")
        
        def echo(self, mac, message):
            self.master.dprint("aen.echo")
            self.send(mac, message, 0x01, 0x15)
            self.iprint(f"Sent {message} to {mac}")
        
        def message(self, mac, message):
            self.master.dprint("aen.message")
            self.send(mac, message, 0x02, 0x22)
            self.iprint(f"Sent {message} to {mac}")
            
        def check_messages(self):
            self.master.dprint("aen.check_message")
            return len(self.saved_messages) > 0
        
        def return_message(self):
            self.master.dprint("aen.return_message")
            if self.saved_messages:
                return self.saved_messages-pop()
            return None
        
        def return_messages(self):
            self.master.dprint("aen.return_messages")
            messages = self.saved_messages[:]
            self.saved_messages.clear()
            return messages

        def stop(self):
            self.master.dprint("aen.stop")
            self.running = False
            self.aen.active(False)
            self.iprint("ESP-NOW stopped")
            
        def resume(self):
            self.master.dprint("aen.resume")
            self.running = True
            self.aen.active(True)
            self.iprint("ESP-NOW resumed")
            
        #The below async functions are not needed anymore
        async def start(self, sleep=0.1):
            self.master.dprint("aen.start")
            while is_running:
                self.receive_task()
                await asyncio.sleep(sleep)
                
        async def start_loop(self, sleep=0.1):
            self.master.dprint("aen.start_loop")
            loop = asyncio.get_event_loop()
            loop.create_task(start(sleep))
            loop.run_forever()
            
        def irq_receive_task(self, espnow):
            self.master.dprint("aen.irq_receive_task")
            self.receive_task()
            return
           
#message structure (what kind of message types do I need?: Command which requires me to do something (ping, pair, change state(update, code, mesh mode, run a certain file), Informational Message (Sharing Sensor Data and RSSI Data)
#| Header (1 byte) | Type (1 byte) | Subtype (1 byte) | Timestamp(ms ticks) (4 bytes) | Payload type (1) | Payload (variable) | Checksum (1 byte) |
