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
        self._infmsg = True
        self._dbgmsg = False
        self._admin = False
            
        self._staif = network.WLAN(network.STA_IF)
        self._apif = network.WLAN(network.AP_IF)
        
        self.sta = self.Sta(self, self._staif)
        self.ap = self.Ap(self, self._apif)
        self.aen = self.Aen(self)
        
        self.id = ubinascii.hexlify(machine.unique_id()).decode()
        self.name = configname
        if self.name == "":
            self.name = str(self.id)
        
    def _iprint(self, message):
        if self._infmsg:
            print(message)
        return
            
    def _dprint(self, message):
        if self._dbgmsg:
            print(message)
        return
    
    
    
    class Sta:
        def __init__(self, master, _staif):
            self.master = master
            self._sta = _staif
            self._sta.active(True)
            self.master._iprint("STA initialized and ready")
            
        def scan(self):
            self.master._dprint("sta.scan")
            scan_result = self._sta.scan()
            if self._infmsg:
                for ap in scan_result:
                    self.master._iprint("SSID:%s BSSID:%s Channel:%d Strength:%d RSSI:%d Auth:%d " % (ap))
            return scan_result
    
        def connect(self, ssid, key="", timeout=10):
            self.master._dprint("sta.connect")
            self._sta.connect(ssid, key)
            stime = time.time()
            #self._sta.status() returns the current wlan status, update below functions with it
            while time.time() - stime < timeout:
                if self._sta.ifconfig()[0] != '0.0.0.0':
                    self.master._iprint("Connected to WiFi")
                    return
                time.sleep(1)
            self.master._iprint(f"Failed to connect to WiFi: {self._sta.status()}")
        
        def disconnect(self):
            self.master._dprint("sta.disconnect")
            self._sta.disconnect()
            
        def ip(self):
            self.master._dprint("sta.ip")
            return self._sta.ifconfig()
    
        def mac(self):
            self.master._dprint("sta.mac")
            return bytes(self._sta.config('mac'))
        
        def mac_decoded(self):#Necessary?
            self.master._dprint("sta.mac_decoded")
            return ubinascii.hexlify(self._sta.config('mac'), ':').decode()
        
        def channel(self):#Is there an equivalent for AP? How does setting channels work for ESP-Now????????
            self.master._dprint("sta.channel")
            return self._sta.config('channel')
        
        def set_channel(self, number):
            self.master._dprint("sta.set_channel")
            if number > 14 or number < 0:
                number = 0
            self._sta.config(channel=number)
            self.vprint(f"STA channel set to {number}")
            #This will override the channel that was set as part of the add_peer function ???
        
        def get_joke(self):
            self.master._dprint("sta.get_joke")
            try:
                reply = urequests.get('https://v2.jokeapi.dev/joke/Programming')
                if reply.status_code == 200:
                    joke = reply.json()
                    return joke.get('setup', '') + '\n' + joke.get('delivery', joke.get('joke', ''))
            except Exception as e:
                print('Error fetching joke:', str(e))
            return None
  
  
  
    class Ap:
        def __init__(self, master, _apif):
            self.master = master
            self._ap = _apif
            self._ap.active(True)
            self.master._iprint("AP initialized and ready")
        
        def set_ap(self, name="", password="", max_clients=10):
            self.master._dprint("ap.setap")
            if name == "":
                name = self.name
            self._ap.active(True)
            self._ap.config(essid=name)
            if password:
                self._ap.config(authmode=network.AUTH_WPA_WPA2_PSK, password=password)
            self._ap.config(max_clients=max_clients)
            self.master._iprint(f"Access Point {name} set with max clients {max_clients}")
        
        def deactivate(self):
            self.master._dprint("ap.deactivate")
            self._ap.active(False)
            self.master._iprint("Access Point deactivated")
            
        def ip(self):
            self.master._dprint("ap.ip")
            return self._ap.ifconfig()
    
        def mac(self):
            self.master._dprint("ap.mac")
            return bytes(self._ap.config('mac'))
        
        def mac_decoded(self):#Necessary?
            self.master._dprint("ap.mac_decoded")
            return ubinascii.hexlify(self._ap.config('mac'), ':').decode()
        
        def channel(self): #How does setting channels work for ESP-Now????????
            self.master._dprint("ap.channel")
            return self._ap.config('channel')
        
        def set_channel(self, number):
            self.master._dprint("ap.set_channel")
            if number > 14 or number < 0:
                number = 0
            self._ap.config(channel=number)
            self.vprint(f"AP channel set to {number}")
            #This will override the channel that was set as part of the add_peer function ???



    class Aen:
        def __init__(self, master):
            self.master = master
            self._aen = espnow.ESPNow()
            self._aen.active(True)
            
            self._peers = {}
            #self.received_messages = []
            self._saved_messages = []
            self._long_buffer = {}
            self._long_sent_buffer = {}
            #self.running = True
            self._irq_function = None
            self.boops = 0
            self.ifidx = 0 #0 sends via sta, 1 via ap
            
            if self.master._admin:
                try:
                    self._aen.irq(self._irq)
                except KeyboardInterrupt:#Trigger should be disabled when ctrl. C-ing
                    self._aen.irq(trigger=0)
                    self._aen.irq(handler=None)
            else:
                self._aen.irq(self._irq)#Processes the messages asap after receiving them, this should not be interrupted by doing ctrl c
            
            self.master._iprint("ESP-NOW initialized and ready")
            
        def update_peer(self, peer_mac, name="", new_channel=None, new_ifidx=None):
            self.master._dprint("aen.update_peer")
            for peer in self._peers:
                if peer[0] == peer_mac:
                    updated_peer = (
                        peer[0],
                        new_channel if new_channel is not None else peer[1],
                        new_ifidx if new_ifidx is not None else peer[2],
                        name if name is not "" else peer[3]
                    )
                    self._peers.remove(peer)
                    self._peers.add(updated_peer)
                    self.master._dprint(f"Peer {peer_mac} updated to channel {updated_peer[1]} and ifidx {updated_peer[2]}")
                return
            self.master._iprint(f"Peer {peer_mac} not found")

        def add_peer(self, peer_mac, name="", channel=0, ifidx=0):
            self.master._dprint("aen.add_peer")
            if peer_mac not in self._peers:
                try:
                    self._peers[peer_mac] = {'channel': channel, 'ifidx': ifidx, 'name': name}
                    self.master._dprint(f"Peer {peer_mac} added with channel {channel} and ifidx {ifidx}")
                except OSError as e:
                    print(f"Error adding peer {peer_mac}: {e}")
            else:
                self.master._dprint(f"Peer {peer_mac} already exists, updating")
                self.update_peer(peer_mac, channel, ifidx, name)

        def remove_peer(self, peer_mac):
            self.master._dprint("aen.remove_peers")
            if peer_mac in self._peers:
                try:
                    del self._peers[peer_mac]
                    self.master._iprint(f"Peer {peer_mac} removed")
                except OSError as e:
                    print(f"Error removing peer {peer_mac}: {e}")

        def peers(self):
            self.master._dprint("aen.peers")
            return self._peers
        
        def rssi(self):
            self.master._dprint("aen.rssi")
            return self._aen.peers_table
        
        def ping(self, mac):
            self.master._dprint("aen.ping")
            self.master._iprint(f"Sending ping to {mac}")
            if bool(self.ifidx):
                channel = self.master.ap.channel()#make sure to account for sta send and ap send
            else:
                channel = self.master.sta.channel()#make sure to account for sta send and ap send
            self._compose(mac, [channel,self.ifidx,self.master.name], 0x01, 0x10) #sends channel, ifidx and name
        
        def echo(self, mac, message):
            self.master._dprint("aen.echo")
            self.master._iprint(f"Sending echo ({message}) to {mac}")
            self._compose(mac, message, 0x01, 0x15)
        
        def send(self, mac, message):
            self.master._dprint("aen.message")
            self.master._iprint(f"Sending message ({message}) to {mac}")
            self._compose(mac, message, 0x02, 0x22)
            
        def broadcast(self, message):#needed?
            self.master._dprint("aen.broadcast")
            self.master._iprint(f"Sending message ({message}) to all")
            mac = b'\xff\xff\xff\xff\xff\xff'
            self._compose(mac, message, 0x02, 0x22)
              
        def check_messages(self):
            self.master._dprint("aen.check_message")
            return len(self._saved_messages) > 0
        
        def return_message(self):
            self.master._dprint("aen.return_message")
            if self.check_messages():
                return self._saved_messages.pop()
            return (None, None, None)
        
        def return_messages(self):
            self.master._dprint("aen.return_messages")
            if self.check_messages():
                messages = self._saved_messages[:]
                self._saved_messages.clear()
                return messages
            return [(None, None, None)]
            
        def _irq(self, espnow):
            self.master._dprint("aen._irq")
            self._receive()
            if self._irq_function and self.check_messages():
                self._irq_function()
            return
        
        def irq(self, func):
            self.master._dprint("aen.irq")
            self._irq_function = func
               
        def _send(self, peers_mac, messages, channel=None, ifidx=None):
            self.master._dprint("aen._send")
            
            def __aen_add_peer(peers_mac, channel, ifidx):
                if isinstance(peers_mac, bytes):
                    peers_mac = [peers_mac]
                for peer_mac in peers_mac:
                    try:
                        if channel != None and ifidx != None:
                            self._aen.add_peer(peer_mac, channel=channel, ifidx=ifidx)
                        elif peer_mac in self._peers:
                            self._aen.add_peer(peer_mac, channel=self._peers[peer_mac]['channel'], ifidx=self._peers[peer_mac]['ifidx'])
                        else:
                            self._aen.add_peer(peer_mac, channel=0, ifidx=self.ifidx)
                    except Exception as e:
                        print(f"Error adding {peer_mac} to buffer: {e}")
                    
            def __aen_del_peer(peers_mac):
                if isinstance(peers_mac, bytes):
                    peers_mac = [peers_mac]
                for peer_mac in peers_mac:
                    try:
                        self._aen.del_peer(peer_mac)
                    except Exception as e:
                        print(f"Error removing {peer_mac} from buffer: {e}")
                        
            __aen_add_peer(peers_mac, channel, ifidx)
            for message in messages:
                message = bytes(message) #just to be safe
                if isinstance(peers_mac, list):
                    mac = None
                else:
                    mac = peers_mac
                for i in range(3):
                    i += i
                    try:
                        self._aen.send(mac, message)
                        break
                    except Exception as e:
                        print(f"Error sending to {mac}: {e}")
                self.master._dprint(f"Sent {message} to {mac}")
            __aen_del_peer(peers_mac)
                
                
        def _compose(self, peer_mac, payload=None, msg_type=0x02, subtype=0x22, channel=None, ifidx=None):#rename the function
            self.master._dprint("aen._compose")
            
            def __encode_payload(payload):
                self.master._dprint("aen.__encode_payload")
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
            
            payload_type, payload_bytes = __encode_payload(payload)
            payload_chunks = []
            total_chunk_number = 0
            if len(payload_bytes) < 242: #250-9=241=max_length
                payload_chunks.append(payload_bytes)
            else:
                self.master._dprint("Long message: Splitting!")
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
                message = bytes(message)
                self.master._dprint(f"Message length: {len(message)}; Message: {message}")
                messages.append(message)
            if total_chunk_number > 1:
                key = message[1:8]
                key.extend(total_chunk_number.to_bytes(1, 'big'))
                self._long_sent_buffer[bytes(key)] = (messages, (channel,ifidx))

            self._send(peer_mac, messages, channel, ifidx)


        def _receive(self): #Processes all the messages in the buffer
            self.master._dprint("aen._receive")
            
            def __decode_payload(payload_type, payload_bytes):
                self.master._dprint("aen.__decode_payload")
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
            
            def __process_message(sender_mac, message, rtimestamp):
                self.master._dprint("aen.__process_message")
                if message[0] != 0x2a:  # Uniqe Message Identifier Check
                    self.master._dprint(" Invalid message: Message ID Fail")
                    return None
                if len(message) < 9:  # Min size
                    self.master._dprint(" Invalid message: too short")
                    return None

                msg_type = bytes(message[1:2])
                subtype = bytes(message[2:3])
                stimestamp = int.from_bytes(message[3:7], 'big')
                payload_type = bytes(message[7:8])
                payload = message[8:-1]
                checksum = message[-1]
                self.master._dprint(f"{type(msg_type)}: {msg_type}, {type(subtype)}: {subtype}, {type(stimestamp)}: {stimestamp}, {type(payload_type)}: {payload_type},  {type(payload)}: {payload},  {type(checksum)}: {checksum}")
                
                #Checksum
                if checksum != sum(message[:-1]) % 256:
                    self.master._dprint(" Invalid message: checksum mismatch")
                    return None
                
                if sender_mac not in self._peers:
                    self.add_peer(sender_mac)
                
                if payload_type == b'\x07':
                    self.master._iprint("Long message received, processing")
                    part_n = int.from_bytes(payload[0:1], 'big')
                    total_n = int.from_bytes(payload[1:2], 'big')
                    payload_type = bytes(payload[2:3])
                    payload = payload[3:]
                    
                    key = (msg_type, subtype, stimestamp, payload_type, total_n)
                    self.master._dprint(f"Key: {key}")
                    if key in self._long_buffer:
                        if self._long_buffer[key][part_n] is None:
                            self._long_buffer[key][part_n] = payload
                            self.master._dprint(f"Long message: Key found, message added to entry in long_message_buffer, {sum(1 for item in self._long_buffer[key] if item is not None)} out of {total_n} packages received")
                            if any(value is None for value in self._long_buffer[key]):
                                return
                    else:
                        payloads = [None] * total_n
                        payloads[part_n] = payload
                        self._long_buffer[key] = payloads
                        self.master._dprint(f"Long message: Key not found and new entry created in long_message_buffer, {sum(1 for item in self._long_buffer[key] if item is not None)} out of {total_n} packages received")
                        if any(value is None for value in self._long_buffer[key]):
                            #create an async task to run in 3 seconds, it checks if the message is still in the buffer and requests the messages to be resent, it does this for a maximum of N times
                            #The message should be a bytearray with all the key elements, followed by the indexes of the missing messages
                            #value])
                            none_indexes = [index for index, value in enumerate(self._long_buffer[key]) if value is None]
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
                    if not any(value is None for value in self._long_buffer[key]):
                        payload = bytearray()
                        for i in range(0, total_n):
                            payload.extend(self._long_buffer[key][i])
                        del self._long_buffer[key]
                        self.master._dprint(f"Long message: All packages received!")
                    else:
                        self.master._dprint("Long Message: Safeguard triggered, code should not have gotten here")
                        return
                  
                if msg_type == b'\x01':  # Command Message
                    __handle_cmd(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
                elif msg_type == b'\x02':  # Informational Message
                    __handle_inf(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
                elif msg_type == b'\x03':  # Acknowledgement Message
                    __handle_ack(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload if payload else None)
                else:
                    self.master._dprint(f"Unknown message type from {sender_mac}: {message}")

            def __handle_cmd(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
                self.master._dprint("aen.__handle_cmd")
                if subtype == b'\x10': #Ping
                    self.master._iprint(f"Ping command received from {sender_mac}")#Check i or d
                    info = __decode_payload(payload_type, payload)
                    self.add_peer(sender_mac, info[2], info[0], info[1])
                    if bool(self.ifidx):
                        channel = self.master.ap.channel()
                    else:
                        channel = self.master.sta.channel()
                    response = [channel, ifidx, self.master.name, stimestamp]
                    self._compose(sender_mac, response, 0x03, 0x10)
                elif subtype == b'\x11': #Pair
                    self.master._dprint(f"Pairing command received from {sender_mac}")
                    # Insert pairing logic here
                elif subtype == b'\x12': #Change Mode to Firmware Update
                    self.master._dprint(f"Update command received from {sender_mac}")
                    # Insert update logic here
                elif subtype == b'\x13': #RSSI Boop
                    self.boops = self.boops + 1
                    self.master._dprint(f"Boop command received from {sender_mac}, Received total of {self.boops} boops!")
                    #self._compose(sender_mac, self._peers_table, 0x02, 0x20)
                elif subtype == b'\x14': #Reboot
                    self.master._dprint(f"Reboot command received from {sender_mac}")
                    machine.reset()
                elif subtype == b'\x15': #Echo
                    self.master._iprint(f"Echo command received from {sender_mac}: {payload}")#Check i or d
                    self._compose(sender_mac, __decode_payload(payload_type, payload), 0x03, 0x15)
                elif subtype == b'\x16': #Run file
                    filename = __decode_payload(payload_type, payload)
                    self.master._dprint(f"Run command received from {sender_mac}: {filename}")    
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
                    payload = __decode_payload(payload_type, payload)
                    self.master._iprint(f"Received resend long message command, checking buffer for lost message")
                    key = payload[0:8]
                    indexes_b = payload[8:]
                    indexes = []
                    for i in range(0, len(indexes_b)):
                        indexes.append(int.from_bytes(indexes_b[i], 'big'))
                    if key in self._long_sent_buffer:
                        channel = self._long_sent_buffer[key][1][0]
                        ifidx = self._long_sent_buffer[key][1][1]
                        for index in indexes:
                            message.append(self._long_sent_buffer[key][0][index])
                        self._send(sender_mac, messages, channel, ifidx)
                        #resend the message from the message buffer
                        self.master._dprint(f"Resent all requested messages")
                    else:
                        self.master._iprint(f"Message not found in the buffer")
                elif subtype == b'\x18': #Connect to WiFi
                    payload = __decode_payload(payload_type, payload) #should return a list of ssid and password
                    self.master._iprint(f"Received connect to wifi command")
                    self.connect(payload[0], payload[1])
                elif subtype == b'\x19': #Disconnect from WiFi
                    self.master._iprint(f"Received disconnect from wifi command")
                    self.disconnect()
                elif subtype == b'\x20': #Enable AP
                    payload = __decode_payload(payload_type, payload) #should return a list of desired name, password an max clients
                    self.master._iprint(f"Received setup AP command")
                    ssid = payload[0]
                    if ssid == "":
                        ssid = self.name
                    password = payload[1]
                    self.setap(ssid, password)
                elif subtype == b'\x21': #Disable AP
                    self.master._iprint(f"Received disable AP command")
                    #disaple ap command
                elif subtype == b'\x22': #Set Admin Bool
                    payload = __decode_payload(payload_type, payload) #should return a bool
                    self.master._iprint(f"Received set admin command: self.admin set to {payload}")
                    self.master._admin = payload
                else:
                    self.vprint(f"Unknown command subtype from {sender_mac}: {subtype}")

            def __handle_inf(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
                self.master._dprint("aen.__inf")
                if subtype == b'\x21': #Sensor Data
                    self.master._iprint(f"Sensor data received from {sender_mac}: {payload}")
                    # Process sensor data
                elif subtype == b'\x20': #RSSI
                    self.master._iprint(f"RSSI data received from {sender_mac}: {payload}")
                    # Process RSSI data
                elif subtype == b'\x22': #Other
                    self.master._iprint(f"Message received from {sender_mac}: {payload}")
                    self._saved_messages.append((sender_mac, payload, rtimestamp))
                else:
                    self.master._iprint(f"Unknown info subtype from {sender_mac}: {subtype}")
                    
            def __handle_ack(sender_mac, subtype, stimestamp, rtimestamp, payload_type, payload):
                self.master._dprint("aen.__handle_ack")
                if subtype == b'\x10': #Pong
                    info = __decode_payload(payload_type, payload)
                    self.add_peer(sender_mac, info[2], info[0], info[1])
                    self.master._iprint(f"Pong received from {sender_mac}, {rtimestamp-info[3]}") #Always print this
                elif subtype == b'\x15': #Echo
                    self.master._iprint(f"Echo received from {sender_mac}, {__decode_payload(payload_type, payload)}") #Always print this
                else:    
                    self.master._iprint(f"Unknown ack subtype from {sender_mac}: {subtype}, Payload: {payload}")
                # Insert more acknowledgement logic here add message to acknowledgement buffer

            if self._aen.any(): #this is necessary as the for loop gets stuck and does not exit properly.
                for sender_mac, data in self._aen:
                    self.master._dprint(f"Received {sender_mac, data}")
                    if sender_mac is None:   # mac, msg will equal (None, None) on timeout
                        break
                    if data:
                        rtimestamp = time.ticks_ms()
                        if sender_mac != None and data != None:
                            #self.received_messages.append((sender_mac, data, rtimestamp))#Messages will be saved here, this is only for debugging purposes
                            #print(f"Received from {sender_mac}: {data}")
                            __process_message(sender_mac, data, rtimestamp)
                    if not self._aen.any():
                        break
                    
           
#message structure (what kind of message types do I need?: Command which requires me to do something (ping, pair, change state(update, code, mesh mode, run a certain file), Informational Message (Sharing Sensor Data and RSSI Data)
#| Header (1 byte) | Type (1 byte) | Subtype (1 byte) | Timestamp(ms ticks) (4 bytes) | Payload type (1) | Payload (variable) | Checksum (1 byte) |
