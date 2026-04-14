#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Junfeng Wang
# Petoi LLC
# Jun. 26th, 2024

from tkinter import ttk
import tkinter.font as tkFont
import os
os.environ["PETOI_SHOW_GUI"] = "1"
from PetoiRobot import *


language = languageList['English']

def txt(key):
    return language.get(key, textEN[key])
    
class Debugger:
    def __init__(self,model,lan):
        global language
        language = lan
        smartConnectPorts()
        start = time.time()
        while config.model_ == '':
            if time.time() - start > 5:
                config.model_ = model    # If can not get the model name, use the model set in the UI interface.
            time.sleep(0.01)
        self.configName = config.model_
        
        # Load configuration from file
        try:
            with open(defaultConfPath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            lines = [line.split('\n')[0] for line in lines]  # remove the '\n' at the end of each line
            self.defaultLan = lines[0]
            self.defaultPath = lines[2]
            self.defaultSwVer = lines[3]
            self.defaultBdVer = lines[4]
            self.defaultMode = lines[5]
            if len(lines) >= 8:
                self.defaultCreator = lines[6]
                self.defaultLocation = lines[7]
            else:
                self.defaultCreator = txt('Nature')
                self.defaultLocation = txt('Earth')
            
            self.configuration = [self.defaultLan, self.configName, self.defaultPath, self.defaultSwVer, self.defaultBdVer,
                                  self.defaultMode, self.defaultCreator, self.defaultLocation]
        except Exception as e:
            print('Create configuration file')
            self.defaultLan = 'English'
            self.defaultPath = releasePath[:-1]
            self.defaultSwVer = '2.0'
            self.defaultBdVer = NyBoard_version
            self.defaultMode = 'Standard'
            self.defaultCreator = txt('Nature')
            self.defaultLocation = txt('Earth')
            self.configuration = [self.defaultLan, self.configName, self.defaultPath, self.defaultSwVer, self.defaultBdVer,
                                  self.defaultMode, self.defaultCreator, self.defaultLocation]

        self.winDebug = Tk()
        self.debuggerReady = False
        self.dialogType = "voiceRst"
        self.strStatus = StringVar()
        
        # Serial port related variables
        self.availablePorts = []
        self.currentPort = None
        self.isConnected = False
        self.receiveThread = None
        self.stopReceiveThread = False
        self.autoscroll = BooleanVar(value=True)
        self.showTimestamp = BooleanVar(value=False)
        self.portCheckingThread = None
        self.stopPortChecking = False

        self.OSname = self.winDebug.call('tk', 'windowingsystem')
        if self.OSname == 'win32':
            # Windows
            self.winDebug.iconbitmap(resourcePath + 'Petoi.ico')
            self.winDebug.geometry('760x700+330+100')
        elif self.OSname == 'aqua':
            # macOS - slightly different size and position for Retina displays
            self.winDebug.geometry('780x720+300+80')
            self.backgroundColor = 'gray'
        else:
            # Linux
            self.winDebug.tk.call('wm', 'iconphoto', self.winDebug._w, "-default",
                                PhotoImage(file= resourcePath + 'Petoi.png'))
            self.winDebug.geometry('800x720+280+80')

        self.myFont = tkFont.Font(
            family='Times New Roman', size=20, weight='bold')
        self.normalFont = tkFont.Font(family='Arial', size=12)
        self.winDebug.title(txt('Debugger'))
        self.createMenu()
        
        # Configure main window columns for responsive layout
        # Column 0 and 2 have weight=0 to keep fixed width, column 1 has weight=1 to match window width changes
        # This ensures text box width changes match window width changes
        self.winDebug.columnconfigure(0, weight=0)
        self.winDebug.columnconfigure(1, weight=1, minsize=400)  # Column 1 expands to match window width changes
        self.winDebug.columnconfigure(2, weight=0)
        
        # Row 0: Model label
        self.modelLabel = Label(self.winDebug, text=displayName(self.configName), font=self.myFont)
        self.modelLabel.grid(row=0, column=0, columnspan=3, pady=10)

        # Row 1: Reset voice module button (centered)
        bw = 23
        voiceResetButton = Button(self.winDebug, text=txt('Reset voice module'), font=self.myFont, fg='blue',
                                  width=bw, relief='raised',command=lambda: self.resetVoice())
        voiceResetButton.grid(row=1, column=1, pady=(0, 10))
        tip(voiceResetButton, txt('tipRstVoice'))

        # Row 2: Calibrate gyroscope button (centered)
        imuCaliButton = Button(self.winDebug, text=txt('Calibrate gyroscope'), font=self.myFont, fg='blue', width=bw,
                               relief='raised',
                               command=lambda: self.imuCali())
        imuCaliButton.grid(row=2, column=1, pady=(0, 10))
        tip(imuCaliButton, txt('tipImuCali'))
        
        # Store reference to button for later width matching
        self.refButton = imuCaliButton

        # Row 3: Serial port selection and connection status (aligned with buttons above)
        self.fmSerial = Frame(self.winDebug)
        self.fmSerial.grid(row=3, column=1, pady=(0, 10))
        
        # Get available ports
        self.updateAvailablePorts()
        
        # Connection status button - create first to measure its width
        self.connectBtn = Button(self.fmSerial, text=txt('Connected') if self.isConnected else txt('Connect'),
                                fg='green' if self.isConnected else 'red',
                                relief=SUNKEN if self.isConnected else RAISED,
                                font=self.normalFont, width=12,
                                command=self.toggleConnection)
        self.connectBtn.pack(side=RIGHT, padx=(2, 0))
        
        # Serial port combobox - will fill remaining space
        self.portCombo = ttk.Combobox(self.fmSerial, values=self.availablePorts, state='readonly', 
                                      font=self.normalFont)
        self.portCombo.pack(side=LEFT, fill=X, expand=True, padx=(0, 2))
        # Bind selection change event
        self.portCombo.bind('<<ComboboxSelected>>', self.onPortSelectionChanged)
        if len(goodPorts) > 0:
            # Set default to first connected port
            firstPort = list(goodPorts.values())[0]
            if firstPort in self.availablePorts:
                self.portCombo.set(firstPort)
                self.currentPort = list(goodPorts.keys())[0]
                self.isConnected = True
                # Update button state to reflect connection
                self.connectBtn.config(text=txt('Connected'), fg='green', relief=SUNKEN)
        elif len(self.availablePorts) > 0:
            self.portCombo.set(self.availablePorts[0])

        # Row 4: Status bar
        fmStatus = ttk.Frame(self.winDebug)
        fmStatus.grid(row=4, column=1, ipadx=2, pady=5, sticky=W + E)
        fmStatus.columnconfigure(0, weight=1)  # Allow status bar to expand
        self.statusBar = ttk.Label(fmStatus, textvariable=self.strStatus, font=('Arial', 14), relief=SUNKEN)
        self.statusBar.grid(row=0, column=0, ipadx=5, sticky=W + E)
        
        # Row 5-7: Main terminal frame (contains input, output, and controls)
        fmSerialMonitor = ttk.Frame(self.winDebug)
        fmSerialMonitor.grid(row=5, column=1, pady=(5, 10), sticky=W + E + N + S)
        
        # Command input frame
        fmInput = ttk.Frame(fmSerialMonitor)
        fmInput.grid(row=0, column=0, pady=(0, 5), sticky=W + E)
        
        self.cmdInput = Entry(fmInput, font=self.normalFont)
        self.cmdInput.grid(row=0, column=0, sticky=W + E, padx=(0, 5))
        self.cmdInput.bind('<Return>', lambda e: self.sendCommand())
        
        self.sendBtn = Button(fmInput, text=txt('Send'), font=self.normalFont, width=10,
                             command=self.sendCommand)
        self.sendBtn.grid(row=0, column=1)
        
        fmInput.columnconfigure(0, weight=1)
        
        # Output text frame
        fmOutput = ttk.Frame(fmSerialMonitor)
        fmOutput.grid(row=1, column=0, pady=(0, 5), sticky=W + E + N + S)
        
        # Text widget with vertical and horizontal scrollbars
        vScrollbar = Scrollbar(fmOutput, orient=VERTICAL)
        vScrollbar.grid(row=0, column=1, sticky=N + S)
        
        hScrollbar = Scrollbar(fmOutput, orient=HORIZONTAL)
        hScrollbar.grid(row=1, column=0, sticky=W + E)
        
        # Use tabstops with character units for precise column alignment
        # Set tab stops every 3 characters to accommodate varying field widths:
        # - First row: 1-2 char numbers (0, 1, 10, 11, etc.)
        # - Second row: 2-3 char numbers with commas (3,, 0,, -3,, etc.)
        # With 3-char tab stops, all fields align properly regardless of width
        # Each field + tab will jump to the next 3-char tab stop, ensuring column alignment
        # Character units ensure consistent alignment in monospace font
        # This spacing ensures uniform spacing between all numbers
        tabstops = tuple([f'{i * 2}c' for i in range(1, 50)])  # Create 50 tab stops, 2 chars apart
        # Set wrap='none' to disable automatic word wrapping and show horizontal scrollbar
        self.outputText = Text(fmOutput, height=15, width=90, font=('Courier New', 16),
                              yscrollcommand=vScrollbar.set, xscrollcommand=hScrollbar.set,
                              wrap='none', tabs=tabstops)
        self.outputText.grid(row=0, column=0, sticky=W + E + N + S)
        vScrollbar.config(command=self.outputText.yview)
        hScrollbar.config(command=self.outputText.xview)
        
        fmOutput.columnconfigure(0, weight=1)
        fmOutput.rowconfigure(0, weight=1)
        
        # Control buttons frame
        fmControls = ttk.Frame(fmSerialMonitor)
        fmControls.grid(row=2, column=0, sticky=W + E)
        fmControls.columnconfigure(2, weight=1)  # Allow middle column to expand, pushing buttons to right
        
        # Left side: checkboxes
        self.autoscrollCheck = Checkbutton(fmControls, text=txt('Autoscroll'), 
                                          variable=self.autoscroll, font=self.normalFont)
        self.autoscrollCheck.grid(row=0, column=0, padx=(0, 10), sticky=W)
        
        self.timestampCheck = Checkbutton(fmControls, text=txt('Show timestamp'),
                                         variable=self.showTimestamp, font=self.normalFont)
        self.timestampCheck.grid(row=0, column=1, padx=(0, 10), sticky=W)
        
        # Right side: copy and clear buttons
        self.copyBtn = Button(fmControls, text=txt('Copy'), font=self.normalFont, width=12,
                             command=self.copyOutput)
        self.copyBtn.grid(row=0, column=3, padx=(0, 5), sticky=E)
        
        self.clearBtn = Button(fmControls, text=txt('Clear output'), font=self.normalFont, width=12,
                              command=self.clearOutput)
        self.clearBtn.grid(row=0, column=4, sticky=E)
        
        # Configure terminal frame to expand
        fmSerialMonitor.columnconfigure(0, weight=1)  # Allow column 0 to expand horizontally
        fmSerialMonitor.rowconfigure(1, weight=1)  # Allow row 1 (output text) to expand vertically
        
        # Set row weights to enable expandable space
        self.winDebug.rowconfigure(5, weight=1)  # Allow row 5 (serial monitor) to expand vertically

        self.debuggerReady = True
        
        # Start serial receive thread if connected
        if self.isConnected:
            self.startReceiveThread()
        
        # Start port checking thread
        self.startPortCheckingThread()
        
        self.winDebug.protocol('WM_DELETE_WINDOW', self.on_closing)
        self.winDebug.update()
        
        # Now that window is rendered, match frame width to button width
        self.matchSerialFrameWidth()
        
        self.winDebug.resizable(True, True)
        self.winDebug.focus_force()    # force the main interface to get focus
        self.winDebug.mainloop()
        
    
    def createMenu(self):
        self.menubar = Menu(self.winDebug, background='#ff8000', foreground='black', activebackground='white',
                            activeforeground='black')
        file = Menu(self.menubar, tearoff=0, background='#ffcc99', foreground='black')
        for m in modelOptions:
            file.add_command(label=m, command=lambda model=m: self.changeModel(model))
        self.menubar.add_cascade(label=txt('Model'), menu=file)

        lan = Menu(self.menubar, tearoff=0)
        for l in languageList:
            lan.add_command(label=languageList[l]['lanOption'], command=lambda lanChoice=l: self.changeLan(lanChoice))
        self.menubar.add_cascade(label=txt('lanMenu'), menu=lan)

        helpMenu = Menu(self.menubar, tearoff=0)
        helpMenu.add_command(label=txt('About'), command=self.showAbout)
        self.menubar.add_cascade(label=txt('Help'), menu=helpMenu)

        self.winDebug.config(menu=self.menubar)


    def changeModel(self, modelName):
        if self.debuggerReady and modelName != self.configName:
            self.configName = modelName
            self.modelLabel.configure(text=modelName)
            # Save configuration
            self.saveConfig(defaultConfPath)
        
    
    def changeLan(self, l):
        global language
        if self.debuggerReady and txt('lan') != l:
            # Get current status bar text before language change
            currentStatus = self.strStatus.get()
            
            language = copy.deepcopy(languageList[l])
            self.defaultLan = l
            self.menubar.destroy()
            self.createMenu()
            self.winDebug.title(txt('Debugger'))
            self.winDebug.winfo_children()[1].config(text=txt('Reset voice module'))
            tip(self.winDebug.winfo_children()[1], txt('tipRstVoice'))
            self.winDebug.winfo_children()[2].config(text=txt('Calibrate gyroscope'))
            tip(self.winDebug.winfo_children()[2], txt('tipImuCali'))
            
            # Update connection button text based on current state
            self.connectBtn.config(text=txt('Connected') if self.isConnected else txt('Connect'))
            
            # Update other UI elements
            self.sendBtn.config(text=txt('Send'))
            self.autoscrollCheck.config(text=txt('Autoscroll'))
            self.timestampCheck.config(text=txt('Show timestamp'))
            self.copyBtn.config(text=txt('Copy'))
            self.clearBtn.config(text=txt('Clear output'))
            
            # Re-translate status bar text if it matches known translation keys
            if currentStatus and currentStatus.strip():
                self._retranslateStatusBar(currentStatus)
            
            # Save configuration
            self.saveConfig(defaultConfPath)
    
    def _retranslateStatusBar(self, currentStatus):
        """Re-translate status bar text when language changes"""
        # List of status message keys that might be displayed
        statusKeys = [
            'Copied selected text to clipboard',
            'Copied all output to clipboard',
            'No output to copy',
            'Failed to copy',
            'Output cleared',
            'Failed to send command',
            'Reset voice module',
            'Calibrate gyroscope',
            'calibrating IMU',
            'Reset successfully',
            'IMU Calibration successfully',
            'IMU Calibration failed'
        ]
        
        # Check if current status matches any translation of these keys in any language
        for key in statusKeys:
            # Check against all languages to find which key this status corresponds to
            for langDict in languageList.values():
                translatedValue = langDict.get(key, '')
                if translatedValue and currentStatus == translatedValue:
                    # Found matching key - re-translate with new language
                    self.strStatus.set(txt(key))
                    return
        
        # Check for status messages with additional info (format: "Key: value" or "Key value")
        # Check for "Sent: cmd" pattern - try all languages
        for langDict in languageList.values():
            sentText = langDict.get('Sent', '')
            if sentText and currentStatus.startswith(sentText + ':'):
                cmd = currentStatus.split(':', 1)[-1].strip()
                if cmd:
                    self.strStatus.set(f'{txt("Sent")}: {cmd}')
                    return
        
        # Check for "Connected to port" pattern
        for langDict in languageList.values():
            connectedText = langDict.get('Connected to', '')
            if connectedText and currentStatus.startswith(connectedText):
                # Extract port name (everything after "Connected to")
                portName = currentStatus[len(connectedText):].strip()
                if portName:
                    self.strStatus.set(f'{txt("Connected to")} {portName}')
                    return
        
        # Check for "Disconnected from port" pattern
        for langDict in languageList.values():
            disconnectedText = langDict.get('Disconnected from', '')
            if disconnectedText and currentStatus.startswith(disconnectedText):
                # Extract port name (everything after "Disconnected from")
                portName = currentStatus[len(disconnectedText):].strip()
                if portName:
                    self.strStatus.set(f'{txt("Disconnected from")} {portName}')
                    return
        
        # Check for "Failed to open port: port" pattern
        for langDict in languageList.values():
            failedText = langDict.get('Failed to open port', '')
            if failedText and currentStatus.startswith(failedText + ':'):
                portName = currentStatus.split(':', 1)[-1].strip()
                if portName:
                    self.strStatus.set(f'{txt("Failed to open port")}: {portName}')
                    return
            
    
    def showAbout(self):
        messagebox.showinfo(txt('titleVersion'), txt('msgVersion'))
        self.winDebug.focus_force()

            
    def createImage(self, frame, imgFile, imgW):
        img = Image.open(imgFile)

        ratio = img.size[0] / imgW
        img = img.resize((imgW, round(img.size[1] / ratio)))
        image = ImageTk.PhotoImage(img)
        imageFrame = Label(frame, image=image)
        imageFrame.image = image
        return imageFrame


    def resetVoice(self):
        if self.debuggerReady == 1:
            if not self.isConnected or not self.currentPort:
                messagebox.showwarning(txt('Warning'), txt('Please connect to a serial port first'))
                return
            
            cmd = "XAc"
            try:
                self.currentPort.Send_data(self.encode(cmd))
                self.displayOutput(f">> {cmd}")
                self.strStatus.set(txt('Reset voice module'))
                self.statusBar.update()
                self.dialogType = "voiceRst"
                self.showDialog(self.dialogType)
            except Exception as e:
                messagebox.showerror(txt('Error'), f'{txt("Error")}: {str(e)}')

    def imuCali(self):
        if self.debuggerReady == 1:
            if not self.isConnected or not self.currentPort:
                messagebox.showwarning(txt('Warning'), txt('Please connect to a serial port first'))
                return
            
            cmd = "d"
            try:
                self.currentPort.Send_data(self.encode(cmd))
                self.displayOutput(f">> {cmd}")
                self.strStatus.set(txt('Calibrate gyroscope'))
                self.statusBar.update()
                self.dialogType = "imuCali"
                self.showDialog(self.dialogType)
            except Exception as e:
                messagebox.showerror(txt('Error'), f'{txt("Error")}: {str(e)}')


    def showDialog(self, dialogType='voiceRst'):
        # Declare a global variable to access it within the function
        # Create the dialog window
        self.dialogWin = Toplevel(self.winDebug)
        self.dialogWin.title(txt('Warning'))
        self.dialogWin.geometry('680x320')

        fmDialog = Frame(self.dialogWin)  # relief=GROOVE to draw border
        fmDialog.grid(ipadx=3, ipady=3, padx=3, pady=5, sticky=W + E)

        if self.dialogType == "voiceRst":
            # creator label
            infoLabel = Label(fmDialog, text=txt('Voice indicates'), justify='left')
            infoLabel.grid(row=0, columnspan=2, padx=2, pady=6, sticky=W)

            # Load the image
            frameImage = self.createImage(fmDialog, resourcePath + 'VoiceSwitch.jpeg', 200)
            frameImage.grid(row=1, columnspan=2,pady=5)
        elif self.dialogType == "imuCali":
            # creator label
            infoLabel = Label(fmDialog, text=txt('IMU indicates'), justify='left')
            infoLabel.grid(row=0, columnspan=2, padx=2, pady=6, sticky=W)

            # Load the image
            frameImage = self.createImage(fmDialog, resourcePath + 'rest.jpeg', 200)
            frameImage.grid(row=1, columnspan=2, pady=5)

        # Create the buttons
        yesButton = tk.Button(fmDialog, text=txt('Yes'), width=10, command=lambda bFlag = True: self.getButtonClick(bFlag))
        yesButton.grid(row=2, column=0,  padx=3, pady=10)


        noButton = tk.Button(fmDialog, text=txt('No'), width=10, command=lambda bFlag = False: self.getButtonClick(bFlag))
        noButton.grid(row=2, column=1, padx=3, pady=10)

        self.dialogWin.mainloop()  # Start the event loop for the dialog window


    def encode(self, in_str, encoding='utf-8'):
        if isinstance(in_str, bytes):
            return in_str
        else:
            return in_str.encode(encoding)


    def getButtonClick(self, buttonValue):
        """Function to handle button clicks and close the window."""
        logger.debug(f"returnVal is {buttonValue}")
        self.dialogWin.destroy()  # Destroy the window
        if self.debuggerReady == 1:
            if self.dialogType == "voiceRst":
                if buttonValue == True:
                    if 'Chinese'in txt('lan'):
                        cmdList = ["XAa", "XAb"]
                    else:
                        cmdList = ["XAb", "XAa"]

                    for cmd in cmdList:
                        if self.currentPort:
                            self.currentPort.Send_data(self.encode(cmd))
                            self.displayOutput(f">> {cmd}")
                            self.winDebug.update()  # Force UI update
                        if cmd == cmdList[0]:
                            time.sleep(2)
                        else:
                            txtResult = txt('Reset successfully')
                            self.strStatus.set(txtResult)
                            self.statusBar.update()
                            messagebox.showinfo(None, txtResult)
                else:
                    self.strStatus.set(' ')
                    self.statusBar.update()
            elif self.dialogType == "imuCali":
                if buttonValue == True:
                    self.strStatus.set(txt('calibrating IMU'))
                    self.statusBar.update()
                    
                    # Temporarily pause the receive thread to avoid competition
                    wasReceiving = False
                    if self.receiveThread and self.receiveThread.is_alive():
                        wasReceiving = True
                        self.stopReceiveThread = True
                        time.sleep(0.1)  # Give thread time to stop
                    
                    if self.currentPort:
                        self.currentPort.Send_data(self.encode("gc"))
                        self.displayOutput(">> gc")
                    
                    # Create a flag variable to track whether calibration is successful.
                    calibration_success = False
                    # Set timeout (seconds):
                    timeout = 20
                    start_time = time.time()
                    
                    # Monitor serial output in real-time:
                    while time.time() - start_time < timeout:
                        # Brief pause to avoid high CPU usage.
                        time.sleep(0.01)
                        # Update UI to keep it responsive
                        self.winDebug.update()
                        
                        # Check current port
                        if self.currentPort and self.currentPort.main_engine.in_waiting > 0:
                            try:
                                # Read serial data of each line
                                data = self.currentPort.main_engine.readline()
                                data_str = data.decode('ISO-8859-1').strip()
                                # Display output in text widget
                                if data_str:
                                    self.displayOutput(data_str)
                                
                                # Check the successful calibration information in the serial output.
                                if "Calibration done" in data_str:
                                    calibration_success = True
                                    break
                            except Exception as e:
                                logger.error(f"Error reading serial data: {e}")
                        
                        # If calibration is successful, exit the loop.
                        if calibration_success:
                            break
                    
                    # Restart receive thread if it was running
                    if wasReceiving:
                        self.startReceiveThread()

                    # Show a message according to the calibration results.
                    if calibration_success:
                        txtResult = txt('IMU Calibration successfully')
                    else:
                        txtResult = txt('IMU Calibration failed')

                    # Update status bar first, then show messagebox
                    self.strStatus.set(txtResult)
                    self.statusBar.update()
                    messagebox.showinfo('Petoi Desktop App', txtResult)
                else:
                    self.strStatus.set(' ')
                    self.statusBar.update()

    def matchSerialFrameWidth(self):
        """Match serial frame width to reference button width"""
        try:
            buttonWidth = self.refButton.winfo_width()
            if buttonWidth > 0:
                # Set frame to exact button width
                self.fmSerial.config(width=buttonWidth, height=self.connectBtn.winfo_reqheight())
                self.fmSerial.pack_propagate(False)  # Prevent frame from resizing
        except:
            pass
    
    def updateAvailablePorts(self):
        """Update the list of available serial ports"""
        allPorts = Communication.Print_Used_Com()
        self.availablePorts = [p.split('/')[-1] for p in allPorts]
    
    def onPortSelectionChanged(self, event=None):
        """Handle port selection change in combobox"""
        if not self.debuggerReady:
            return
        
        selectedPortName = self.portCombo.get()
        if not selectedPortName:
            return
        
        # Check if currently connected and selected port is different from connected port
        if self.isConnected and self.currentPort:
            # Get the port name of currently connected port
            currentPortName = None
            # First try to get from goodPorts dictionary
            if self.currentPort in goodPorts:
                currentPortName = goodPorts[self.currentPort]
            else:
                # Try to find port name by matching serial object
                for serialObj, portName in goodPorts.items():
                    if serialObj == self.currentPort:
                        currentPortName = portName
                        break
            
            # If we couldn't find the port name, check if currentPort is still valid
            # If selected port is different from connected port, disconnect
            if currentPortName:
                if selectedPortName != currentPortName:
                    # Selected different port, disconnect current connection
                    # Pass the current port name to show correct status message
                    self.disconnectPort(portName=currentPortName)
            else:
                # Current port not found in goodPorts, disconnect anyway
                # This handles edge cases where port might have been disconnected externally
                self.disconnectPort()
        
    def toggleConnection(self):
        """Toggle serial port connection"""
        if self.isConnected:
            # Disconnect
            self.disconnectPort()
        else:
            # Connect
            self.connectSerialPort()
    
    def connectSerialPort(self):
        """Connect to selected serial port using testPort()"""
        portName = self.portCombo.get()
        if not portName:
            messagebox.showwarning(txt('Warning'), txt('Please select a serial port'))
            return
        
        # Disable button during connection attempt
        self.connectBtn.config(state='disabled')
        self.strStatus.set(f'{txt("Testing port")} {portName}...')
        
        def testPortInThread():
            """Test port in background thread"""
            serialObj = None
            try:
                # Find full port path
                allPorts = Communication.Print_Used_Com()
                fullPath = None
                for p in allPorts:
                    if p.split('/')[-1] == portName or p == portName:
                        fullPath = p
                        break
                
                if fullPath is None:
                    fullPath = portName
                
                # Create serial connection
                serialObj = Communication(fullPath, 115200, 1)
                
                if not serialObj.main_engine or not serialObj.main_engine.is_open:
                    raise Exception("Failed to open port")
                
                # Store serialObj reference before calling testPort
                # testPort will add it to goodPorts if successful
                serialObjBeforeTest = serialObj
                
                # Call testPort to test if it's a Petoi device
                # testPort will add serialObj to goodPorts if successful
                # If not a Petoi device, testPort will close the port but not raise exception
                # If exception occurs, it means port cannot be opened
                testPort(goodPorts, serialObj, portName)
                
                # Check if port was added to goodPorts (success)
                if serialObjBeforeTest in goodPorts:
                    # Successfully connected to Petoi device
                    # Use default parameter to capture variable values in closure
                    self.winDebug.after(0, lambda obj=serialObjBeforeTest, name=portName: self.onPortConnected(obj, name))
                else:
                    # Port was tested but not added (not a Petoi device)
                    # testPort already closed the port, so we don't need to close it again
                    # Use default parameter to capture variable value in closure
                    self.winDebug.after(0, lambda name=portName: self.onPortNotPetoiDevice(name))
                    
            except Exception as e:
                # Exception occurred (port cannot be opened)
                # Make sure to close the port if it was opened
                if serialObj and serialObj.main_engine and serialObj.main_engine.is_open:
                    try:
                        serialObj.Close_Engine()
                    except:
                        pass
                # Use default parameter to capture variable values in closure
                # This prevents "free variable referenced before assignment" error
                errorMsg = str(e)
                self.winDebug.after(0, lambda name=portName, msg=errorMsg: self.onPortOpenFailed(name, msg))
        
        # Run testPort in background thread
        testThread = threading.Thread(target=testPortInThread, daemon=True)
        testThread.start()
    
    def onPortConnected(self, serialObj, portName):
        """Handle successful port connection"""
        # Stop any existing receive thread
        if self.receiveThread and self.receiveThread.is_alive():
            self.stopReceiveThread = True
            self.receiveThread.join(timeout=0.5)
        
        self.currentPort = serialObj
        self.isConnected = True
        
        # Update button state
        self.connectBtn.config(text=txt('Connected'), fg='green', relief=SUNKEN, state='normal')
        # Format: "Connected to" + serial port name (no space)
        connectedText = txt("Connected to")
        self.strStatus.set(f'{connectedText}{portName}')
        
        # Start receive thread
        self.startReceiveThread()
    
    def onPortNotPetoiDevice(self, portName):
        """Handle case when port is not a Petoi device"""
        self.connectBtn.config(text=txt('Connect'), fg='red', relief=RAISED, state='normal')
        # Use translation with portName placeholder
        statusText = txt('Port is not connected to a Petoi device')
        self.strStatus.set(statusText.format(portName=portName))
    
    def onPortOpenFailed(self, portName, errorMsg):
        """Handle case when port cannot be opened"""
        self.connectBtn.config(text=txt('Connect'), fg='red', relief=RAISED, state='normal')
        # Use translation with portName placeholder
        statusText = txt('Port cannot be opened')
        self.strStatus.set(statusText.format(portName=portName))
    
    def disconnectPort(self, portName=None):
        """Disconnect from current serial port"""
        if self.currentPort:
            try:
                # Get port name before disconnecting
                disconnectedPortName = portName
                if not disconnectedPortName:
                    # Try to get port name from goodPorts
                    if self.currentPort in goodPorts:
                        disconnectedPortName = goodPorts[self.currentPort]
                    else:
                        # Fallback to current combobox selection
                        disconnectedPortName = self.portCombo.get()
                
                # Stop receive thread
                self.stopReceiveThread = True
                if self.receiveThread and self.receiveThread.is_alive():
                    self.receiveThread.join(timeout=1)
                
                # Close serial port
                if self.currentPort.main_engine and self.currentPort.main_engine.is_open:
                    self.currentPort.main_engine.close()
                
                # Remove from goodPorts
                if self.currentPort in goodPorts:
                    del goodPorts[self.currentPort]
                
                self.currentPort = None
                self.isConnected = False
                
                # Update button state
                self.connectBtn.config(text=txt('Connect'), fg='red', relief=RAISED)
                if disconnectedPortName:
                    # Format: "Disconnected from" + serial port name (no space)
                    disconnectedText = txt("Disconnected from")
                    self.strStatus.set(f'{disconnectedText}{disconnectedPortName}')
                
            except Exception as e:
                messagebox.showerror(txt('Error'), f'{txt("Error")}: {str(e)}')
    
    def startReceiveThread(self):
        """Start thread to receive serial data"""
        self.stopReceiveThread = False
        self.receiveThread = threading.Thread(target=self.receiveSerialData, daemon=True)
        self.receiveThread.start()
    
    def receiveSerialData(self):
        """Receive and display serial data"""
        while not self.stopReceiveThread and self.currentPort:
            try:
                if self.currentPort.main_engine and self.currentPort.main_engine.is_open:
                    if self.currentPort.main_engine.in_waiting > 0:
                        data = self.currentPort.main_engine.readline()
                        try:
                            data_str = data.decode('ISO-8859-1').strip()
                            if data_str:
                                self.displayOutput(data_str)
                        except:
                            pass
                time.sleep(0.01)
            except Exception as e:
                if not self.stopReceiveThread:
                    logger.error(f"Error receiving serial data: {e}")
                break
    
    def normalizeTabFields(self, message):
        """Normalize tab-separated fields for consistent alignment
        Returns normalized message string with aligned fields, or None if no tabs found
        """
        if '\t' not in message:
            return None
        
        fields = message.split('\t')
        normalized_fields = []
        # Use fixed width for number part to ensure digit alignment
        # CRITICAL: Numbers should align by their last digit, not by comma
        # All fields use TOTAL_WIDTH = 5 characters for consistent column alignment
        # Fields without comma: number right-aligned to 4 chars + 1 space = 5 chars total
        # Fields with comma: number right-aligned to 4 chars + 1 comma = 5 chars total
        NUMBER_WIDTH = 4  # Width for number part (right-aligned)
        for field in fields:
            field = field.strip()
            # Check if field ends with comma
            if field.endswith(','):
                # Separate number part and comma
                number_part = field[:-1]  # Remove trailing comma
                # Right-align the number part, then append comma
                # This ensures the last digit aligns with numbers above, comma follows
                normalized_field = f"{number_part:>{NUMBER_WIDTH}},"
            else:
                # No comma, right-align number to NUMBER_WIDTH, then add space to match TOTAL_FIELD_WIDTH
                # This ensures consistent column width and digit alignment
                normalized_field = f"{field:>{NUMBER_WIDTH}} "
            normalized_fields.append(normalized_field)
        
        # Use fixed spacing (2 spaces) between fields for consistent spacing
        field_separator = ' ' * 2
        return field_separator.join(normalized_fields)
    
    def displayOutput(self, message):
        """Display message in output text widget"""
        if self.showTimestamp.get():
            timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            # For sent commands (starting with ">> "), don't use " -> " separator
            if message.startswith(">> "):
                self.outputText.insert(END, f"[{timestamp}] {message}\n")
            else:
                # Normalize tab-separated fields for consistent alignment
                normalized_message = self.normalizeTabFields(message)
                if normalized_message is not None:
                    # Use normalized message with aligned fields
                    timestamp_prefix = f"[{timestamp}] -> "
                    initial_spacing = ' ' * 2  # 2 spaces after timestamp prefix (same as field spacing)
                    self.outputText.insert(END, f"{timestamp_prefix}{initial_spacing}{normalized_message}\n")
                else:
                    # No tabs in message, use as is
                    self.outputText.insert(END, f"[{timestamp}] -> {message}\n")
        else:
            # Apply same field alignment logic when timestamp is disabled
            normalized_message = self.normalizeTabFields(message)
            if normalized_message is not None:
                # Use normalized message with aligned fields
                self.outputText.insert(END, normalized_message + '\n')
            else:
                # No tabs in message, use as is
                self.outputText.insert(END, message + '\n')
        
        if self.autoscroll.get():
            self.outputText.see(END)
        
        # Force update to display immediately
        self.outputText.update_idletasks()
    
    def sendCommand(self):
        """Send command from input field"""
        cmd = self.cmdInput.get().strip()
        if not cmd:
            return
        
        if not self.isConnected or not self.currentPort:
            messagebox.showwarning(txt('Warning'), txt('Please connect to a serial port first'))
            return
        
        try:
            # Send command
            self.currentPort.Send_data(self.encode(cmd))
            
            # Display sent command (using displayOutput for consistent formatting)
            self.displayOutput(f">> {cmd}")
            
            # Clear input field
            self.cmdInput.delete(0, END)
            
            self.strStatus.set(f'{txt("Sent")}: {cmd}')
            
        except Exception as e:
            messagebox.showerror(txt('Error'), f'{txt("Error")}: {str(e)}')
            self.strStatus.set(txt('Failed to send command'))
    
    def copyOutput(self):
        """Copy selected text or all text from output widget to clipboard"""
        try:
            # Check if there is selected text
            if self.outputText.tag_ranges('sel'):
                # Get selected text
                selected_text = self.outputText.get('sel.first', 'sel.last')
                # Copy to clipboard
                self.winDebug.clipboard_clear()
                self.winDebug.clipboard_append(selected_text)
                self.strStatus.set(txt('Copied selected text to clipboard'))
            else:
                # No selection, copy all text
                all_text = self.outputText.get('1.0', END)
                # Remove the last newline that Text widget always adds
                all_text = all_text.rstrip('\n')
                if all_text:
                    self.winDebug.clipboard_clear()
                    self.winDebug.clipboard_append(all_text)
                    self.strStatus.set(txt('Copied all output to clipboard'))
                else:
                    self.strStatus.set(txt('No output to copy'))
        except Exception as e:
            messagebox.showerror(txt('Error'), f'{txt("Error")}: {str(e)}')
            self.strStatus.set(txt('Failed to copy'))
    
    def clearOutput(self):
        """Clear output text widget"""
        self.outputText.delete('1.0', END)
        self.strStatus.set(txt('Output cleared'))

    def saveConfig(self, filename):
        """Save configuration to file"""
        self.configuration = [self.defaultLan, self.configName, self.defaultPath, self.defaultSwVer, self.defaultBdVer,
                              self.defaultMode, self.configuration[6], self.configuration[7]]
        saveConfigToFile(self.configuration, filename)
    
    def checkPortStatus(self):
        """Check current selected port status and update UI accordingly"""
        if not self.debuggerReady:
            return
        
        selectedPortName = self.portCombo.get()
        if not selectedPortName:
            return
        
        # Check if the selected port is in goodPorts
        portFound = False
        matchingSerialObj = None
        
        for serialObj, portName in goodPorts.items():
            if portName == selectedPortName:
                portFound = True
                matchingSerialObj = serialObj
                break
        
        if portFound:
            # Port is available and connected
            # Check if we need to update the connection state
            if self.currentPort != matchingSerialObj or not self.isConnected:
                # Update to use the matching port
                wasConnected = self.isConnected
                self.isConnected = True
                self.currentPort = matchingSerialObj
                
                # Update button to show connected state
                self.connectBtn.config(text=txt('Connected'), fg='green', relief=SUNKEN)
                # Format: "Connected to" + serial port name (no space)
                connectedText = txt("Connected to")
                self.strStatus.set(f'{connectedText}{selectedPortName}')
                
                # Start receive thread if not already running
                if not wasConnected or not self.receiveThread or not self.receiveThread.is_alive():
                    if wasConnected:
                        # Stop old thread first
                        self.stopReceiveThread = True
                        if self.receiveThread and self.receiveThread.is_alive():
                            self.receiveThread.join(timeout=0.5)
                    self.startReceiveThread()
        else:
            # Port is disconnected or not available
            # Check if we need to disconnect (if currently connected to this port)
            shouldDisconnect = False
            if self.isConnected and self.currentPort:
                # Check if currentPort corresponds to the selected port name
                currentPortName = None
                if self.currentPort in goodPorts:
                    currentPortName = goodPorts[self.currentPort]
                # If currentPort is not in goodPorts or doesn't match selected port, disconnect
                if self.currentPort not in goodPorts or currentPortName != selectedPortName:
                    shouldDisconnect = True
            
            if shouldDisconnect:
                self.isConnected = False
                # Stop receive thread
                self.stopReceiveThread = True
                if self.receiveThread and self.receiveThread.is_alive():
                    self.receiveThread.join(timeout=0.5)
                self.currentPort = None
                self.connectBtn.config(text=txt('Connect'), fg='red', relief=RAISED)
                # Format: "Disconnected from" + serial port name (no space)
                disconnectedText = txt("Disconnected from")
                self.strStatus.set(f'{disconnectedText}{selectedPortName}')
            elif not self.isConnected:
                # Already disconnected, just update status if needed
                currentStatus = self.strStatus.get()
                disconnectedText = txt("Disconnected from")
                expectedStatus = f'{disconnectedText}{selectedPortName}'
                if currentStatus != expectedStatus:
                    self.connectBtn.config(text=txt('Connect'), fg='red', relief=RAISED)
                    self.strStatus.set(expectedStatus)
    
    def startPortCheckingThread(self):
        """Start thread to check port status using keepCheckingPort"""
        def updateCallback():
            """Callback function called by keepCheckingPort when port status changes"""
            # Use after() to safely update UI from background thread
            self.winDebug.after(0, self.checkPortStatus)
        
        def portCheckingWrapper():
            """Wrapper to run keepCheckingPort with proper condition"""
            # Create condition that checks if we should continue checking
            cond = lambda: not self.stopPortChecking
            try:
                keepCheckingPort(goodPorts, cond1=cond, check=True, updateFunc=updateCallback)
            except Exception as e:
                logger.error(f"Error in port checking thread: {e}")
        
        self.stopPortChecking = False
        self.portCheckingThread = threading.Thread(target=portCheckingWrapper, daemon=True)
        self.portCheckingThread.start()
    
    def on_closing(self):
        if messagebox.askokcancel(txt('Quit'), txt('Do you want to quit?')):
            # Save configuration before closing
            self.saveConfig(defaultConfPath)
            self.debuggerReady = False
            self.stopReceiveThread = True
            self.stopPortChecking = True
            if self.receiveThread and self.receiveThread.is_alive():
                self.receiveThread.join(timeout=1)
            if self.portCheckingThread and self.portCheckingThread.is_alive():
                self.portCheckingThread.join(timeout=1)
            self.winDebug.destroy()
            closeAllSerial(goodPorts)
            os._exit(0)


if __name__ == '__main__':
    # Do not rebind goodPorts; it must remain the same dict as PetoiRobot.ardSerial.goodPorts (see Calibrator.py).
    # goodPorts = {}
    try:
        model = "Bittle"
        Debugger(model,language)
        closeAllSerial(goodPorts)
        os._exit(0)
    except Exception as e:
        logger.info("Exception")
        closeAllSerial(goodPorts)
        raise e
