from networking import Networking
import time

#Initialise
networking = Networking()

#Example code
recipient_mac = b'\xff\xff\xff\xff\xff\xff'
message =  b'Boop'
#print own mac
print(networking.mac())

#Ping, calculates the time until you receive a response from the peer
networking.aen.ping(recipient_mac)

#Echo, sends a message that will be repeated back by the recipient
networking.aen.echo(recipient_mac, message)

#Message, sends the specified message to the recipient, supported formats are bytearrays, bytes, int, float, string, bool, list and dict, max 60928 bytes
networking.aen.message(recipient_mac, message)

#Check if there are any messages in the message buffer
print(networking.aen.check_messages())

#Get Last Received Message
print(networking.aen.return_message())

#Get All Recieved Messages
messages = networking.aen.return_messages()
for mac, message, receive_time in messages:
    print(mac, message, rtime)
    
#Set up an interrupt which runs a function as soon as possible after receiving a new message
def receive():
    for mac, message, rtime in networking.aen.return_messages(): #You can directly iterate over the  
        print(mac, message, rtime)

networking.aen.cirq(receive) #interrupt handler