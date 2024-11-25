mysecrets = {"SSID": "Tufts_Robot", "key" : ""}
msg_codes = {"cmd": b'\x01', "inf": b'\x01', "ack": b'\x01'}
msg_subcodes = {"cmd": {"Reboot": b'\x00', "Firmware-Update": b'\x01', "File-Update": b'\x02', "File-Download": b'\x03', "File-Run": b'\x05', "Set-Admin": b'\x06', "Whitelist-Add": b'\x07', "Config-Change": b'\x08', "Ping": b'\x10', "Pair": b'\x11', "Set-Pair": b'\x12', "RSSI/Status/Config-Boop": b'\x13', "Directory-Get": b'\x14', "Echo": b'\x15', "Resend": b'\x16', "WiFi-Connect": b'\x21', "WiFi-Disconnect": b'\x22', "AP-Enable": b'\x23', "AP-Disable": b'\x24', "Pause": b'\x25', "Continue": b'\x26'}, "inf": {"RSSI": b'\x20', "Sensor": b'\x21', "Message": b'\x22', "Directory": b'\x23'}, "ack": {"Pong": b'\x10', "Success": b'\x11', "Fail": b'\x12', "Confirm": b'\x13', "Echo": b'\x15'}}
configname = "Nickname"
config = "AdminModuleConfig"
whitelist = [b'd\xe83\x84\xd8\x18',b'd\xe83\x84\xd8\x19',b'd\xe83\x85\xd3\xbc', b'd\xe83\x85\xd3\xbd', b'd\xe83\x84\xd8\x18', b'd\xe83\x84\xd8\x19'] #each ESP32 has two MAC addresses
i2c_dict = {"0x3C": ["pca9685", 0, "screen"], "0x53" : ["ACCEL", 1, "accelerometer"]} #key is i2c address: ["device name", Output (0) or Input (1), "Description"]
version={"adxl345":3,"files":2, "icons":2, "motor":4, "main":0, "networking":0, "prefs":2, "sensors":4, "servo":2, "ssd1306":2} #motor used to be main