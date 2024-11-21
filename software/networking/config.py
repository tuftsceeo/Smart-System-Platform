mysecrets = {"SSID": "Tufts_Robot", "key" : ""}
codes = {"0": b'PairingCodePhrase', "1": b'PairingResponsePhrase', "2": b'PairingConfirmationPhrase'}
configname = "Nickname"
config = "AdminModuleConfig"
whitelist = [b'd\xe83\x84\xd8\x18',b'd\xe83\x84\xd8\x19',b'd\xe83\x85\xd3\xbc', b'd\xe83\x85\xd3\xbd', b'd\xe83\x84\xd8\x18', b'd\xe83\x84\xd8\x19'] #each ESP32 has two MAC addresses
i2c_dict = {"0x3C": ["pca9685", 0, "screen"], "0x53" : ["ACCEL", 1, "accelerometer"]} #key is i2c address: ["device name", Output (0) or Input (1), "Description"]
version={"adxl345":3,"files":2, "icons":2, "motor":4, "main":0, "networking":0, "prefs":2, "sensors":4, "servo":2, "ssd1306":2} #motor used to be main