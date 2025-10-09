

# Smart System Education Platform

## Location: /work/Smart-System-Platform/Smart-System-Platform/software/release/sl1/README.qmd

### Description

This directory hosts release ready code for the smart module sl1.

### Directories & Files

The repository has the following directory tree.

    .
    ├── README.md
    ├── README.qmd
    ├── README.rmarkdown
    ├── adxl345.py
    ├── boot.py
    ├── config.py
    ├── files.py
    ├── icons.py
    ├── networking.py
    ├── sensors.py
    ├── servo.py
    ├── sl1.py
    ├── smartlight.py
    ├── ssd1306.py
    └── ssp_networking.py

A short description of the files can be found below.

| name | description | contribution |
|----|----|----|
| config.py | Smart Module Configuration File | Nick |
| boot.py | Smart Module boot.py | Nick |
| sl1.py | Smart motor module main program | Milan |
| networking.py | This is the main networking code that builds on ESP-NOW. There are many prepared functionalities (and some more that I am working on), such as long message support, sending of various variable types (bytes, bytearray, dicts, lists, int, float, char, string), as well as different types of messages such as ping, echo and more. There are also various features in place to make the networking more robust. | Nick |
| ssp_networking.py | This is the ssp networking module. It needs config.py to function. | Nick |
| adxl345.py | Support for the built in accelerometer https://github.com/DFRobot/micropython-dflib/blob/master/ADXL345/user_lib/ADXL345.py | Milan |
| files.py | Custom save to file library | Milan |
| icons.py | Icon support for the smart motor module | Milan |
| sensors.py | Sensor support for the smart motor module | Milan |
| servo.py | Servo support for the smart motor module | Milan |
| smartlight.py | Smart light support for smart light module | Milan |
| ssd1306.py | Support for the built in OLED screen https://github.com/stlehmann/micropython-ssd1306/blob/master/ssd1306.py | Milan |
