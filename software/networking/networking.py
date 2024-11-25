import network
import machine
from config import mysecrets, configname, config, whitelist, i2c_dict, version, msg_codes, msg_subcodes
import time
import ubinascii
import urequests
import espnow
import gc
import asyncio
import struct
import json
import os

inittime = time.ticks_ms()

class Networking:       
    def __init__(self, infmsg=False, dbgmsg=False, admin=False):
        self.inittime = inittime
        if infmsg:
            print(f"{(time.ticks_ms() - inittime) / 1000:.3f} Initialising Networking")
        self.master = self
        self.infmsg = infmsg
        self.dbgmsg = dbgmsg
        self.admin = admin
            
        self._staif = network.WLAN(network.STA_IF)
        self._apif = network.WLAN(network.AP_IF)
        
        self.sta = self.Sta(self, self._staif)
        self.ap = self.Ap(self, self._apif)
        self.aen = self.Aen(self)
        
        self.id = ubinascii.hexlify(machine.unique_id()).decode()
        self.name = configname
        if not self.name:
            self.name = str(self.id)
        self.config = config
        self.version = version
        self.version_n = ''.join(str(value) for value in self.version.values())
        if infmsg:
            print(f"{(time.ticks_ms() - inittime) / 1000:.3f} seconds: Networking initialised and ready")
            
    def cleanup(self):
        self.dprint(".cleanup")
        self.aen.cleanup()
        self._staif.active(False)
        self._apif.active(False)
        
    def iprint(self, message):
        if self.infmsg:
            try:
                print(f"{(time.ticks_ms() - inittime) / 1000:.3f} Networking Info: {message}")
            except Exception as e:
                print(f"Error printing networking Info: {e}")
        return
            
    def dprint(self, message):
        if self.dbgmsg:
            try:
                print(f"{(time.ticks_ms() - inittime) / 1000:.3f} Networking Debug: {message}")
            except Exception as e:
                print(f"Error printing networking Debug: {e}")
        return
    
    
    
    class Sta:

        def __init__(self, master, _staif):
            self.master = master
            self._sta = _staif
            self._sta.active(True)
            self.master.iprint("STA initialised and ready")
            
        def scan(self):
            self.master.dprint("sta.scan")
            scan_result = self._sta.scan()
            if self.infmsg:
                for ap in scan_result:
                    self.master.iprint(f"SSID:%s BSSID:%s Channel:%d Strength:%d RSSI:%d Auth:%d " % ap)
            return scan_result
    
        def connect(self, ssid, key="", timeout=10):
            self.master.dprint("sta.connect")
            self._sta.connect(ssid, key)
            stime = time.time()
            while time.time() - stime < timeout:
                if self._sta.ifconfig()[0] != '0.0.0.0':
                    self.master.iprint("Connected to WiFi")
                    return
                time.sleep(0.1)
            self.master.iprint(f"Failed to connect to WiFi: {self._sta.status()}")
        
        def disconnect(self):
            self.master.dprint("sta.disconnect")
            self._sta.disconnect()
            
        def ip(self):
            self.master.dprint("sta.ip")
            return self._sta.ifconfig()
    
        def mac(self):
            self.master.dprint("sta.mac")
            return bytes(self._sta.config('mac'))
        
        def mac_decoded(self):#Necessary?
            self.master.dprint("sta.mac_decoded")
            return ubinascii.hexlify(self._sta.config('mac'), ':').decode()
        
        def channel(self):
            self.master.dprint("sta.channel")
            return self._sta.config('channel')
        
        def set_channel(self, number):
            self.master.dprint("sta.set_channel")
            if number > 14 or number < 0:
                number = 0
            self._sta.config(channel=number)
            self.vprint(f"STA channel set to {number}")
        
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
        def __init__(self, master, _apif):
            self.master = master
            self._ap = _apif
            self._ap.active(True)
            self.master.iprint("AP initialised and ready")
        
        def set_ap(self, name="", password="", max_clients=10):
            self.master.dprint("ap.set_ap")
            if name == "":
                name = self.name
            self._ap.active(True)
            self._ap.config(essid=name)
            if password:
                self._ap.config(authmode=network.AUTH_WPA_WPA2_PSK, password=password)
            self._ap.config(max_clients=max_clients)
            self.master.iprint(f"Access Point {name} set with max clients {max_clients}")
        
        def deactivate(self):
            self.master.dprint("ap.deactivate")
            self._ap.active(False)
            self.master.iprint("Access Point deactivated")
            
        def ip(self):
            self.master.dprint("ap.ip")
            return self._ap.ifconfig()
    
        def mac(self):
            self.master.dprint("ap.mac")
            return bytes(self._ap.config('mac'))
        
        def mac_decoded(self):
            self.master.dprint("ap.mac_decoded")
            return ubinascii.hexlify(self._ap.config('mac'), ':').decode()
        
        def channel(self):
            self.master.dprint("ap.channel")
            return self._ap.config('channel')
        
        def set_channel(self, number):
            self.master.dprint("ap.set_channel")
            if number > 14 or number < 0:
                number = 0
            self._ap.config(channel=number)
            self.vprint(f"AP channel set to {number}")



    class Aen:
        def __init__(self, master):
            self.master = master
            self._aen = espnow.ESPNow()
            self._aen.active(True)
            
            self._peers = {}
            self._received_messages = []
            self._received_messages_size = []
            self._long_buffer = {}
            self._long_buffer_size = {}
            self.received_sensor_data = {}
            self.received_rssi_data = {}
            #self._long_sent_buffer = {}
            self._irq_function = None
            self._pause_function = None
            self.boops = 0
            self.ifidx = 0 #0 sends via sta, 1 via ap
            #self._channel = 0
            
            self._whitelist = whitelist
            
            #Flags
            self._pairing = True
            self._running = True
            
            self._aen.irq(self._irq)
            
            self.master.iprint("ESP-NOW initialised and ready")

        def cleanup(self):
            self.master.iprint("aen.cleanup")
            self.irq(None)
            self._aen.active(False)
            #add delete buffers and stuff

        def update_peer(self, peer_mac, name=None, channel=None, ifidx=None):
            self.master.dprint("aen.update_peer")
            if peer_mac in self._peers:
                try:
                    if name is not None:
                        self._peers[peer_mac]['name'] = name
                    if channel is not None:
                        self._peers[peer_mac]['channel'] = channel
                    if ifidx is not None:
                        self._peers[peer_mac]['ifidx'] = ifidx
                    self.master.dprint(f"Peer {peer_mac} updated to channel {channel}, ifidx {ifidx} and name {name}")
                except OSError as e:
                    print(f"Error updating peer {peer_mac}: {e}")
                return
            self.master.iprint(f"Peer {peer_mac} not found")

        def add_peer(self, peer_mac, name=None, channel=None, ifidx=None):
            self.master.dprint("aen.add_peer")
            if peer_mac not in self._peers:
                try:
                    self._peers[peer_mac] = {'channel': channel, 'ifidx': ifidx, 'name': name}
                    self.master.dprint(f"Peer {peer_mac} added with channel {channel}, ifidx {ifidx} and name {name}")
                except OSError as e:
                    print(f"Error adding peer {peer_mac}: {e}")
            else:
                self.master.dprint(f"Peer {peer_mac} already exists, updating")
                self.update_peer(peer_mac, name, channel, ifidx)

        def remove_peer(self, peer_mac):
            self.master.dprint("aen.remove_peers")
            if peer_mac in self._peers:
                try:
                    del self._peers[peer_mac]
                    self.master.iprint(f"Peer {peer_mac} removed")
                except OSError as e:
                    print(f"Error removing peer {peer_mac}: {e}")

        def peers(self):
            self.master.dprint("aen.peers")
            return self._peers
        
        def peer_name(self, key):
            self.master.dprint("aen.name")
            if key in self._peers:
                return self._peers[key]['name']
            else:
                return None
        
        def rssi(self):
            self.master.dprint("aen.rssi")
            return self._aen.peers_table

        #Send cmds
        def ping(self, mac, channel=None, ifidx=None):
            self.master.dprint("aen.ping")
            if bool(self.ifidx):
                send_channel = self.master.ap.channel()
            else:
                send_channel = self.master.sta.channel()
            self._compose(mac, [send_channel,self.ifidx,self.master.name], 0x01, 0x10, channel, ifidx) #sends channel, ifidx and name
            self.master.iprint(f"Sent ping to {mac} ({self.peer_name(mac)})")
            gc.collect()
        
        def echo(self, mac, message, channel=None, ifidx=None):
            self.master.dprint("aen.echo")
            try:
                self.master.iprint(f"Sending echo ({message}) to {mac} ({self.peer_name(mac)})")
            except Exception as e:
                self.master.iprint(f"Sending echo to {mac} ({self.peer_name(mac)}), but error printing message content: {e}")
            self._compose(mac, message, 0x01, 0x15, channel, ifidx)
            gc.collect()
        
        def send(self, mac, message, channel=None, ifidx=None):
            self.master.dprint("aen.message")
            if len(str(message)) > 241:
                try:
                    self.master.iprint(f"Sending message ({str(message)[:50] + '... (truncated)'}) to {mac} ({self.peer_name(mac)})")
                except Exception as e:
                    self.master.iprint(f"Sending message to {mac} ({self.peer_name(mac)}), but error printing message content: {e}")
                    gc.collect()
            else:
                self.master.iprint(f"Sending message ({message}) to {mac} ({self.peer_name(mac)})")
            self._compose(mac, message, 0x02, 0x22, channel, ifidx)
            gc.collect()
            self.master.dprint(f"Free memory: {gc.mem_free()}")
            
        def broadcast(self, message, channel=None, ifidx=None):
            self.master.dprint("aen.broadcast")
            mac = b'\xff\xff\xff\xff\xff\xff'
            self.send(mac, message, channel, ifidx)

        def send_data_sensor(self, mac, message, channel=None, ifidx=None):#message is a dict, key is the sensor type and the value is the sensor value
            self.master.dprint("aen.message")
            try:
                self.master.iprint(f"Sending sensor data ({message}) to {mac} ({self.peer_name(mac)})")
            except Exception as e:
                self.master.iprint(f"Sending sensor data to {mac} ({self.peer_name(mac)}), but error printing message content: {e}")
            self._compose(mac, message, 0x02, 0x21, channel, ifidx)

        #Boop RSSI/Config

        #set pair

        #pairing

        #Firmware Update Mode

        #File Update

        #enable WebREPL

        #Run File

        #Reboot

        #WiFi enable

        #WiFi disable

        #AP enable

        #AP disable

        #admin bool

        #ad admin mac to whitelist

        #continue

        #pause

        #download gitHub files

        #file directory cmd


        def check_messages(self):
            self.master.dprint("aen.check_message")
            return len(self._received_messages) > 0
        
        def return_message(self):
            self.master.dprint("aen.return_message")
            if self.check_messages():
                self._received_messages_size.pop()
                return self._received_messages.pop()
            return None, None, None
        
        def return_messages(self):
            self.master.dprint("aen.return_messages")
            if self.check_messages():
                messages = self._received_messages[:]
                self._received_messages.clear()
                self._received_messages_size.clear()
                gc.collect()
                return messages
            return [(None, None, None)]
            
        def _irq(self):
            self.master.dprint("aen._irq")
            if self.master.admin:
                try:
                    self._receive()
                    if self._irq_function and self.check_messages() and self._running:
                        self._irq_function()
                    gc.collect()
                    return
                except KeyboardInterrupt:
                    #machine.disable_irq() #throws errors
                    self.master.iprint("aen._irq except KeyboardInterrupt") 
                    #self._aen.irq(None) #does not work
                    self._aen.active(False)
                    #self.master.cleanup() #network cleanup
                    #self.cleanup() #aen cleanup
                    raise SystemExit("Stopping networking execution. ctrl-c or ctrl-d again to stop main code") #in thonny stops library code but main code keeps running, same in terminal
                    #self._running = False
                    #raise KeyboardInterrupt #error in thonny but then stops running, just keeps running in terminal
                    #sys.exit(0) #breaks thonny, keeps running and recv (although ctl-d-able and keeps running main loop in terminal
                    #machine.reset() #nogo keeps raising errors and running in terminal
                    #uos.sysexit() #raises an error in thonny but keeps running in terminal (although ctrl-d able)
                    #raise SystemExit #stops current library script, but main script keeps running, but now it just keeps the main code running in terminal...
                    #os.exec(sys.argv[0], sys.argv) #error in thonny, keeps running recv in terminal
                    #raise Exception("An error occurred!") #error in thonny, and then stops running due to keyboard interrupt, keeps running recv and irq in terminal
                    #raise KeyboardInterrupt("User interrupt simulated.") #interrupts library code, but main code keeps running, recv just keeps running in terminal
            else:
                self._receive()
                if self._irq_function and self.check_messages() and self._running:
                    self._irq_function()
                gc.collect()
                return
        
        def irq(self, func):
            self.master.dprint("aen.irq")
            self._irq_function = func
               
        def _send(self, peers_mac, messages, channel, ifidx):
            self.master.dprint("aen._send")     

            if isinstance(peers_mac, bytes):
                peers_mac = [peers_mac]
            for peer_mac in peers_mac:
                try:
                    if channel is not None and ifidx is not None:
                        self._aen.add_peer(peer_mac, channel=channel, ifidx=ifidx)
                    elif channel is not None:
                        if peer_mac in self._peers:
                            self._aen.add_peer(peer_mac, channel=channel, ifidx=self._peers[peer_mac]['ifidx'])
                        else:
                            self._aen.add_peer(peer_mac, channel=channel, ifidx=self.ifidx)
                    elif ifidx is not None:
                        if peer_mac in self._peers:
                            self._aen.add_peer(peer_mac, channel=self._peers[peer_mac]['channel'], ifidx=ifidx)
                        else:
                            self._aen.add_peer(peer_mac, channel=0, ifidx=ifidx)
                    elif peer_mac in self._peers:
                        self._aen.add_peer(peer_mac, channel=self._peers[peer_mac]['channel'],
                                           ifidx=self._peers[peer_mac]['ifidx'])
                    else:
                        self._aen.add_peer(peer_mac, channel=0, ifidx=self.ifidx)
                except Exception as e:
                    print(f"Error adding {peer_mac} to buffer: {e}")
                    
            for m in range(len(messages)):
                if isinstance(peers_mac, list):
                    mac = None
                else:
                    mac = peers_mac
                for i in range(3):
                    i += i
                    try:
                        self._aen.send(mac, messages[m])
                        break
                    except Exception as e:
                        print(f"Error sending to {mac}: {e}")
                self.master.dprint(f"Sent {messages[m]} to {mac} ({self.peer_name(mac)})")
                gc.collect()

            if isinstance(peers_mac, bytes):
                peers_mac = [peers_mac]
            for peer_mac in peers_mac:
                try:
                    self._aen.del_peer(peer_mac)
                except Exception as e:
                    print(f"Error removing {peer_mac} from buffer: {e}")
                 
        def _compose(self, peer_mac, payload=None, msg_type=0x02, subtype=0x22, channel=None, ifidx=None):
            self.master.dprint("aen._compose")
            
            if isinstance(peer_mac, list):
                 for peer_macs in peer_mac:
                     if peer_macs not in self._peers:
                         self.add_peer(peer_macs, None, channel, ifidx)
            elif peer_mac not in self._peers:
                self.add_peer(peer_mac, None, channel, ifidx)
            
            def __encode_payload():
                self.master.dprint("aen.__encode_payload")
                if payload is None: #No payload type
                    return b'\x00', b''
                elif isinstance(payload, bytearray): #bytearray
                    return b'\x01', bytes(payload)
                elif isinstance(payload, bytes): #bytes
                    return b'\x01', payload
                elif isinstance(payload, bool): #bool
                    return b'\x02', (b'\x01' if payload else b'\x00')
                elif isinstance(payload, int): #int
                    return b'\x03', struct.pack('>i', payload)
                elif isinstance(payload, float): #float
                    return b'\x04', struct.pack('>f', payload)
                elif isinstance(payload, str): #string
                    return b'\x05', payload.encode('utf-8')
                elif isinstance(payload, dict) or isinstance(payload, list): #json dict or list
                    json_payload = json.dumps(payload)
                    return b'\x06', json_payload.encode('utf-8')
                else:
                    raise ValueError("Unsupported payload type")
            
            payload_type, payload_bytes = __encode_payload()
            messages = []
            identifier = 0x2a
            timestamp = time.ticks_ms()
            header = bytearray(8)
            header[0] = identifier
            header[1] = msg_type
            header[2] = subtype
            header[3:7] = timestamp.to_bytes(4, 'big')
            if len(payload_bytes) < 242: #250-9=241=max_length
                header[7] = payload_type[0]
                total_length = 1 + 1 + 1 + 4 + 1 + len(payload_bytes) + 1
                message = bytearray(total_length)
                message[:8] = header
                message[8:-1] = payload_bytes                
                message[-1:] = (sum(message) % 256).to_bytes(1, 'big') #Checksum
                self.master.dprint(f"Message {1}/{1}; Length: {len(message)}; Free memory: {gc.mem_free()}")
                messages.append(message)

            else:
                self.master.dprint("Long message: Splitting!")
                max_size = 238 #241-3
                total_chunk_number = (-(-len(payload_bytes)//max_size)) #Round up division
                lba = b'\x07'
                header[7] = lba[0] #Long byte array
                if total_chunk_number > 256:
                    raise ValueError("More than 256 chunks, unsupported")
                for chunk_index in range(total_chunk_number):
                    message = bytearray(9 + 3 + min(max_size,len(payload_bytes)-chunk_index*max_size))
                    message[:8] = header
                    message[8:10] = chunk_index.to_bytes(1, 'big') + total_chunk_number.to_bytes(1, 'big')
                    message[10] = payload_type[0]
                    message[11:-1] = payload_bytes[chunk_index * max_size: (chunk_index + 1) * max_size]           
                    message[-1:] = (sum(message) % 256).to_bytes(1, 'big') #Checksum
                    self.master.dprint(message)
                    messages.append(bytes(message))
                    self.master.dprint(f"Message {chunk_index+1}/{total_chunk_number}; length: {len(message)}; Free memory: {gc.mem_free()}")
                    gc.collect()
#                 key = bytearray()
#                 key.extend(header[1:8])
#                 key.extend(total_chunk_number.to_bytes(1, 'big'))
#                 self._long_sent_buffer[bytes(key)] = (messages, (channel,ifidx))

            gc.collect()
            self._send(peer_mac, messages, channel, ifidx)


        def _receive(self): #Processes all the messages in the buffer
            self.master.dprint("aen._receive")
            
            def __decode_payload(payload_type, payload_bytes):
                self.master.dprint("aen.__decode_payload")
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
                    raise ValueError(f"Unsupported payload type: {payload_type} Message: {payload_bytes}")
            
            def __process_message(sender_mac, message, receive_timestamp):
                self.master.dprint("aen.__process_message")
                if message[0] != 0x2a:  # Unique Message Identifier Check
                    self.master.dprint("Invalid message: Message ID Fail")
                    return None
                if len(message) < 9:  # Min size
                    self.master.dprint("Invalid message: too short")
                    return None

                msg_type = bytes(message[1:2])
                subtype = bytes(message[2:3])
                send_timestamp = int.from_bytes(message[3:7], 'big')
                payload_type = bytes(message[7:8])
                payload = message[8:-1]
                checksum = message[-1]
                self.master.dprint(f"{type(msg_type)}: {msg_type}, {type(subtype)}: {subtype}, {type(send_timestamp)}: {send_timestamp}, {type(payload_type)}: {payload_type},  {type(payload)}: {payload},  {type(checksum)}: {checksum}")
                
                #Checksum
                if checksum != sum(message[:-1]) % 256:
                    self.master.dprint("Invalid message: checksum mismatch")
                    return None
                
                if sender_mac not in self._peers:
                    self.add_peer(sender_mac)
                
                if payload_type == b'\x07':
                    self.master.dprint("Long message received, processing...")
                    part_n = int.from_bytes(payload[0:1], 'big')
                    total_n = int.from_bytes(payload[1:2], 'big')
                    payload_type = bytes(payload[2:3])
                    payload = payload[3:]
                    
                    # Create a key as a bytearray: (msg_type, subtype, timestamp, payload_type, total_n)
                    key = bytearray()
                    key.extend(msg_type)
                    key.extend(subtype)
                    key.extend(message[3:7])
                    key.extend(payload_type)
                    key.append(total_n)
                    key = bytes(key)
                    self.master.dprint(f"Key: {key}")
                    
                    # Check if the key already exists in the long buffer
                    if key in self._long_buffer:
                        # If the part is None, add the payload
                        if self._long_buffer[key][part_n] is None:
                            self._long_buffer[key][part_n] = payload
                            self._long_buffer_size[key] = self._long_buffer_size[key] + len(payload)
                            self.master.dprint(f"Long message: Key found, message added to entry in long_message_buffer, {sum(1 for item in self._long_buffer[key] if item is not None)} out of {total_n} packages received")
                            # If there are still missing parts, return
                            if any(value is None for value in self._long_buffer[key]):
                                gc.collect()
                                return
                    else:
                        # Initialize the long message buffer for this key
                        payloads = [None] * total_n
                        payloads[part_n] = payload
                        self._long_buffer[key] = payloads
                        self._long_buffer_size[key] = len(payload)
                        self.master.dprint(f"Long message: Key not found and new entry created in long_message_buffer, {sum(1 for item in self._long_buffer[key] if item is not None)} out of {total_n} packages received")
                        
                        while len(self._long_buffer) > 8 or sum(self._long_buffer_size.values()) > 75000:
                            self.master.dprint(f"Maximum buffer size reached: {len(self._long_buffer)}, {sum(self._long_buffer_size.values())} bytes; Reducing!")
                            self._long_buffer.popitem(last=False)
                            self._long_buffer_size.popitem(last=False)
                        gc.collect()
                        return
                        
                    # If all parts have been received, reconstruct the message
                    if not any(value is None for value in self._long_buffer[key]):
                        payload = bytearray()
                        for i in range(0, total_n):
                            payload.extend(self._long_buffer[key][i])
                        del self._long_buffer[key]
                        del self._long_buffer_size[key]
                        self.master.dprint("Long message: All packages received!")
                    else:
                        self.master.dprint("Long Message: Safeguard triggered, code should not have gotten here")
                        gc.collect()
                        return
                
                #Handle the message based on type
                if msg_type == (msg_key := msg_codes["cmd"]):  # Command Message
                    __handle_cmd(sender_mac, subtype, send_timestamp, receive_timestamp, payload_type, payload if payload else None, msg_key)
                elif msg_type == (msg_key := cmsg_codes["inf"]):  # Informational Message
                    __handle_inf(sender_mac, subtype, send_timestamp, receive_timestamp, payload_type, payload if payload else None, msg_key)
                elif msg_type == (msg_key := msg_codes["ack"]):  # Acknowledgement Message
                    __handle_ack(sender_mac, subtype, send_timestamp, receive_timestamp, payload_type, payload if payload else None, msg_key)
                else:
                    self.master.iprint(f"Unknown message type from {sender_mac} ({self.peer_name(sender_mac)}): {message}")

            def __check_authorisation(sender_mac, payload):
                return sender_mac in self._whitelist or payload == "sudo" or payload[-1] == "sudo"

            def __send_confirmation(type, recipient_mac, msg_subkey_type, payload=None, error=None):
                if type == "Success":
                    self._compose(recipient_mac, [msg_subkey_type, payload], 0x03, 0x11)
                elif type == "Fail":
                    self._compose(recipient_mac, [msg_subkey_type, error, payload], 0x03, 0x12)
                else:
                    self._compose(recipient_mac, [msg_subkey_type, payload], 0x03, 0x13)

            def __handle_cmd(sender_mac, subtype, send_timestamp, receive_timestamp, payload_type, payload, msg_key):
                self.master.dprint(f"aen.__handle_cmd")
                payload = __decode_payload(payload_type, payload)
                if subtype == msg_subcodes[msg_key][msg_subkey := "Reboot"]:  # Reboot
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        __send_confirmation("Confirm", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        machine.reset()
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Firmware-Update"]: # Firmware-Update
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            # Insert update logic here
                            self.master.iprint("no update logic written just yet")
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "File-Update"]:  # File-Update
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            # Insert update logic here
                            self.master.iprint("No update logic written just yet")
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "File-Download"]: #File-Download
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    payload = __decode_payload(payload_type, payload) #should return a list with a link and the list of files to download
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            import mip
                            base = payload[0]
                            files_to_copy = payload[1]
                            for f in files_to_copy:
                                print("Installing: ", f)
                                mip.install(base + f)
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                # enable WebREPL
                elif subtype == msg_subcodes[msg_key][msg_subkey := "File-Run"]: #File-Run
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            self.master.iprint("Execute logic not implemented")
                            #insert run logic here
                        except Exception as e:
                            self.master.iprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Set-Admin"]: #Set Admin Bool
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        self.master.iprint(f"Received Set-Admin command: self.admin set to {payload[0]}")
                        try:
                            self.master.admin = payload[0]
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Whitelist-Add"]: # Whitelist-Add - Add Admin macs to _whitelist
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        self.master.iprint(f"Received add admin macs to _whitelist command, added {payload[0]} and {payload[1]}")
                        try:
                            self._whitelist.append(payload[0])
                            self._whitelist.append(payload[1])
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Config-Change"]:  # change config
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.iprint(f"Not yet implemented")
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Ping"]: #Ping
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    self.add_peer(sender_mac, payload[2], payload[0], payload[1])
                    if bool(self.ifidx):
                        channel = self.master.ap.channel()
                    else:
                        channel = self.master.sta.channel()
                    response = [channel, self.ifidx, self.master.name, send_timestamp]
                    self._compose(sender_mac, response, 0x03, 0x10)
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Pair"]: #Pair
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self._pairing:
                        try:
                            # Insert pairing logic here
                            self.master.iprint("no pairing logic written just yet")
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", "Pairing disabled", payload)
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Set-Pair"]: #Enable pairing mode
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            self._pairing = payload[0]
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "RSSI/Status/Config-Boop"]: # RSSI/Status/Config Boop
                    self.boops = self.boops + 1
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)}), Received total of {self.boops} boops!")
                    try:
                        self._compose(sender_mac, [self.master.id, self.master.name, self.master.config, self.master.version_n, self.master.version, self.master.sta.mac, self.master.ap.mac, self.rssi()], 0x02, 0x20) #[ID, Name, Config, Version, sta mac, ap mac, rssi]
                    except Exception as e:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Directory-Get"]: #Get List of Files
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    try:
                        result = []
                        entries = os.listdir()
                        for entry in entries:
                            full_path = f"{path}/{entry}"
                            if os.stat(full_path)[0] & 0x4000:
                                result.extend(list_all_paths(full_path))
                            else:
                                result.append(full_path)
                            self._compose(sender_mac, result, 0x02, 0x20)
                    except Exception as e:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Echo"]: #Echo
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)}): {__decode_payload(payload_type, payload)}") #Check i or d
                    self._compose(sender_mac, payload, 0x03, 0x15)
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Resend"]: #Resend lost long messages
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    self.master.iprint("Long_sent_buffer disabled due to memory constraints")
#                    payload = __decode_payload(payload_type, payload)
#                    self.master.iprint("Received resend long message command, checking buffer for lost message")
#                     key = payload[0:8]
#                     indexes_b = payload[8:]
#                     indexes = []
#                     for i in range(0, len(indexes_b)):
#                         indexes.append(int.from_bytes(indexes_b[i], 'big'))
#                     if key in self._long_sent_buffer:
#                         channel = self._long_sent_buffer[key][1][0]
#                         ifidx = self._long_sent_buffer[key][1][1]
#                         for index in indexes:
#                             message.append(self._long_sent_buffer[key][0][index])
#                         self._send(sender_mac, messages, channel, ifidx)
#                         #resend the message from the message buffer
#                         self.master.iprint("Resent all requested messages")
#                     else:
#                         self.master.iprint("Message not found in the buffer")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "WiFi-Connect"]: #Connect to Wi-Fi
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            self.connect(payload[0], payload[1])
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "WiFi-Disconnect"]: #Disconnect from Wi-Fi
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            self.disconnect()
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "AP-Enable"]: #Enable AP
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            ssid = payload[0]
                            if ssid == "":
                                ssid = self.master.name
                            password = payload[1]
                            self.setap(ssid, password)
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "AP-Disable"]: #Disable AP
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    payload = __decode_payload(payload_type, payload) #should return a list of desired name, password and max clients
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            self.master.ap.deactivate()
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Pause"]: #Set Pause
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            self.master.iprint(f"Received pause command: {payload[0]}")
                            self._running = False
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                            if self._pause_function:
                                self._pause_function() #calls the custom set pause function to display a screen
                            while not self._running:
                                sleep(0.5)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Continue"]: #Set Continue
                    self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                    if self.__check_authorisation(sender_mac, payload):
                        try:
                            self.master.iprint(f"Received continue command: {payload}")
                            self.master._running = True
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                else:
                    self.master.iprint(f"Unknown command subtype from {sender_mac} ({self.peer_name(sender_mac)}): {subtype}")

            def __handle_inf(sender_mac, subtype, send_timestamp, receive_timestamp, payload_type, payload, msg_key):
                self.master.dprint("aen.__handle_inf")
                payload = __decode_payload(payload_type, payload)
                if subtype == msg_subcodes[msg_key][msg_subkey := "RSSI"]: #RSSI
                    #payload["time_sent"] = send_timestamp
                    #payload["time_recv"] = receive_timestamp
                    self.master.iprint(f"{msg_subkey} ({subtype}) data received from {sender_mac} ({self.peer_name(sender_mac)}): {payload}")
                    self.received_rssi_data[sender_mac] = payload
                    #__send_confirmation("Confirm", sender_mac, f"{msg_subkey} ({subtype})", payload) #confirm message recv
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Sensor"]: #Sensor Data
                    payload["time_sent"] = send_timestamp
                    payload["time_recv"] = receive_timestamp
                    self.master.iprint(f"{msg_subkey} ({subtype}) data received from {sender_mac} ({self.peer_name(sender_mac)}): {payload}")
                    self.received_sensor_data[sender_mac] = payload
                    #__send_confirmation("Confirm", sender_mac, f"{msg_subkey} ({subtype})", payload) #confirm message recv
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Message"]: #Message / Other
                    self.master.iprint(f"{msg_subkey} ({subtype}) received from {sender_mac} ({self.peer_name(sender_mac)}): {payload}")
                    self._received_messages.append((sender_mac, payload, receive_timestamp))
                    self._received_messages_size.append(len(payload))
                    while len(self._received_messages) > 2048 or sum(self._received_messages_size) > 20000:
                        self.master.dprint(f"Maximum buffer size reached: {len(self._received_messages)}, {sum(self._received_messages_size)} bytes; Reducing!")
                        self._received_messages.pop(0)
                        self._received_messages_size.pop(0)
                    #__send_confirmation("Confirm", sender_mac, f"{msg_subkey} ({subtype})", payload) #confirm message recv
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Directory"]: #File Directory
                    self.master.iprint(f"{msg_subkey} ({subtype}) data received from {sender_mac} ({self.peer_name(sender_mac)}): {payload}")
                    #__send_confirmation("Confirm", sender_mac, f"{msg_subkey} ({subtype})", payload) #confirm message recv
                else:
                    self.master.iprint(f"Unknown info subtype from {sender_mac} ({self.peer_name(sender_mac)}): {subtype}")
                    
            def __handle_ack(sender_mac, subtype, send_timestamp, receive_timestamp, payload_type, payload, msg_key):
                self.master.dprint("aen.__handle_ack")
                payload = __decode_payload(payload_type, payload)
                if subtype == msg_subcodes[msg_key][msg_subkey := "Pong"]: #Pong
                    self.add_peer(sender_mac, payload[2], payload[0], payload[1])
                    self.master.iprint(f"{msg_subkey} ({subtype})  received from {sender_mac} ({self.peer_name(sender_mac)}), {receive_timestamp-info[3]}")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Echo"]: #Echo
                    self.master.iprint(f"{msg_subkey} ({subtype})  received from {sender_mac} ({self.peer_name(sender_mac)}), {__decode_payload(payload_type, payload)}")
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Success"]: #Success
                    # payload should return a list with a cmd type and payload
                    self.master.iprint(f"Cmd {msg_subkey} ({subtype}) received from {sender_mac} ({self.peer_name(sender_mac)}) for type {payload[0]} with payload {payload[1]}")
                    #add to ack buffer
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Fail"]: #Fail
                    # payload should return a list with a cmd type, error and payload
                    self.master.iprint(f"Cmd {msg_subkey} ({subtype}) received from {sender_mac} ({self.peer_name(sender_mac)}) for type {payload[0]} with error {payload[1]} and payload {payload[2]}")
                    #add to ack buffer
                elif subtype == msg_subcodes[msg_key][msg_subkey := "Confirm"]: #Confirmation
                    # payload should return a list with message type and payload
                    self.master.iprint(f"{msg_subkey} ({subtype}) received from {sender_mac} ({self.peer_name(sender_mac)}) for type {payload[0]} with payload {payload[1]}")
                    #add to ack buffer
                else:
                    self.master.iprint(f"Unknown ack subtype from {sender_mac} ({self.peer_name(sender_mac)}): {subtype}, Payload: {payload}")
                # Insert more acknowledgement logic here and/or add message to acknowledgement buffer

            if self._aen.any(): 
                for mac, data in self._aen:
                    self.master.dprint(f"Received {mac, data}")
                    if mac is None: # mac, msg will equal (None, None) on timeout
                        break
                    if data:
                        if mac and data is not None:
                            #self._received_messages.append((sender_mac, data, receive_timestamp))#Messages will be saved here, this is only for debugging purposes
                            __process_message(mac, data, time.ticks_ms())
                    if not self._aen.any():#this is necessary as the for loop gets stuck and does not exit properly.
                        break


#message structure (what kind of message types do I need?: Command which requires me to do something (ping, pair, change state(update, code, mesh mode, run a certain file), Informational Message (Sharing Sensor Data and RSSI Data)
#| Header (1 byte) | Type (1 byte) | Subtype (1 byte) | Timestamp(ms ticks) (4 bytes) | Payload type (1) | Payload (variable) | Checksum (1 byte) |