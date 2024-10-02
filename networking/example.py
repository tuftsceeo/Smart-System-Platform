from networking import Networking
import time

#Initialise
networking = Networking()

###Example code###

recipient_mac = b'\xff\xff\xff\xff\xff\xff' #This mac sends to all
message =  b'Boop'

#Print own mac
print(networking.sta._sta.config('mac'))
print()

#Ping, calculates the time until you receive a response from the peer
networking.aen.ping(recipient_mac)
print()

#Echo, sends a message that will be repeated back by the recipient
networking.aen.echo(recipient_mac, message)
print()

#Message, sends the specified message to the recipient, supported formats are bytearrays, bytes, int, float, string, bool, list and dict, max 60928 bytes
networking.aen.send(recipient_mac, message)
print()

#Check if there are any messages in the message buffer
print(networking.aen.check_messages())
print()

#Get Last Received Message
print(networking.aen.return_message()) #Returns none, none, none if there are no messages
print()

#Get All Recieved Messages
messages = networking.aen.return_messages()
for mac, message, receive_time in messages:
    print(mac, message, receive_time)
    
#Set up an interrupt which runs a function as soon as possible after receiving a new message
def receive():
    for mac, message, rtime in networking.aen.return_messages(): #You can directly iterate over the  
        print(mac, message, rtime)

networking.aen.irq(receive) #interrupt handler