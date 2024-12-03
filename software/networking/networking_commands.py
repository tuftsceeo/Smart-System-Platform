class Commands:
    def __init__(self, networking):
        self.master = networking
        self.aen = networking.aen
    
    def ping(self, mac, channel=None, ifidx=None):
        self.master.dprint("net.cmd.ping")
        self.aen.ping(mac, channel, ifidx)
    
    def echo(self, mac, message, channel=None, ifidx=None):
        self.master.dprint("net.cmd.echo")
        self.aen.echo(mac, message, channel, ifidx)
        
    def boop(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("aen.boop")
        self.aen.boop(mac, channel, ifidx, sudo)
    
    def send(self, mac, message, channel=None, ifidx=None):
        self.master.dprint("net.cmd.message")
        self.aen.send(mac, message, channel, ifidx)

    def broadcast(self, message, channel=None, ifidx=None):
        self.master.dprint("net.cmd.broadcast")
        mac = b'\xff\xff\xff\xff\xff\xff'
        self.send(mac, message, channel, ifidx)

    def send_sensor(self, mac, message, channel=None,ifidx=None):  # message is a dict, key is the sensor type and the value is the sensor value
        self.master.dprint("net.cmd.message")
        
    
    

    def reboot(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.reboot")
        self.aen.send_command("Reboot", mac, None, channel, ifidx, sudo)

    def firmware_update(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.firmware_update")
        self.aen.send_command("Firmware-Update", mac, None, channel, ifidx, sudo)

    def file_update(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.file_update")
        self.aen.send_command("File-Update", mac, None, channel, ifidx, sudo)

    def file_download(self, mac, link, file_list=None, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.file_download")
        self.aen.send_command("File-Download", mac, [link, file_list], channel, ifidx, sudo)

    def web_repl(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.web_repl")
        self.master.ap.set_ap(ap_name := self.master.config["name"], password := networking_keys["default_ap_key"])
        self.aen.send_command("Web-Repl", mac, [ap_name, password], channel, ifidx, sudo)
        # await success message and if success False disable AP or try again

    def file_run(self, mac, filename, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.file_run")
        self.aen.send_command("File-Run", mac, filename, channel, ifidx, sudo)

    def admin_set(self, mac, new_bool, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.admin_set")
        self.aen.send_command("Admin-Set", mac, new_bool, channel, ifidx, sudo)

    def whitelist_add(self, mac, mac_list=None, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.whitelist_add")
        if mac_list is not None:
            mac_list = [self.master.sta.mac, self.master.ap.mac]
        self.aen.send_command("Whitelist-Add", mac, mac_list, channel, ifidx, sudo)

    def config_change(self, mac, new_config, hardcode=False, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.config_change")
        self.aen.send_command("Config-Change", mac, [new_config, hardcode], channel, ifidx, sudo)
        
    def reboot(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.reboot")
        self.aen.send_command("Reboot", mac, None, channel, ifidx, sudo)

    def firmware_update(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.firmware_update")
        self.aen.send_command("Firmware-Update", mac, None, channel, ifidx, sudo)

    def file_update(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.file_update")
        self.aen.send_command("File-Update", mac, None, channel, ifidx, sudo)

    def file_download(self, mac, link, file_list=None, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.file_download")
        self.aen.send_command("File-Download", mac, [link, file_list], channel, ifidx, sudo)

    def web_repl(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.web_repl")
        self.master.ap.set_ap(ap_name := self.master.config["name"], password := networking_keys["default_ap_key"])
        self.aen.send_command("Web-Repl", mac, [ap_name, password], channel, ifidx, sudo)
        # await success message and if success False disable AP or try again

    def file_run(self, mac, filename, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.file_run")
        self.aen.send_command("File-Run", mac, filename, channel, ifidx, sudo)

    def admin_set(self, mac, new_bool, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.admin_set")
        self.aen.send_command("Admin-Set", mac, new_bool, channel, ifidx, sudo)

    def whitelist_add(self, mac, mac_list=None, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.whitelist_add")
        if mac_list is not None:
            mac_list = [self.master.sta.mac, self.master.ap.mac]
        self.aen.send_command("Whitelist-Add", mac, mac_list, channel, ifidx, sudo)

    def config_change(self, mac, new_config, hardcode=False, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.config_change")
        self.aen.send_command("Config-Change", mac, [new_config, hardcode], channel, ifidx, sudo)
        
    def name_change(self, mac, new_name, hardcode=False, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.name_change")
        self.aen.send_command("Name-Change", mac, [new_name, hardcode], channel, ifidx, sudo)

    def pair(self, mac, key=networking_keys["handshake_key1"], channel=None, ifidx=None):
        self.master.dprint("net.cmd.pair")
        self.aen.send_command("Pair", mac, key, channel, ifidx)

    def pair_enable(self, mac, pair_bool, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.pair")
        self.aen.send_command("Set-Pair", mac, pair_bool, channel, ifidx, sudo)

    def directory_get(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.directory_get")
        self.aen.send_command("Directory-Get", mac, None, channel, ifidx, sudo)
        
    # resend cmd

    def wifi_connect(self, mac, name, password, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.wifi_connect")
        self.aen.send_command("Wifi-Connect", mac, [name, password], channel, ifidx, sudo)

    def wifi_disconnect(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.wifi_disconnect")
        self.aen.send_command("Wifi-Disconnect", mac, None, channel, ifidx, sudo)

    def ap_enable(self, mac, name, password, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.ap_enable")
        self.aen.send_command("AP-Enable", mac, [name, password], channel, ifidx, sudo)

    def ap_disable(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.ap_disable")
        self.aen.send_command("AP-Disable", mac, None, channel, ifidx, sudo)

    def pause(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.pause")
        self.aen.send_command("Pause", mac, None, channel, ifidx, sudo)

    def resume(self, mac, channel=None, ifidx=None, sudo=False):
        self.master.dprint("net.cmd.resume")
        self.aen.send_command("Resume", mac, None, channel, ifidx, sudo)


