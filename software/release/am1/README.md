

# Smart System Education Platform

## Location: /work/Smart-System-Platform/Smart-System-Platform/software/release/am1/README.qmd

### Description

This directory hosts release ready code for the am1 module.

### Directories & Files

The repository has the following directory tree.

    .
    ├── README.md
    ├── README.qmd
    ├── README.rmarkdown
    ├── adxl345.py
    ├── am1.py
    ├── boot.py
    ├── config.py
    ├── files.py
    ├── hm3.py
    ├── icons.py
    ├── main.py
    ├── networking.py
    ├── sensors.py
    ├── servo.py
    ├── sl1.py
    ├── sm3.py
    ├── smartlight.py
    ├── smartmotor.py
    ├── sp1.py
    ├── splat.py
    ├── ssd1306.py
    ├── ssp_networking.py
    └── variableLED.py

A short description of the directories can be found below.

| name | description | contribution |
|----|----|----|
| release/config.py | Smart Module Configuration File | Nick |
| main/boot.py | Smart Module boot.py | Nick |
| main/am1.py | Admin module main program | Nick |
| main/hm3.py | Hive motor module main program | Nick |
| main/sl1.py | Smart light module main program | Milan |
| main/sm3.py | Smart motor module main program | Milan |
| main/sp1.py | Smart splat module main program | Nick |
| networking/networking.py | This is the main networking code that builds on ESP-NOW. There are many prepared functionalities (and some more that I am working on), such as long message support, sending of various variable types (bytes, bytearray, dicts, lists, int, float, char, string), as well as different types of messages such as ping, echo and more. There are also various features in place to make the networking more robust. | Nick |
| networking/ssp_networking.py | This is the ssp networking module. It needs config.py to function. | Nick |
| libraries/adxl345.py | Support for the built in accelerometer https://github.com/DFRobot/micropython-dflib/blob/master/ADXL345/user_lib/ADXL345.py | Milan |
| libraries/files.py | Custom save to file library | Milan |
| libraries/icons.py | Icon support for the smart motor module | Milan |
| libraries/sensors.py | Sensor support for the smart motor module | Milan |
| libraries/servo.py | Servo support for the smart motor module | Milan |
| libraries/smartlight.py | Smart light support for smart light module | Milan |
| libraries/splat.py | Smart splat support for smart splat module | Sophie |
| libraries/ssd1306.py | Support for the built in OLED screen https://github.com/stlehmann/micropython-ssd1306/blob/master/ssd1306.py | Milan |
| libraries/variableLED.py | Library that powers the variable LED grid | Sophie |
