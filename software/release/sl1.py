
from machine import Pin, SoftI2C, PWM, ADC
from files import *
import time
from machine import Timer
#import smarttools
import servo
import icons
import os
import sys
import ubinascii
import machine
import smartlight


import sensors
sens=sensors.SENSORS()

#unique name

ID= ubinascii.hexlify(machine.unique_id()).decode()
numberofIcons=[len(icons.iconFrames[i]) for i in range(len(icons.iconFrames))] #[homescreen, trainscreen, playscreen, playthefilesscreen, settingsscreen]
highlightedIcon=[]
for numberofIcon in numberofIcons:
    highlightedIcon.append([0,numberofIcon])

screenID=1
lastPressed=0
previousIcon=0
filenumber=0


currentlocaltime=0
oldlocaltime=0

points = []


#Defining all flags
#flags
flags=[False,False,False,False, False]
playFlag=False
triggered=False
LOGGING=True


#switch flags
switch_state_up = False
switch_state_down = False
switch_state_select = False

last_switch_state_up = False
last_switch_state_down = False
last_switch_state_select = False

switched_up = False
switched_down = False
switched_select = False


#mainloop flags
clearscreen=False


#define buttons , sensors and motors
#servo
s = smartlight.SmartLight(2)

#nav switches
switch_down = Pin(8, Pin.IN)
switch_select = Pin(9, Pin.IN)
switch_up= Pin(10, Pin.IN)

i2c = SoftI2C(scl = Pin(7), sda = Pin(6))
display = icons.SSD1306_SMART(128, 64, i2c,switch_up)

#scale values for raibow lights instead of servo motor
output_range = [0, 1000]
sens.set_final_range(output_range) #ensure output of sensor mapping gives correct range
display.set_output_range(output_range) #ensure display shows correct range in y direction

#highlightedIcon=[(ICON,TotalIcons),...]
#screenID gives the SCREEN number I am at
#SCREENID
#0 - HOMESCREEN
#1 - PlaySCREEN
#2 - TrainSCREEN
#3 - Playthefiles
#4 - ConnectSCREEN

#highligtedIcons[screenID][0] which icon is highlighted on screenID screen
#highligtedIcons[screenID][0] =1 # First Icon selected
#highligtedIcons[screenID][0] =2 #Second
#highligtedIcons[screenID][0] =3 #Third

#interrupt functions

def downpressed(count=-1):
    global playFlag
    global triggered
    playFlag = False
    time.sleep(0.05)
    if(time.ticks_ms()-lastPressed>200):
        displayselect(count)
    
    triggered=True #log file


def uppressed(count=1):
    global playFlag
    global triggered
    playFlag = False 
    time.sleep(0.05)
    if(time.ticks_ms()-lastPressed>200):
        displayselect(count)
    triggered=True #log file


def displayselect(selectedIcon):
    global screenID
    global highlightedIcon
    global lastPressed
    global previousIcon
    
    highlightedIcon[screenID][0]=(highlightedIcon[screenID][0]+selectedIcon)%highlightedIcon[screenID][1]
    display.selector(screenID,highlightedIcon[screenID][0],previousIcon) #draw circle at selection position, and remove from the previousIconious position
    previousIcon=highlightedIcon[screenID][0]

    lastPressed=time.ticks_ms()
    
def selectpressed():
    #declare all global variables, include all flags
    global flags
    global triggered
    time.sleep(0.1)
    flags[highlightedIcon[screenID][0]]=True
    triggered=True #log file
    

    
        
def resettohome():
    global screenID
    global highlightedIcon
    global previousIcon
    global clearscreen
    screenID=0
    previousIcon=0
    for numberofIcon in numberofIcons:
        highlightedIcon.append([0,numberofIcon])
    display.selector(screenID,highlightedIcon[screenID][0],0)
    #display.fill(0) # clear screen
    clearscreen=True
    
def check_switch(p):
    global switch_state_up
    global switch_state_down
    global switch_state_select
    
    global switched_up
    global switched_down
    global switched_select
    
    global last_switch_state_up
    global last_switch_state_down
    global last_switch_state_select
    
    switch_state_up = switch_up.value()
    switch_state_down = switch_down.value()
    switch_state_select = switch_select.value()
         
    if switch_state_up != last_switch_state_up:
        switched_up = True
        
    elif switch_state_down != last_switch_state_down:
        switched_down = True
        
    elif switch_state_select != last_switch_state_select:
        switched_select = True
                
    if switched_up:
        if switch_state_up == 0:
            uppressed()
        switched_up = False
    elif switched_down:
        if switch_state_down == 0:
            downpressed()
        switched_down = False
    elif switched_select:
        if switch_state_select == 0:
            selectpressed()
        switched_select = False
    
    last_switch_state_up = switch_state_up
    last_switch_state_down = switch_state_down
    last_switch_state_select = switch_state_select



def displaybatt(p):
    batterycharge=sens.readbattery()
    display.showbattery(batterycharge)
    if LOGGING:
        savetolog(time.time(),screenID,highlightedIcon, point,points) 
    return batterycharge



def nearestNeighbor(data, point):
    try:
        point = point[0]
    except TypeError:
        print("error")
        pass
    if len(data) == 0:
        return 0
    diff = 10000
    test = None
    for i in data:
        if abs(i[0] - point) <= diff:
            diff = abs(i[0] - point)
            test = i
    return test

def resetflags():
    global flags
    for i in range(len(flags)):
        flags[i]=False
 
 
def shakemotor(point):
    motorpos=point[1]
    for i in range(2):
        s.write_angle(min(180,motorpos+5))
        time.sleep(0.1)
        s.write_angle(max(0,motorpos-5))
        time.sleep(0.1)
        
    print(motorpos)
    
    

def readdatapoints():
    datapoints=readfile()        
    if(datapoints):
        numberofdata=len(datapoints)
        return datapoints[-1]    
    else:
        return ([])
    

def setloggingmode():
    #sets pref to log by default
    if not switch_down.value() and not switch_up.value() and not switch_select.value():
        resetlog()  #delete all the previous logs
        setprefs()  #sets preference file to True 
        display.showmessage("LOG: ON")
        print("resetting the log file")
        

    #resets prefs to not log by default
    if not switch_down.value() and not switch_up.value() and switch_select.value():
        resetprefs()  #resets preference file to False
        print("turn OFF the logging")
        display.showmessage("LOG: OFF")


    if switch_down.value() and switch_up.value() and switch_select.value():
        print("default: turn ON the logging")
        
        
    import prefs
    return prefs.log


points=readdatapoints()
points_color = []
points_number = []
points_brightness = []
if points==[]:
    highlightedIcon[1][0]=1  #go to add if there are no data saved

#setting up Timers
tim = Timer(0)
tim.init(period=50, mode=Timer.PERIODIC, callback=check_switch)
batt = Timer(2)
batt.init(period=3000, mode=Timer.PERIODIC, callback=displaybatt)


display.welcomemessage()
    
    
LOGGING=setloggingmode()
       
#setup with homescreen  #starts with screenID=0
display.selector(screenID,highlightedIcon[screenID][0],-1)
oldpoint=[-1,-1]
highlighted = highlightedIcon[screenID][0]
    
while True:
    #log       
    point = sens.readpoint()
    #print(highlightedIcon[screenID][0])
    if(triggered):
        if LOGGING:
            savetolog(time.time(),screenID,highlightedIcon, point,points)
        triggered=False
    

    #broadcast(point, screenID, highlightedIcon[screenID][0],ID)
    
    #Homepage
    #[fb_Train,fb_Play]
    
    if(screenID==0):
        if(flags[0]):
            points=[] #empty the points arrray
            points_color = []
            points_brightness = []
            points_number = []
            screenID=1
            clearscreen=True
            display.graph(oldpoint, point, points)
            
        elif(flags[1]):
            screenID=2
            clearscreen=True
            datapoints=readfile()
            if (datapoints==[]):
                display.showmessage("No data saved")
                resettohome()
            else:
                display.graph(oldpoint, point, points)
            
    # Training Screen
    # [fb_add,fb_delete,fb_smallplay,fb_home]
    elif(screenID==1):
        
        if (highlighted != highlightedIcon[screenID][0]):
            display.cleargraph()
        
        if(flags[0]): # Play button is pressed
            if (points):
                playFlag=True
                s.set_white()
                #savetofile(points)
                #shakemotor(point)
                #screenID=2 # trigger play screen
                #uppressed(count=4)
            else:
                cleardatafile()
                display.showmessage("NO DATA")
                #resettohome()
        
        elif(flags[1]): # add button is pressed
            points_color.append(list(point))
            points.append(list(point))
            display.graph(oldpoint, point, points)
            #shakemotor(point)
            
        elif(flags[2]): #brightness add button is pressed
            points_brightness.append(list(point))
            points.append(list(point))
            display.graph(oldpoint, point, points_brightness)
                

        elif(flags[3]): #number add button is pressed
            points_number.append(list(point))
            points.append(list(point))
            display.graph(oldpoint, point, points_number)

 
        elif(flags[4]): #delete button is pressed
            if(points): #delete only when there is something
                points.pop()
            if(points_color): points_color.pop()
            if(points_brightness): points_brightness.pop()
            if(points_number): points_number.pop()
            display.cleargraph()
            display.graph(oldpoint, point, points)

        
        if(playFlag): #only when point is different now
            if(not point==oldpoint): #only when point is different now
                point = nearestNeighbor(points,point)
                if (points_color): s.set_color(nearestNeighbor(points_color,point)[1])
                if (points_brightness): s.set_brightness(nearestNeighbor(points_brightness,point)[1])
                if (points_number): s.set_number(nearestNeighbor(points_number,point)[1])
                s.update()
                display.graph(oldpoint, point, points)

            
        else:
            if(not point==oldpoint): #only when point is different now
                
                display.cleargraph()
                
                if (highlighted == 1): #training color
                    s.set_white()
                    s.set_color(point[1])
                    s.update()
                    display.graph(oldpoint, point, points_color)
                    
                elif(highlighted == 2): #training brightness
                    s.set_white()
                    s.set_brightness(point[1])
                    s.update()
                    display.graph(oldpoint, point, points_brightness)
                    
                elif (highlighted == 3): #training number
                    s.set_white()
                    s.set_number(point[1])
                    s.update()
                    display.graph(oldpoint, point, points_number)
                    
                else:
                    display.graph(oldpoint, point, points)
                    
    
    # Load saved files screen
    #[fb_next,fb_delete,fb_home,fb_toggle]
    elif(screenID==2):
        datapoints=readfile()        
        if(datapoints):
            numberofdata=len(datapoints)
            points=datapoints[filenumber]
            
            if(flags[0]):
                filenumber=((filenumber+1)%numberofdata)
                points=datapoints[filenumber]
                display.cleargraph()
                
            elif(flags[1]):
                del datapoints[filenumber]
                replacefile(datapoints)
                filenumber=0
                display.cleargraph()

            elif(flags[2]):
                resettohome()
                
            if(not point==oldpoint): #only when point is different now
                point = nearestNeighbor(points,point)
                s.write_color(point[1])
                display.graph(oldpoint, point, points)
        else:
            display.showmessage("No files to show")
            resettohome()
               
    # Settings Screen
    #[fb_Lead,fb_Follow, fb_BIGHome]
    elif(screenID==4):
        if(flags[0]):
            display.showmessage(ID)
            waitforconnection()
            
        elif(flags[1]):
            print("I shall follow you")
        
        elif(flags[2]):
            resettohome()
                    
    oldpoint=point
    highlighted = highlightedIcon[screenID][0]
    resetflags()
    if clearscreen:
        display.fill(0)
        display.selector(screenID,highlightedIcon[screenID][0],-1)
        clearscreen=False





