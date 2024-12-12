from config import mysecrets, config, whitelist, i2c_dict, version, msg_codes, msg_subcodes, networking_keys
from networking import Networking
import ubinascii
import machine
import time
import os
import gc
import webrepl


class SSP_Networking:
    def __init__(self, infmsg=False, dbgmsg=False, errmsg=False, admin=False, inittime=time.ticks_ms()):
        if infmsg:
            print(f"{(time.ticks_ms() - inittime) / 1000:.3f} Initialising Smart System Education Platform Networking")
        self.networking = Networking(infmsg, dbgmsg, errmsg, admin, inittime)
        config["id"] = ubinascii.hexlify(machine.unique_id()).decode()
        config["version"] = ''.join(str(value) for value in version.values())
        config["ap_mac"] = self.networking.ap.mac()
        config["sta_mac"] = self.networking.sta.mac()
        self.networking.config = config
        self.config = self.networking.config
        self.version = version
        self.commands = self.Commands(self)
        self.orders = self.Orders(self)
        self.inittime = self.networking.inittime
        
    def rssi(self):
        return self.networking.aen.rssi()
    
    def peers(self):
        return self.networking.aen.peers()
    
    def irq(self, func):
        self.networking.aen.irq(func)
    
    def check_messages(self):
        return self.networking.aen.check_messages()

    def return_message(self):
        return self.networking.aen.return_message()
    
    def return_messages(self):
        return self.networking.aen.return_messages()
    
    def cleanup(self):
        self.networking.cleanup()
    
    class Commands:
        def __init__(self, master):
            self.master = master

        def send_command(self, msg_subkey, mac, payload=None, channel=None, ifidx=None, sudo=False):
            self.master.dprint("aen.send_command")
            if sudo and isinstance(payload, list):
                payload.append("sudo")
            elif sudo and payload is None:
                payload = ["sudo"]
            else:
                payload = [payload, "sudo"]
            if (msg_key := "cmd") and msg_subkey in msg_subcodes[msg_key]:
                self.master.networking.iprint(f"Sending {msg_subkey} ({bytes([msg_subcodes[msg_key][msg_subkey]])}) command to {mac} ({self.master.networking.aen.peer_name(mac)})")
                self.master.networking.aen.send_command(msg_codes[msg_key], msg_subcodes[msg_key][msg_subkey], mac, payload, channel, ifidx)
            else:
                self.master.iprint(f"Command {msg_subkey} not found")
            gc.collect()

        def ping(self, mac, channel=None, ifidx=None):
            self.master.networking.dprint("net.cmd.ping")
            self.master.networking.aen.ping(mac, channel, ifidx)

        def echo(self, mac, message, channel=None, ifidx=None):
            self.master.networking.dprint("net.cmd.echo")
            self.master.networking.aen.echo(mac, message, channel, ifidx)

        def boop(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.boop")
            self.master.networking.aen.boop(mac, channel, ifidx, sudo)

        def send(self, mac, message, channel=None, ifidx=None):
            self.master.networking.dprint("net.cmd.message")
            self.master.networking.aen.send(mac, message, channel, ifidx)

        def broadcast(self, message, channel=None, ifidx=None):
            self.master.networking.dprint("net.cmd.broadcast")
            mac = b'\xff\xff\xff\xff\xff\xff'
            self.send(mac, message, channel, ifidx)

        def send_data(self, mac, message, channel=None,ifidx=None):  # message is a dict, key is the sensor type and the value is the sensor value
            self.master.networking.dprint("net.cmd.message")
            self.master.networking.aen.send_data(mac, message, channel, ifidx)

        def reboot(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.reboot")
            self.master.networking.aen.send_command("Reboot", mac, None, channel, ifidx, sudo)

        def firmware_update(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.firmware_update")
            self.master.networking.aen.send_command("Firmware-Update", mac, None, channel, ifidx, sudo)

        def file_update(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.file_update")
            self.master.networking.aen.send_command("File-Update", mac, None, channel, ifidx, sudo)

        def file_download(self, mac, link, file_list=None, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.file_download")
            self.master.networking.aen.send_command("File-Download", mac, [link, file_list], channel, ifidx, sudo)

        def web_repl(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.web_repl")
            self.master.networking.ap.set_ap(ap_name := self.master.networking.config["name"], password := networking_keys["default_ap_key"])
            self.master.networking.aen.send_command("Web-Repl", mac, [ap_name, password], channel, ifidx, sudo)
            # await success message and if success False disable AP or try again

        def file_run(self, mac, filename, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.file_run")
            self.master.networking.aen.send_command("File-Run", mac, filename, channel, ifidx, sudo)

        def admin_set(self, mac, new_bool, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.admin_set")
            self.master.networking.aen.send_command("Admin-Set", mac, new_bool, channel, ifidx, sudo)

        def whitelist_add(self, mac, mac_list=None, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.whitelist_add")
            if mac_list is not None:
                mac_list = [self.master.networking.sta.mac, self.master.networking.ap.mac]
            self.master.networking.aen.send_command("Whitelist-Add", mac, mac_list, channel, ifidx, sudo)

        def config_change(self, mac, new_config, hardcode=False, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.config_change")
            self.master.networking.aen.send_command("Config-Change", mac, [new_config, hardcode], channel, ifidx, sudo)

        def name_change(self, mac, new_name, hardcode=False, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.name_change")
            self.master.networking.aen.send_command("Name-Change", mac, [new_name, hardcode], channel, ifidx, sudo)

        def pair(self, mac, key=networking_keys["handshake_key1"], channel=None, ifidx=None):
            self.master.networking.dprint("net.cmd.pair")
            self.master.networking.aen.send_command("Pair", mac, key, channel, ifidx)

        def pair_enable(self, mac, pair_bool, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.pair")
            self.master.networking.aen.send_command("Set-Pair", mac, pair_bool, channel, ifidx, sudo)

        def directory_get(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.directory_get")
            self.master.networking.aen.send_command("Directory-Get", mac, None, channel, ifidx, sudo)

        # resend cmd

        def wifi_connect(self, mac, name, password, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.wifi_connect")
            self.master.networking.aen.send_command("Wifi-Connect", mac, [name, password], channel, ifidx, sudo)

        def wifi_disconnect(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.wifi_disconnect")
            self.master.networking.aen.send_command("Wifi-Disconnect", mac, None, channel, ifidx, sudo)

        def ap_enable(self, mac, name, password, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.ap_enable")
            self.master.networking.aen.send_command("AP-Enable", mac, [name, password], channel, ifidx, sudo)

        def ap_disable(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.ap_disable")
            self.master.networking.aen.send_command("AP-Disable", mac, None, channel, ifidx, sudo)

        def pause(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.pause")
            self.master.networking.aen.send_command("Pause", mac, None, channel, ifidx, sudo)

        def resume(self, mac, channel=None, ifidx=None, sudo=False):
            self.master.networking.dprint("net.cmd.resume")
            self.master.networking.aen.send_command("Resume", mac, None, channel, ifidx, sudo)


    class Orders:
        def __init__(self, master):
            self.master = master
            self.master.networking.dprint("net.cmd.orders")
            self._whitelist = whitelist

            self._pause_function = None

            # Flags
            self._pairing_enabled = True
            self._pairing = False
            self._paired = False
            self._paired_macs = []
            self._running = True

            def __check_authorisation(sender_mac, payload):
                return sender_mac in self._whitelist or payload == "sudo" or payload[-1] == "sudo"

            def __send_confirmation(msg_type, recipient_mac, msg_subkey_type, payload=None, error=None):
                self.master.networking.dprint("net.order.__send_confirmation")
                self.master.networking.aen.__send_confirmation(msg_type, recipient_mac, msg_subkey_type, payload, error)

            def custom_cmd_handler(sender_mac, subtype, send_timestamp, receive_timestamp, payload, msg_key):
                self.master.networking.dprint("net.order.custom_cmd_handler")
                if (msg_subkey := "Reboot") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Reboot
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        __send_confirmation("Confirm", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        machine.reset()
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Firmware-Update") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Firmware-Update
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            # Insert update logic here
                            self.master.iprint("no update logic written just yet")
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.eprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "File-Update") and subtype == msg_subcodes[msg_key][msg_subkey]:  # File-Update
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            # Insert update logic here
                            self.master.iprint("No update logic written just yet")
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.eprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "File-Download") and subtype == msg_subcodes[msg_key][msg_subkey]:  # File-Download
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    # should return a list with a link and the list of files to download
                    if __check_authorisation(sender_mac, payload):
                        try:
                            # import mip
                            # base = payload[0]
                            # files_to_copy = payload[1]
                            # if files_to_copy is None:
                            #     mip.install(base)
                            # else:
                            #     for f in files_to_copy:
                            #         mip.install(base + f)
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.eprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Web-Repl") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Web-Repl
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    # should be a list with name and password
                    if __check_authorisation(sender_mac, payload):
                        try:
                            # add logic to connect to Wi-Fi and set up webrepl
                            webrepl.start()
                            self.master.sta.connect(payload[0], payload[1])
                            link = "webrepl link"
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", link)
                        except Exception as e:
                            self.master.eprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "File-Run") and subtype == msg_subcodes[msg_key][msg_subkey]:  # File-Run
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.iprint("Execute logic not implemented")
                            # insert run logic here
                        except Exception as e:
                            self.master.eprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Set-Admin") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Set Admin Bool
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        self.master.iprint(f"Received Set-Admin command: self.admin set to {payload[0]}")
                        try:
                            self.master.admin = payload[0]
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Whitelist-Add") and subtype == msg_subcodes[msg_key][
                    msg_subkey]:  # Whitelist-Add - Add Admin macs to _whitelist
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        self.master.iprint(
                            f"Received add admin macs to _whitelist command, added {payload[0]} and {payload[1]}")
                        try:
                            self._whitelist.append(payload[0])
                            self._whitelist.append(payload[1])
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Config-Change") and subtype == msg_subcodes[msg_key][msg_subkey]:  # change config
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.config["configuration"] = payload[0]
                            if payload[1]:
                                file_path = "config.py"
                                with open(file_path, "r") as f:
                                    lines = f.readlines()
                                with open(file_path, "w") as f:
                                    for line in lines:
                                        if line.startswith('    "configuration": '):
                                            f.write(f'    "configuration": "{payload[0]}",\n')
                                        else:
                                            f.write(line)
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Name-Change") and subtype == msg_subcodes[msg_key][msg_subkey]:  # change name
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.config["name"] = payload[0]
                            if payload[1]:
                                file_path = "config.py"
                                with open(file_path, "r") as f:
                                    lines = f.readlines()
                                with open(file_path, "w") as f:
                                    for line in lines:
                                        if line.startswith('    "name": '):
                                            f.write(f'    "name": "{payload[0]}"\n')
                                        else:
                                            f.write(line)
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Ping") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Ping
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    self.master.networking.aen.add_peer(sender_mac, payload[2]["name"], payload[2]["id"], payload[2]["configuration"],
                                  payload[2]["version"], payload[0], payload[1])
                    if bool(self.master.networking.aen.ifidx):
                        channel = self.master.ap.channel()
                    else:
                        channel = self.master.sta.channel()
                    response = [channel, self.master.networking.aen.ifidx, self.master.config, send_timestamp]
                    self.master.networking.aen.send_command(0x03, 0x10, sender_mac, response)
                #                 elif (msg_subkey := "Pair") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Pair #add something that checks that the messages are from the same mac # BREAKS NETWORK
                #                     self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                #                     if self._pairing_enabled and networking_keys["handshake_key_1"] == payload:
                #                         self._pairing = True
                #                         self.pair(sender_mac, networking_keys["handshake_key_2"])
                #                         # some timer for if key 3 is not received to reset states
                #                     elif self._pairing_enabled and self._pairing and networking_keys["handshake_key_2"] == payload:
                #                         self._paired = True
                #                         self._paired_macs.append(sender_mac)
                #                         self.pair(sender_mac, networking_keys["handshake_key_3"])
                #                         # some timer that sets to false if key 4 is not received
                #                     elif self._pairing_enabled and self._pairing and networking_keys["handshake_key_3"] == payload:
                #                         try:
                #                             # Insert pairing logic here do a reverse handshake
                #                             self._paired = True
                #                             self._paired_macs.append(sender_mac)
                #                             self.pair(sender_mac, networking_keys["handshake_key_4"])
                #                             self.master.iprint("no pairing logic written just yet")
                #                             __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                #                         except Exception as e:
                #                             self.master.eprint(f"Error: {e} with payload: {payload}")
                #                             __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                #                     elif self._pairing_enabled and self._pairing and networking_keys["handshake_key_3"] == payload:
                #                         self._paired = True
                #                         # remove timer from before
                #                     else:
                #                         __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", "Pairing disabled", payload)
                #                 elif (msg_subkey := "Set-Pair") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Enable pairing mode
                #                     self.master.iprint(f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.peer_name(sender_mac)})")
                #                     if __check_authorisation(sender_mac, payload):
                #                         try:
                #                             self._pairing_enabled = payload[0]
                #                             __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                #                         except Exception as e:
                #                             self.master.eprint(f"Error: {e} with payload: {payload}")
                #                             __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                #                     else:
                #                         __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "RSSI/Status/Config-Boop") and subtype == msg_subcodes[msg_key][
                    msg_subkey]:  # RSSI/Status/Config Boop
                    self.boops = self.boops + 1
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)}), Received total of {self.boops} boops!")
                    try:
                        self.master.networking.aen.send_command(0x02, 0x20, sender_mac,[self.master.config, self.master.version, self.master.sta.mac, self.master.ap.mac, self.master.networking.aen.rssi()])  # [ID, Name, Config, Version, sta mac, ap mac, rssi]
                    except Exception as e:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                elif (msg_subkey := "Directory-Get") and subtype == msg_subcodes[msg_key][
                    msg_subkey]:  # Get List of Files # BREAKS NETWORK
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    try:
                        def ___list_all_files(path):
                            result = []
                            entries = os.listdir(path)
                            for entry in entries:
                                full_path = path + "/" + entry
                                try:
                                    if os.stat(full_path)[0] & 0x4000:
                                        result.extend(___list_all_files(full_path))
                                    else:
                                        result.append(full_path)
                                except OSError:
                                    # Handle inaccessible files or directories
                                    continue
                            return result

                        start_path = '.'
                        all_files = ___list_all_files(start_path)
                        self.master.networking.aen.send_command(0x02, 0x20, sender_mac, all_files)
                    except Exception as e:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                elif (msg_subkey := "Echo") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Echo
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)}): {payload}")  # Check i or d
                    self.master.networking.aen.send_command(0x03, 0x15, sender_mac, payload)
                elif (msg_subkey := "Resend") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Resend lost long messages
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    self.master.iprint("Long_sent_buffer disabled due to memory constraints")
                elif (msg_subkey := "WiFi-Connect") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Connect to Wi-Fi
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.sta.connect(payload[0], payload[1])
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.eprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "WiFi-Disconnect") and subtype == msg_subcodes[msg_key][
                    msg_subkey]:  # Disconnect from Wi-Fi
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.sta.disconnect()
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.eprint(f"Error: {e}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "AP-Enable") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Enable AP
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            ssid = payload[0]
                            if ssid == "":
                                ssid = self.master.config["name"]
                            password = payload[1]
                            self.master.ap.setap(ssid, password)
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.eprint(f"Error: {e} with payload: {payload}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "AP-Disable") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Disable AP
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.ap.deactivate()
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            self.master.iprint(f"Error: {e}")
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Pause") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Set Pause
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.iprint(f"Received pause command: {payload[0]}")
                            self._running = False
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                            if self._pause_function:
                                self._pause_function()  # calls the custom set pause function to display a screen
                            while not self._running:
                                time.sleep(0.5)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                elif (msg_subkey := "Resume") and subtype == msg_subcodes[msg_key][msg_subkey]:  # Set Continue
                    self.master.iprint(
                        f"{msg_subkey} ({subtype}) command received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)})")
                    if __check_authorisation(sender_mac, payload):
                        try:
                            self.master.iprint(f"Received continue command: {payload}")
                            self.master._running = True
                            __send_confirmation("Success", sender_mac, f"{msg_subkey} ({subtype})", payload)
                        except Exception as e:
                            __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, e)
                    else:
                        __send_confirmation("Fail", sender_mac, f"{msg_subkey} ({subtype})", payload, "Not authorised")
                else:
                    self.master.iprint(
                        f"Unknown command subtype from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)}): {subtype}")

            def custom_inf_handler(sender_mac, subtype, send_timestamp, receive_timestamp, payload, msg_key):
                self.master.networking.dprint("net.order.custom_inf_handler")
                if (msg_subkey := "Directory") and subtype == msg_subcodes[msg_key][msg_subkey]:  # File Directory
                    self.master.iprint(f"{msg_subkey} ({subtype}) data received from {sender_mac} ({self.master.networking.aen.peer_name(sender_mac)}): {payload}")
                    # __send_confirmation("Confirm", sender_mac, f"{msg_subkey} ({subtype})", payload) #confirm message recv


            def custom_ack_handler(sender_mac, subtype, send_timestamp, receive_timestamp, payload, msg_key):
                self.master.networking.dprint("net.order.custom_ack_handler")

            self.master.networking.aen.cmd(custom_cmd_handler)
            self.master.networking.aen.inf(custom_inf_handler)
            self.master.networking.aen.ack(custom_ack_handler)