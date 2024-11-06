# Smart System Education Platform

## Location: /software/README.qmd

### Description

This directory hosts code for the smart modules.

### Directories & Files

The repository has the following directory tree.

    .
    ├── README.md
    ├── README.qmd
    ├── README.rmarkdown
    ├── libraries
    │   ├── README.md
    │   ├── README.qmd
    │   └── variableLED.py
    ├── networking
    │   ├── README.md
    │   ├── README.qmd
    │   ├── config.py
    │   ├── examples
    │   └── networking.py
    ├── old
    │   ├── 4sophie.py
    │   ├── aioespnow.py
    │   ├── hackathon
    │   ├── led.py
    │   ├── long_message_Test.py
    │   ├── main.py
    │   ├── networking2.py
    │   ├── networking_old copy.py
    │   ├── networking_old.py
    │   ├── networkingtest.py
    │   └── secrets.py
    └── tools
        ├── MnS
        ├── README.md
        ├── README.qmd
        ├── boop-o-meters
        ├── display
        ├── p2p
        └── ping

A short description of the directories can be found below.

    #### Description for libraries 



    # Smart System Education Platform

    ## Location: /software/libraries/README.qmd

    ### Description

    This directory hosts used and useful libraries.

    ### Directories & Files

    The repository has the following directory tree.

        .
        ├── README.qmd
        ├── README.rmarkdown
        └── variableLED.py

    A short description of the directories can be found below.

    variableLED.py: variable LED library 

    #### Description for networking 



    # Smart System Education Platform

    ## Location: /software/networking/README.qmd

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

        .
        ├── README.qmd
        ├── README.rmarkdown
        ├── config.py
        ├── examples
        └── networking.py

    A short description of the directories can be found below.

    | name | description | contribution |
    |----|----|----|
    | config.py | This file hosts configurations and secrets, such as the board name, WiFi name and password, as well as handshake keys which is used by some of the legacy networking code. | Nick |
    | examples | This directory hosts example code | Nick |
    | examples/example.py | This is some basic example code on how to use my networking library | Nick |
    | examples/long_message_example.py | This code showcases the long message capabilities built into my code. By sending multiple messages that are then stitched back together by the recipient the max payload can be increased from 241 bytes to 256 x 238 = 60928 bytes, although in reality the ESP32 boards will start running out of memory with messages above 30 kilobytes. | Nick |
    | networking.py | This is the main networking code that builds on ESP-NOW. There are many prepared functionalities (and some more that I am working on), such as long message support, sending of various variable types (bytes, bytearray, dicts, lists, int, float, char, string), as well as different types of messages such as ping, echo and more. There are also various features in place to make the networking more robust. It needs config.py to function. | Nick | 

    #### Description for tools 



    # Smart System Education Platform

    ## Location: /software/tools/README.qmd

    ### Description

    This directory hosts the code.

    ### Directories & Files

    The repository has the following directory tree.

        .
        ├── MnS
        │   ├── master.py
        │   └── slave.py
        ├── README.md
        ├── README.qmd
        ├── README.rmarkdown
        ├── boop-o-meters
        │   ├── boop-o-meter 100.py
        │   ├── boop-o-meter 200.py
        │   └── boop-o-meter 300.py
        ├── display
        │   ├── display.py
        │   └── networking_display.py
        ├── p2p
        │   └── main.py
        └── ping
            ├── echo.py
            └── shout.py

    A short description of the directories can be found below.

    A short description of the directories can be found below.

    | name | description | contribution |
    |----|----|----|
    | boop-o-meters | This code will allow you to send “boops” to any discovered mac address (i.e. every running smart motor that has networking.py initialised). It counts how many “boops” were sent and received. | Nick |
    | display | Displays discovered smart modules with networking enabled. | Nick |
    | MnS | This uses the networking code to control multiple smart motor using the sensor inputs of a “master” smart motor. The MAC is hard-coded. | Nick |
    | p2p | This uses the networking code to have smart motors use their partners sensor inputs. The MAC is hard-coded. If there is no stream of sensor data received from the partner, the smart motor reverts back and uses their own inputs. | Nick |
    | ping | Example code for pings and for returning pings (echo) | Nick | 
    