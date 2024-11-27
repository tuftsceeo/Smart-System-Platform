

# 

#### Location: /software/applications/README.qmd

##### Description

This directory hosts the code.

##### Directories & Files

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
    ├── githubfiledownload
    │   └── filedownload.py
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
