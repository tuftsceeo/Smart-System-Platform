config = {"name": "Nickname", "configuration": "AM1", "id": None, "version": None, "sta_channel": None, "ap_channel": None}
version = {'adxl345.py': 3,
            'splat.py': 1,
            'sp1.py': 2,
            'hm3.py': 2,
            'am1.py': 1,
            'ssp_networking.py': 4,
            'files.py': 2,
            'icons.py': 2,
            'prefs.py': 2,
            'sensors.py': 4,
            'servo.py': 2,
            'ssd1306.py': 2,
            'sm3.py': 1,
            'sl1.py': 1,
            'smartlight.py': 1,
            'networking.py': 6,
            'boot.py': 0
            }
mysecrets = {"SSID": "Tufts_Robot", "key": ""}
msg_codes = {"cmd": 0x01, "inf": 0x02, "ack": 0x03}
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
        "Name-Change": 0x09,
        "Ping": 0x10,
        "Pair": 0x11,
        "Set-Pair": 0x12,
        "RSSI/Status/Config-Boop": 0x13,
        "Directory-Get": 0x14,
        "Echo": 0x15,
        "Resend": 0x16,
        "Hive-Set": 0x17,
        "Hive-Configure": 0x18,
        "Web-Repl": 0x20,
        "WiFi-Connect": 0x21,
        "WiFi-Disconnect": 0x22,
        "AP-Enable": 0x23,
        "AP-Disable": 0x24,
        "Pause": 0x25,
        "Resume": 0x26,
    },
    "inf": {
        "RSSI/Status/Config-Boop": 0x20,
        "Data": 0x21,
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
whitelist = [b'd\xe83\x84\xd8\x18', b'd\xe83\x84\xd8\x19',
             b'd\xe83\x85\xd3\xbc', b'd\xe83\x85\xd3\xbd',
             b'd\xe83\x84\xd8\x18', b'd\xe83\x84\xd8\x19']  #each ESP32 has two MAC addresses
i2c_dict = {
    "0x3C": ["pca9685", 0, "screen"],
    "0x53": ["ACCEL", 1, "accelerometer"]
}  #key is i2c address: ["device name", Output (0) or Input (1), "Description"]
sensor_dict = {"sensor": [0,4095], "potentiometer": [0,180], "select": [0,1], "up": [0,1], "down": [0,1], "button": [0,1], "sw1": [0,1],  "sw2": [0,1],  "sw3": [0,1],  "sw4": [0,1]}
hive_config = {"hive": False, "refreshrate": 0, "recipients": [], "sender_sensor_list": [], "mode": None}


