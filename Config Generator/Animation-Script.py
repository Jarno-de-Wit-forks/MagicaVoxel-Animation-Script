
from time import process_time_ns, thread_time_ns
from typing import Optional
from ctypes import wintypes, windll, create_unicode_buffer
import pyperclip
import pydirectinput as pydi
import time
import json
import sys
import os

command = []
global atime
atime = int(0)

def getForegroundWindowTitle() -> Optional[str]:            #Get current active Window
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)
    if buf.value == "MagicaVoxel | Ephtracy":              #If current active Window Magicavoxel then
        return False                                       #Continue script (not very performant) takes about 0.2 seconds to run and is has a noticable impact how fast something can go.
    else:
        return True


def exitprog():
    input("Press Enter to continue...")
    sys.exit()


#big working mess
def beziersetup(firstkeyframe, lastkeyframe, data, ammountframes):
    frame = 0
    
    while frame < ammountframes:                                                        #Repeats for the ammount of frames
        frame += 1           
        command = []   
        commandstring = " "                                                        
        for key, _ in data["keyframe"][firstkeyframe]["param"].items():                   #Get all items of the first keyframe
            lerparray = []                                                              #Array to store the lerp values
            currentkeyframe = firstkeyframe                                             #define starting keyframe 
            count = 0                           
            while currentkeyframe <= lastkeyframe+1:                                     #loop through all keyframes until keyframe is no longer a bezier keyframe 
                if key.find("ry") != -1:                                                        #If key is yaw                         
                    if len(lerparray) == 0:                                             #If lerparray is empty             
                        lerparray.append(float(data['keyframe'][currentkeyframe]["param"]["cam ry"]))#Add first value to lerparray
                        currentkeyframe += 1                       #Add first yaw value to lerparray
                    try:                                                                                                #Try to get next yaw value          
                        lerparray.append(leftright(float(lerparray[count]), float(data["keyframe"][currentkeyframe]["param"]["cam ry"]), data["keyframe"][currentkeyframe-1]["Option"]["direction"]))  #Sends first yaw value (from lerp array appended two lines above) to leftright + current yaw value and in which direction to move line 77
                        currentkeyframe += 1                                            #progress to next keyframe
                        count += 1                                                      #increase count
                    except:                     
                        currentkeyframe += 1                                            #catching some rare errors that dont have much impact on the animation                  
                else:
                    lerparray.append(data['keyframe'][currentkeyframe]["param"][key])     #if key is not yaw then add value to lerparray
                    currentkeyframe += 1                                                #progress to next keyframe                      
                                                                                        #Do all of that untill all data from all keyframes is stored in lerparray
            commandstring = commandstring + key + " " + str(bezier(lerparray, frame/ammountframes,key)) + " | " 
            if len(commandstring) > 400:                                    #command limit in magicavoxel
                command.append(commandstring)
                commandstring = ""
        commandstring = commandstring + " " + animationHandler(firstkeyframe,data) 
        command.append(commandstring)              
        print("Frame: " + str(frame+1) + " of " + str(ammountframes))
        print("Keyframe: " + str(firstkeyframe))
        print("Last command: " + str(command))
        mvinput(command,float(data["keyframe"][firstkeyframe]["SecondsPerRender"])) 
        
    global keyframenum
    keyframenum = keyframenum + 1
        #This exports all of the command data to MVInput, Mv input will use these to interact with MagicaVoxel itself.
        #Command data is calculated from the bezier function, and the frame is used to calculate the position on the bezier curve. For each frame.


def leftright(c_yaw,n_yaw,c_dircetion):
    #I WAS TOO STUPIDD TO UNUDERSTAND HOW TO NORMALIZE THE VALUE OR WHAT NORMALISATOIN EVEN IS

    c_dircetion = c_dircetion.lower()
    if c_dircetion == "counterclockwise" or "decrease":
        if c_yaw > 0 and n_yaw < 0:
            n_yaw = n_yaw + 360
        elif c_yaw < 0 and n_yaw > 0:
            n_yaw = n_yaw - 360
        elif c_yaw > 0 and n_yaw > 0:
            n_yaw = n_yaw + 360
        elif c_yaw < 0 and n_yaw < 0:
            n_yaw = n_yaw - 360
    elif c_dircetion == "clockwise" or "increase":
        if c_yaw > 0 and n_yaw < 0:
            n_yaw = n_yaw + 360
        elif c_yaw < 0 and n_yaw > 0:
            n_yaw = n_yaw - 360
        elif c_yaw > 0 and n_yaw > 0:
            n_yaw = n_yaw - 360
        elif c_yaw < 0 and n_yaw < 0:
            n_yaw = n_yaw + 360
    return n_yaw



def bezier(lerparray, frame,key):                   #get the whole lerparray the current frame and 
    
    count = 0                                       #define count                 
    newlerparray = []                               #define newlerparray this will always get filled with new data      
    while count < len(lerparray)-1:                 # repeat until the lenght of lerparray is reached Why? Example: Lerparray Lenght 3 -> (1)(2)(3) Values are slowly beeing interpolated and and only 1 out 2 values are clockwise.
        newlerparray.append(float(lerp(float(lerparray[count ]), float(lerparray[count+1]), frame)))#                                      (1) (2)  Orignal set is stored in lerparray
        count += 1                                 #increase count                                                                           (1)    New values are storred in newlerparray
                                                                                                                                #                   If count reaches 1 there is nothing to be interpolated we have reached our final value 
    if len(newlerparray) == 1:                     #if newlerparray is only one value clockwise then return that value                                   Lean more at https://youtu.be/aVwxzDHniEw?t=237
        return float(newlerparray[0])              #return value to previous recursion
    else:
        return bezier(newlerparray, frame,key)     #return recursivly until out of bezier completly (probably could do that differnt my brain was mush)

def lerp(a, b, t):
    return float(a + (b - a) * t)

def readconfig():                                                            
    try:
        global data 
        with open('config.json') as json_file:             #Load Json file
            data = json.load(json_file)                    #Write Json to var
        json_file.close()                                  #Close Json file
    except:                                                #If json not found error
        print("ERROR: You either dont have a camara.json in this folder or you made a mistake.")
        print("Common issues: you wrote true or false with an uppercaseletter or you got a typo somewhere")
        exitprog()

    print("Please open MagicaVoxel and make sure its in the foreground.")
    pause(True)                                            #Wait until window in Active to start script we dont want the script spamming your discord for 
    global keyframenum
    keyframenum = 0
    interpolation = []

                                                                #big mess
                                                                #Run through all keyframes     
    while keyframenum < len(data['keyframe']):
        try:                                                    #Storing all interpolation values in a list
            interpolation.append(str(data['keyframe'][keyframenum]["option"]['interpolation']))
        except:                                                 #If no interpolation is found for a keyframe then it is set 1
            interpolation.append("1")                           #How it works Key frame start with Bezier from 1 - 5th keyframe. This would look like this in the list Bezier 1 1 1 1 
        keyframenum += 1                                        #untill it finds another interpolation type for example linear 6 - 7 -> Bezier 1 1 1 1 Linaer 1 

    keyframenum = 0
    while keyframenum+1 < len(data['keyframe']):                #Another big mess
        ammountframes = 0                                       #keeps track of how many frames the animation will have
        if interpolation[keyframenum] == "bezier":              #If current keyframe is a bezier keyframe
            ammountframes = int(data['keyframe'][keyframenum]["option"]['frames'])+ammountframes #count up how many frames the animation will have frames are defined in camara.json
            bezierKeyframe = keyframenum                                                                    #store the keyframe number                                                          
            if keyframenum+1 < len(interpolation):
                while interpolation[keyframenum+1] == "1":  #Get how many more bezier keyframes there are. This is important since we want a smooth animation for all frames. 
                    keyframenum += 1
                    ammountframes = int(data['keyframe'][keyframenum]["option"]['frames'])+ammountframes   #if we went had a bezier curve between two lines we would effectifly have a line.
                    if keyframenum+1 >= len(interpolation):
                        break                               
                        
            beziersetup(bezierKeyframe, keyframenum, data, ammountframes)                    #Run bezier function
        else:
            liniar(keyframenum, data)                                            #If current keyframe is a liniar keyframe send current and next keyframe to liniar function
            keyframenum += 1




def animationHandler(currentkeyframe, data):
    global atime
    if True == data['keyframe'][currentkeyframe]["animation"]["enable animation"]:
        atime = atime + 1
        if atime == int(data['keyframe'][currentkeyframe]['animation']['endframe']):
            if data['keyframe'][currentkeyframe]['animation']["loop"] == "true":
                atime = int(data['keyframe'][currentkeyframe]['animation']['startframe'])
    else:
        return ""

    return "set a_time "+ str(int(atime)) + " | " 

def normalise(val):
    return (val % 360 + 360) % 360

def normaliseneg(val):
    return (val % -360 + -360) % -360

def liniar(currentkeyframe, data):
    try:
        valueM = []
        totalframeCurKeyframe = int(data['keyframe'][currentkeyframe]["option"]['frames'])
        global atime
        
        for i in range(0, totalframeCurKeyframe):                                 
            command = []
            commandValue = ""

            if bool(data["global"]['saverenders']):
                commandValue ="snap scene | "
            for key, _ in data["keyframe"][currentkeyframe]["param"].items():
                startPos = float(data['keyframe'][currentkeyframe]["param"][key])
                goalPos = float(data['keyframe'][currentkeyframe+1]["param"][key])


                if key.find("ry") != -1:
                    currentDircetion = data["keyframe"][currentkeyframe]["option"]["direction"]
                    if currentDircetion == "clockwise":
                        startPos = normalise(startPos)
                        goalPos = normalise(goalPos)
                    elif currentDircetion == "counterclockwise":
                        startPos = normalise(startPos)
                        goalPos = normaliseneg(goalPos)

                commandValue = commandValue + key + " " + str(round(lerp(startPos, goalPos, i/totalframeCurKeyframe),4)) + " | "
            command.append(commandValue)
    

            if "Animation" in data["keyframe"]:
                atime = float(data["keyframe"][currentkeyframe]["animation"]["startframe"])
            secondPerRender = float(data['keyframe'][currentkeyframe]["option"]['secondsperrender'])
            print("Estimated time for current Keyframe: " + str(round((2+secondPerRender)*(totalframeCurKeyframe-i),2)) + " seconds")
            print("Frame: " + str(i) + " of " + str(totalframeCurKeyframe))
            print("Keyframe: " + str(currentkeyframe+1) + " of " + str(len(data['keyframe'])))
            #print "#" to covert the whole console width
            print("#"*(os.get_terminal_size().columns))


            #mvinput(command,secondPerRender)

    except ValueError:
        print("Error in config. Did you accidentally input a letter instead of a number?")
        exitprog()

    print("Keyframe: " + str(currentkeyframe+2) + " of " + str(len(data['keyframe'])))

def mvinput(command,secondPerRender):
    for i in range(len(command)):
        pydi.press('f1') 
        pause(False) 
        pyperclip.copy(command[i])  
        pydi.keyDown("ctrl")
        pydi.press("v")
        pydi.keyUp("ctrl")
        time.sleep(0.2) 
        pydi.press('enter')
        if bool(data["global"]['saveRenders']):         
            time.sleep(0.2)
            pydi.press('enter')
    time.sleep(secondPerRender)              

    
def pause(firsttime):
    if firsttime:
        while getForegroundWindowTitle():   #Detect if magicavoxel is active to not spam mv commands into normal user programms like discord
            time.sleep(3)    
        pass
    else:   
        if getForegroundWindowTitle():
            print("Progress paused...")     #This message appears if magicavoxel is not active anymore to prevent damage or unwanted messages
            while getForegroundWindowTitle():
                time.sleep(5)                                   
            print("WARNING: You exited magicavoxel while the render was in progress.")
            print("To avoid problems make sure the console is not selected and if it has any contenct delete it as this might lead to some issues.")
            input("Press enter to confirm")
            print("Select magicavoxel")

            while getForegroundWindowTitle():
                time.sleep(5)              

def main():
    readconfig()

try:
    main()
except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)


