

# Smart System Education Platform

## Location: /work/Smart-System-Platform/Smart-System-Platform/software/release/min/README.qmd

### Description

This directory hosts release ready code for the smart module min.

### Directories & Files

The repository has the following directory tree.

    .
    ├── README.qmd
    ├── README.rmarkdown
    ├── boot.py
    ├── config.py
    ├── main.py
    ├── networking.py
    └── ssp_networking.py

A short description of the files can be found below.

| name | description | contribution |
|----|----|----|
| config.py | Smart Module Configuration File | Nick |
| boot.py | Smart Module boot.py | Nick |
| main.py | Smart Module main.py | Nick |
| networking.py | This is the main networking code that builds on ESP-NOW. There are many prepared functionalities (and some more that I am working on), such as long message support, sending of various variable types (bytes, bytearray, dicts, lists, int, float, char, string), as well as different types of messages such as ping, echo and more. There are also various features in place to make the networking more robust. | Nick |
| ssp_networking.py | This is the ssp networking module. It needs config.py to function. | Nick |
