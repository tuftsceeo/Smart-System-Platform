import network
sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)
sta_if.active(True)
sta_if.connect('', '') #fill in with wifi and pw

import mip
base = "https://raw.githubusercontent.com/tuftsceeo/Smart-System-Platform/tree/b55c0e019d56afd73d017165f8d3636b31cd7edc/software/networking"
files_to_copy = ["config.py", "networking.py"]

for f in files_to_copy:
    print("Installing: ", f)
    mip.install(base+f)