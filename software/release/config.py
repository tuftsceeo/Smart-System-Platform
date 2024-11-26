mysecrets = {"SSID": "Tufts_Robot", "key": ""}
msg_codes = {"cmd": 0x01, "inf": 0x01, "ack": 0x01}
msg_subcodes = {
    "cmd": {
        "Reboot": 0x00,
        "Firmware-Update": 0x01,
        "File-Update": 0x02,
        "File-Download": 0x03,
        "File-Run": 0x05,
        "Set-Admin": 0x06,
        "Whitelist-Add": 0x07,
        "Config-Change": 0x08,
        "Ping": 0x10,
        "Pair": 0x11,
        "Set-Pair": 0x12,
        "RSSI/Status/Config-Boop": 0x13,
        "Directory-Get": 0x14,
        "Echo": 0x15,
        "Resend": 0x16,
        "WiFi-Connect": 0x21,
        "WiFi-Disconnect": 0x22,
        "AP-Enable": 0x23,
        "AP-Disable": 0x24,
        "Pause": 0x25,
        "Resume": 0x26,
    },
    "inf": {
        "RSSI": 0x20,
        "Sensor": 0x21,
        "Message": 0x22,
        "Directory": 0x23,
    },
    "ack": {
        "Pong": 0x10,
        "Success": 0x11,
        "Fail": 0x12,
        "Confirm": 0x13,
        "Echo": 0x15,
    },
}
networking_keys = {
    "default_handshake_key": "handshake",
    "handshake_key1": "handshake1",
    "handshake_key2": "handshake2",
    "handshake_key3": "handshake3",
    "handshake_key4": "handshake4",
    "default_ap_key": "password",
    "default_wifi_key": "password"
}
configname = "Nickname"
config = "AdminModuleConfig"
whitelist = [b'd\xe83\x84\xd8\x18', b'd\xe83\x84\xd8\x19',
             b'd\xe83\x85\xd3\xbc', b'd\xe83\x85\xd3\xbd',
             b'd\xe83\x84\xd8\x18', b'd\xe83\x84\xd8\x19']  #each ESP32 has two MAC addresses
i2c_dict = {
    "0x3C": ["pca9685", 0, "screen"],
    "0x53": ["ACCEL", 1, "accelerometer"]
}  #key is i2c address: ["device name", Output (0) or Input (1), "Description"]
version = {"adxl345": 3, "files": 2, "icons": 2, "motor": 4, "main": 0, "networking": 0, "prefs": 2, "sensors": 4, "servo": 2, "ssd1306": 2}  # motor used to be main
