---
editor: visual
editor_options:
  chunk_output_type: console
execute:
  echo: false
  message: false
  warning: false
toc-title: Table of contents
---

# Smart System Education Platform

## Location: /work/Smart-System-Platform/Smart-System-Platform/software/networking/README.qmd

### Description

This directory hosts the networking code and examples. The networking
code builds on top of the ESP-Now p2p networking code by espressif,
which itself uses the WiFi capabilities of the ESP32 board.

Some facts and figures:

Range: up to 215 meters

Max Payload: 241 bytes

Channels: 14

### Directories & Files

The repository has the following directory tree.

:::: cell
::: {.cell-output .cell-output-stdout}
    .
    ├── README.md
    ├── README.qmd
    ├── README.rmarkdown
    ├── config.py
    ├── examples
    │   ├── default_main.py
    │   ├── example.py
    │   ├── long_message_example.py
    │   └── pyscript_main.py
    └── networking.py
:::
::::

A short description of the directories can be found below.

  -----------------------------------------------------------------------------------------------------------------
  name                               description                                                     contribution
  ---------------------------------- --------------------------------------------------------------- --------------
  config.py                          This file hosts configurations and secrets, such as the board   Nick
                                     name, WiFi name and password, as well as handshake keys which   
                                     is used by some of the legacy networking code.                  

  examples                           This directory hosts example code                               Nick

  examples/example.py                This is some basic example code on how to use my networking     Nick
                                     library                                                         

  examples/long_message_example.py   This code showcases the long message capabilities built into my Nick
                                     code. By sending multiple messages that are then stitched back  
                                     together by the recipient the max payload can be increased from 
                                     241 bytes to 256 x 238 = 60928 bytes, although in reality the   
                                     ESP32 boards will start running out of memory with messages     
                                     above 30 kilobytes.                                             

  networking.py                      This is the main networking code that builds on ESP-NOW. There  Nick
                                     are many prepared functionalities (and some more that I am      
                                     working on), such as long message support, sending of various   
                                     variable types (bytes, bytearray, dicts, lists, int, float,     
                                     char, string), as well as different types of messages such as   
                                     ping, echo and more. There are also various features in place   
                                     to make the networking more robust. It needs config.py to       
                                     function.                                                       
  -----------------------------------------------------------------------------------------------------------------
