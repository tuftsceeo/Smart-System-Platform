from networking import Networking
import time

networking = Networking()

start = time.ticks_ms()
mark = time.ticks_ms()
while True:
    if time.ticks_ms()-mark >= 1000:
        mark = time.ticks_ms()
        print(f"{(mark-start)/1000}: {networking.aen.boops}")
    networking.aen.receive_task()