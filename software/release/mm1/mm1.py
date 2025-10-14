import uasyncio as asyncio
import time

try:  # ensure networking is available
    networking
except NameError:
    from config import networking as networking

from config import hive_config

print("running mm1.py")

async def heartbeat_loop():
    while hive_config["hive"]:
        print("heartbeat")
        if hive_config["recipients"]:
            test_data = {
                "test": 42,
                "time_sent": time.ticks_ms()
            }
            networking.send_data(hive_config["recipients"], test_data)

        recv_sensor_data = networking.return_data()
        for mac, data in recv_sensor_data.items():
            print(f"Received from {mac}: {data}")

        await asyncio.sleep(hive_config["refreshrate"] / 1000)


if hive_config["hive"]:
    asyncio.run(heartbeat_loop())
