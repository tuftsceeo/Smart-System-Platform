

# Smart System Education Platform

## Location: /work/Smart-System-Platform/Smart-System-Platform/software/release/sp1/README.qmd

### Description

This directory hosts release ready code for the smart module sp1.

### Directories & Files

The repository has the following directory tree.

    .
    ├── README.md
    ├── README.qmd
    ├── README.rmarkdown
    ├── boot.py
    ├── config.py
    ├── networking.py
    ├── sp1.py
    ├── splat.py
    ├── ssp_networking.py
    └── variableLED.py

A short description of the files can be found below.

| name | description | contribution |
|----|----|----|
| config.py | Smart Module Configuration File | Nick |
| boot.py | Smart Module boot.py | Nick |
| sp1.py | Smart splat module main program | Nick |
| networking.py | This is the main networking code that builds on ESP-NOW. There are many prepared functionalities (and some more that I am working on), such as long message support, sending of various variable types (bytes, bytearray, dicts, lists, int, float, char, string), as well as different types of messages such as ping, echo and more. There are also various features in place to make the networking more robust. | Nick |
| ssp_networking.py | This is the ssp networking module. It needs config.py to function. | Nick |
| splat.py | Smart splat support for smart splat module | Sophie |
| variableLED.py | Library that powers the variable LED grid | Sophie |
