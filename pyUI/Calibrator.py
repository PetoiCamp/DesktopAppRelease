#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from commonVar import *

language = languageList['English']

BittleRWinSet = {
    "imageW": 360,       # The width of image
    "sliderW": 260,      # The width of the slider rail corresponding to joint numbers 0 to 3
    "rowJoint1": 2,      # The row number of the label with joint number 2 and 3
    "sliderLen": 260,    # The length of the slider rail corresponding to joint numbers 4 to 15
    "rowJoint2": 4       # The row number of the label with joint number 4 or 15 is located
}

RegularWinSet = {
    "imageW": 250,
    "sliderW": 200,
    "rowJoint1": 11,
    "sliderLen": 150,
    "rowJoint2": 2
}

BittleRMacSet = {
    "imageW": 300,       # The width of image
    "sliderW": 200,      # The width of the slider rail corresponding to joint numbers 0 to 3
    "rowJoint1": 2,      # The row number of the label with joint number 2 and 3
    "sliderLen": 200,    # The length of the slider rail corresponding to joint numbers 4 to 15
    "rowJoint2": 4       # The row number of the label with joint number 4 or 15 is located
}

RegularMacSet = {
    "imageW": 190,
    "sliderW": 140,
    "rowJoint1": 11,
    "sliderLen": 140,
    "rowJoint2": 2
}

# Chero-specific settings - compact 5-column layout
CheroWinSet = {
    "imageW": 250,       # Image width for Chero
    "sliderW": 150,      # Width for horizontal sliders (joints 0,1)
    "rowJoint1": 2,      # Row for horizontal sliders
    "sliderLen": 150,    # Length for vertical sliders (joints 2,3,4,5)
    "rowJoint2": 5       # Starting row for vertical sliders (moved down by 1 to make space for image)
}

CheroMacSet = {
    "imageW": 190,
    "sliderW": 120,
    "rowJoint1": 2,
    "sliderLen": 120,
    "rowJoint2": 5
}

parameterWinSet = {
    "Nybble": RegularWinSet,
    "Bittle": RegularWinSet,
    "BittleX+Arm": BittleRWinSet,
    "DoF16": RegularWinSet,
    "Chero": CheroWinSet,
}

parameterMacSet = {
    "Nybble": RegularMacSet,
    "Bittle": RegularMacSet,
    "BittleX+Arm": BittleRMacSet,
    "DoF16": RegularMacSet,
    "Chero": CheroMacSet,
}

frontJointIdx = [4, 5, 8, 9, 12, 13]

def txt(key):
    return language.get(key, textEN[key])
    
class Calibrator:
    def __init__(self,model,lan):
        self.calibratorReady = False
        global language
        language = lan
#        global goodPorts
        connectPort(goodPorts)
        start = time.time()
        while config.model_ == '':
            if time.time() - start > 5:
                config.model_ = model
                config.version_ = "N_210101"
                print('Use the model set in the UI interface.')
            time.sleep(0.01)
        self.configName = config.model_
        self.boardVersion = config.version_
        config.model_ = config.model_.replace(' ', '')
        if config.model_ == 'BittleX':
            self.model = 'Bittle'
        elif config.model_ == 'BittleX+Arm':
            self.model = 'BittleX+Arm'
        elif config.model_ == 'NybbleQ':
            self.model = 'Nybble'
        elif config.model_ == 'Chero':
            self.model = 'Chero'
        else:
            self.model = config.model_

        self.winCalib = Tk()
        self.winCalib.title(txt('calibTitle'))
        self.winCalib.geometry('+200+100')
        self.winCalib.resizable(False, False)
        self.calibSliders = list()
        self.OSname = self.winCalib.call('tk', 'windowingsystem')
        if self.OSname == 'win32':
            self.winCalib.iconbitmap(resourcePath + 'Petoi.ico')
            self.calibButtonW = 8
        else:
            self.calibButtonW = 4
        self.frameCalibButtons = Frame(self.winCalib)
        # For Chero, position the button frame to avoid overlap with horizontal sliders
        if self.model == 'Chero':
            self.frameCalibButtons.grid(row=0, column=2, rowspan=14)  # Column 2 (middle) - increased by 1
        else:
            self.frameCalibButtons.grid(row=0, column=3, rowspan=13)  # Original position - increased by 1
        calibButton = Button(self.frameCalibButtons, text=txt('Calibrate'), fg = 'blue', width=self.calibButtonW,command=lambda cmd='c': self.calibFun(cmd))
        standButton = Button(self.frameCalibButtons, text=txt('Stand Up'), fg = 'blue', width=self.calibButtonW, command=lambda cmd='balance': self.calibFun(cmd))
        restButton = Button(self.frameCalibButtons, text=txt('Rest'),fg = 'blue', width=self.calibButtonW, command=lambda cmd='d': self.calibFun(cmd))
        walkButton = Button(self.frameCalibButtons, text=txt('Walk'),fg = 'blue', width=self.calibButtonW, command=lambda cmd='walk': self.calibFun(cmd))
        saveButton = Button(self.frameCalibButtons, text=txt('Save'),fg = 'blue', width=self.calibButtonW, command=lambda: send(goodPorts, ['s', 0]))
        abortButton = Button(self.frameCalibButtons, text=txt('Abort'),fg = 'blue', width=self.calibButtonW, command=lambda: send(goodPorts, ['a', 0]))
#        quitButton = Button(self.frameCalibButtons, text=txt('Quit'),fg = 'blue', width=self.calibButtonW, command=self.closeCalib)
        if self.model == 'Chero':
            calibButton.grid(row=7, column=0)
            restButton.grid(row=7, column=1)
            standButton.grid(row=7, column=2)
            walkButton.grid(row=12, column=0)
            saveButton.grid(row=12, column=1)
            abortButton.grid(row=12, column=2)
        else:
            calibButton.grid(row=6, column=0)
            restButton.grid(row=6, column=1)
            standButton.grid(row=6, column=2)
            walkButton.grid(row=11, column=0)
            saveButton.grid(row=11, column=1)
            abortButton.grid(row=11, column=2)
#        quitButton.grid(row=11, column=2)

        self.OSname = self.winCalib.call('tk', 'windowingsystem')
        print(self.OSname)
        if self.OSname == 'win32':
            self.parameterSet = parameterWinSet[self.model]
        else:
            self.parameterSet = parameterMacSet[self.model]

        if self.model == 'BittleX+Arm':
            # self.parameterSet = parameterSet['BittleX+Arm']
            scaleNames = BittleRScaleNames
        elif self.model == 'Chero':
            # For Chero, use RegularScaleNames but only show 6 joints
            scaleNames = RegularScaleNames
        else:
            # self.parameterSet = parameterSet['Regular']
            scaleNames = RegularScaleNames

        if "B" in self.boardVersion:
            self.imgWiring = createImage(self.frameCalibButtons,
                                         resourcePath + config.model_ + self.boardVersion[1] + '_Wire.jpeg',
                                         self.parameterSet['imageW'])
        else:
            self.imgWiring = createImage(self.frameCalibButtons,
                                         resourcePath + config.model_ + '_Wire.jpeg',
                                         self.parameterSet['imageW'])

        self.imgWiring.grid(row=0, column=0, rowspan=5, columnspan=3)
        Hovertip(self.imgWiring, txt('tipImgWiring'))

        self.imgPosture = createImage(self.frameCalibButtons, resourcePath + self.model + '_Ruler.jpeg', self.parameterSet['imageW'])
        if self.model == 'Chero':
            self.imgPosture.grid(row=8, column=0, rowspan=3, columnspan=3)
        else:
            self.imgPosture.grid(row=7, column=0, rowspan=3, columnspan=3)

        # For Chero, show only 6 joints; for others, show 16 joints
        if self.model == 'Chero':
            self.numJoints = 6
        else:
            self.numJoints = 16

        for i in range(self.numJoints):
            if self.model == 'Chero':
                # Chero layout: joints 0,1 horizontal, joints 2,3,4,5 vertical (like DoF16 joints 8,9,10,11)
                if i < 2:  # Joints 0, 1 - horizontal
                    tickDirection = 1
                    cSPAN = 2  # Each horizontal slider spans 2 columns
                    ROW = 0
                    rSPAN = 1
                    ORI = HORIZONTAL
                    LEN = self.parameterSet['sliderW']  # Use full slider width like SkillComposer
                    ALIGN = 'we'
                    
                    if i == 0:  # Head Pan
                        COL = 0  # Joint 0: columns 0-1 (leftmost)
                    else:  # Head Tilt  
                        COL = 3  # Joint 1: columns 3-4 (rightmost, skip column 2)
                else:  # Joints 2, 3, 4, 5 - vertical (like DoF16 joints 8,9,10,11)
                    tickDirection = -1
                    # Map Chero joints 2,3,4,5 to DoF16 layout positions 8,9,10,11
                    if i == 2:  # Joint 2 -> position like DoF16 joint 8 (left front)
                        leftQ = True
                        frontQ = True
                    elif i == 3:  # Joint 3 -> position like DoF16 joint 9 (right front)
                        leftQ = False
                        frontQ = True
                    elif i == 4:  # Joint 4 -> position like DoF16 joint 10 (right back)
                        leftQ = False
                        frontQ = False
                    else:  # Joint 5 -> position like DoF16 joint 11 (left back)
                        leftQ = True
                        frontQ = False
                    
                    LEN = self.parameterSet['sliderLen']
                    rSPAN = 3
                    cSPAN = 1
                    ROW = self.parameterSet['rowJoint2'] + (1 - frontQ) * (rSPAN + 2)
                    
                    # Use specific columns: joints 2,5 at column 0; joints 3,4 at column 4
                    if leftQ:
                        COL = 0  # Joints 2,5: column 0
                        ALIGN = 'sw'
                    else:
                        COL = 4  # Joints 3,4: column 4
                        ALIGN = 'se'
                    ORI = VERTICAL
            else:
                # Original logic for other models (16 joints)
                if i < 4:
                    tickDirection = 1
                    cSPAN = 3
                    if i < 2:
                        ROW = 0
                    else:
                        ROW = self.parameterSet['rowJoint1']

                    if 0 < i < 3:
                        COL = 4
                    else:
                        COL = 0
                    rSPAN = 1
                    ORI = HORIZONTAL
                    LEN = self.parameterSet['sliderW']
                    ALIGN = 'we'

                else:
                    tickDirection = -1
                    leftQ = (i - 1) % 4 > 1
                    frontQ = i % 4 < 2
                    upperQ = i / 4 < 3

                    rSPAN = 3
                    cSPAN = 1
                    ROW = self.parameterSet['rowJoint2'] + (1 - frontQ) * (rSPAN + 2)

                    if leftQ:
                        COL = 3 - i // 4
                        ALIGN = 'sw'
                    else:
                        COL = 3 + i // 4
                        ALIGN = 'se'
                    ORI = VERTICAL
                    LEN = self.parameterSet['sliderLen']
                    # ALIGN = 'sw'
            stt = NORMAL
            if i in NaJoints[self.model]:
                clr = 'light yellow'
            else:
                clr = 'yellow'
            
            # Set side labels
            if self.model == 'Chero':
                # For Chero, joints 2,3,4,5 should have side labels corresponding to DoF16 joints 8,9,10,11
                if i in range(2, 6):  # Joints 2,3,4,5
                    # Map Chero joints 2,3,4,5 to DoF16 joints 8,9,10,11 labels
                    dof16_index = i + 6  # 2->8, 3->9, 4->10, 5->11
                    sideLabel = txt(sideNames[dof16_index % 8]) + '\n'
                else:
                    sideLabel = ''
            else:
                if i in range(8, 12):
                    sideLabel = txt(sideNames[i % 8]) + '\n'
                else:
                    sideLabel = ''
                    
            label = Label(self.winCalib,
                          text=sideLabel + '(' + str(i) + ')\n' + txt(scaleNames[i]))

            value = DoubleVar()
            if i in frontJointIdx:
                if self.model == 'BittleX+Arm':
                    LEN = LEN + 30
                sliderBar = Scale(self.winCalib, state=stt, fg='blue', bg=clr, variable=value, orient=ORI,
                                  borderwidth=2, relief='flat', width=8, from_=-25 * tickDirection,
                                  to=25 * tickDirection,
                                  length=LEN, tickinterval=10, resolution=1, repeatdelay=100, repeatinterval=100,
                                  command=lambda value, idx=i: self.setCalib(idx, value))
            else:
                sliderBar = Scale(self.winCalib, state=stt, fg='blue', bg=clr, variable=value, orient=ORI,
                                  borderwidth=2, relief='flat', width=8, from_=-25 * tickDirection, to=25 * tickDirection,
                                  length=LEN, tickinterval=10, resolution=1, repeatdelay=100, repeatinterval=100,
                                  command=lambda value, idx=i: self.setCalib(idx, value))
            self.calibSliders.append(sliderBar)
            
            # Special layout handling for Chero
            if self.model == 'Chero':
                if i < 2:  # Horizontal sliders (Head Pan/Tilt) - use cSPAN=2 like SkillComposer
                    label.grid(row=ROW, column=COL, columnspan=cSPAN, pady=2, sticky=ALIGN)
                else:  # Vertical sliders - use columnspan=1 to prevent overlap
                    label.grid(row=ROW, column=COL, columnspan=1, pady=2, sticky=ALIGN)
            elif i == 2 and scaleNames == BittleRScaleNames:
                autoCalibButton = Button(self.winCalib, text=txt('Auto'), fg='blue',
                                         width=self.calibButtonW, command=lambda cmd='c-2': self.calibFun(cmd))
                label.grid(row=ROW, column=COL, columnspan=2, pady=2, sticky='e')
                autoCalibButton.grid(row=ROW, column=COL+2,  pady=2, sticky='w')    # padx=5,
            else:
                label.grid(row=ROW, column=COL, columnspan=cSPAN, pady=2, sticky=ALIGN)
            sliderBar.grid(row=ROW + 1, column=COL, rowspan=rSPAN, columnspan=cSPAN, sticky=ALIGN)
        time.sleep(3) # wait for the robot to reboot
        self.calibFun('c')
        self.winCalib.update()
        self.calibratorReady = True
        self.winCalib.protocol('WM_DELETE_WINDOW', self.closeCalib)
        self.winCalib.focus_force()    # force the main interface to get focus
        self.winCalib.mainloop()

    def calibFun(self, cmd):
#        global ports
        imageW = self.parameterSet['imageW']

        self.imgPosture.destroy()
        if cmd == 'c' or cmd == 'c-2':
            self.imgPosture = createImage(self.frameCalibButtons, resourcePath + self.model + '_Ruler.jpeg', imageW)
            if cmd == 'c-2':
                send(goodPorts, ['c', [-2], 0])
                time.sleep(1)
                result = send(goodPorts, ['c', 0])
            else:
                result = send(goodPorts, [cmd, 0])
            # print("result:", result)

            if result != -1:
                offsets = result[1]
                print("Raw result:", offsets)
                
                # Better parsing logic for calibration data
                # Look for numeric patterns in the data
                import re
                # Extract all numeric values (including negative numbers)
                numeric_matches = re.findall(r'-?\d+(?:\.\d+)?', offsets)
                # remove the first self.numJoints values
                numeric_matches = numeric_matches[self.numJoints:]
                # print("numeric_matches:", numeric_matches)

                # Filter out values that are clearly not joint offsets
                # Joint offsets should be reasonable values (typically between -50 and 50)
                cleaned_offsets = []
                for match in numeric_matches:
                    try:
                        value = float(match)
                        # Only accept reasonable offset values
                        if -50 <= value <= 50:
                            cleaned_offsets.append(value)
                    except ValueError:
                        continue
                # print("cleaned_offsets:", cleaned_offsets)
                # If we don't have enough valid offsets, try alternative parsing
                if len(cleaned_offsets) < 6:  # Need at least 6 for Chero
                    # Try to find comma-separated values
                    if ',' in offsets:
                        parts = offsets.split(',')
                        for part in parts:
                            try:
                                value = float(part.strip())
                                if -50 <= value <= 50:
                                    cleaned_offsets.append(value)
                            except ValueError:
                                continue
                
                # Ensure we have at least 16 offsets for compatibility
                while len(cleaned_offsets) < 16:
                    cleaned_offsets.append(0.0)
                
                offsets = cleaned_offsets[:self.numJoints]
                # print("cleaned_offsets:", cleaned_offsets)
            else:
                offsets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

            if cmd == 'c-2':
                print("offset2:", offsets[2])
                if int(offsets[2]) > 25:
                    messagebox.showwarning(title=txt('Warning'), message=txt('AutoCali failed'))
                else:
                    self.calibSliders[2].set(offsets[2])
            else:
                # For Chero, only set offsets for 6 joints; for others, set all 16
                if self.model == 'Chero':
                    for i in range(min(6, len(self.calibSliders), len(offsets))):
                        self.calibSliders[i].set(offsets[i])
                else:
                    for i in range(min(16, len(self.calibSliders), len(offsets))):
                        self.calibSliders[i].set(offsets[i])
        elif cmd == 'd':
            self.imgPosture = createImage(self.frameCalibButtons, resourcePath + self.model + '_Rest.jpeg', imageW)
            send(goodPorts, ['d', 0])
        elif cmd == 'balance':
            self.imgPosture = createImage(self.frameCalibButtons, resourcePath + self.model + '_Stand.jpeg', imageW)
            send(goodPorts, ['kbalance', 0])
        elif cmd == 'walk':
            self.imgPosture = createImage(self.frameCalibButtons, resourcePath + self.model + '_Walk.jpeg', imageW)
            send(goodPorts, ['kwkF', 0])

        if self.model == 'Chero':
            self.imgPosture.grid(row=8, column=0, rowspan=3, columnspan=3)
        else:
            self.imgPosture.grid(row=7, column=0, rowspan=3, columnspan=3)

        Hovertip(self.imgPosture, txt('tipImgPosture'))
        self.winCalib.update()

    def setCalib(self, idx, value):
        if self.calibratorReady:
            value = int(value)
            send(goodPorts, ['c', [idx, value], 0])

    def closeCalib(self):
        confirm = messagebox.askyesnocancel(title=None, message=txt('Do you want to save the offsets?'),
                                            default=messagebox.YES)
        if confirm is not None:
#            global ports
            if confirm:
                send(goodPorts, ['s', 0])
            else:
                send(goodPorts, ['a', 0])
            time.sleep(0.1)
            self.calibratorReady = False
            self.calibSliders.clear()
            self.winCalib.destroy()
            closeAllSerial(goodPorts)
            os._exit(0)
            
if __name__ == '__main__':
    goodPorts = {}
    try:
        #        time.sleep(2)
        #        if len(goodPorts)>0:
        #            t=threading.Thread(target=keepReadingSerial,args=(goodPorts,))
        #            t.start()
        model = "Bittle"
        Calibrator(model,language)
        closeAllSerial(goodPorts)
        os._exit(0)
    except Exception as e:
        logger.info("Exception")
        closeAllSerial(goodPorts)
        raise e

