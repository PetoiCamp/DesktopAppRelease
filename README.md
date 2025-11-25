# DesktopAppRelease
This repo makes the Petoi Desktop App independent from the original [OpenCat](https://github.com/PetoiCamp/OpenCat-Quadruped-Robot) project. You can find the previous releases in that project. 

Introduction
Petoi Desktop App provides a neat graphical user interface to configure the firmware, calibrate the robot, and design customized motions for your robot. The major function modules are the Firmware Uploader, Joint Calibrator, and Skill Composer.


Download & Installation
You can download the latest version of the desktop App and unzip it.

Before running the app, you must use the included USB adapter or the Bluetooth dongle to connect to a Petoi robot.  You may need to install drivers for USB connection.

Windows
Run the UI.exe in the unzipped folder.  Do NOT move the UI.exe to another location in Windows.

Mac
After downloading the Mac version, you must drag it into the Applications folder. 

If you see the error message that "Petoi Desktop App" cannot be opened because the developer cannot be verified, you can right-click the icon, hold the Shift key, and click Open. If it still doesn't open, go to your System Settings -> Privacy and Security and scroll down. There should be an option to allow the app to run. 


The upgraded macOS has introduced some incompatibility with the GUI library. To click/activate an element in the app's interface, you need to click the element, hold the click, and slightly move your finger, then release. Otherwise, the event cannot be recognized. Sorry for the inconvenience. It's been a known issue between macOS and the popular Tkinter library.



Linux
Please see the next chapter to run the app from a terminal.

Run the app from the Terminal
In the case of compatibility issues, or if you want to modify the source and test, you can also run the code from the Terminal.

The Terminal is a built-in interface on macOS or Linux machines. The equivalent environment on Windows machines is called the Command-Line Tool (CMD). It's recommended that you install Anaconda to manage your Python environment. It can also provide the Powershell as a Terminal for the Windows machines.

Depending on your existing Python configuration, you may need to upgrade to Python 3 and install the following libraries:

pyserial

pillow

You can install them by entering pip3 install pyserial pillow in the Terminal or using the package manager in Anaconda.

To run the code:

In the Terminal, use the cd command to navigate to the OpenCat/pyUI/ folder. You can use the Tab key to auto-complete the path name.

After entering the pyUI/ folder, enter ls and ensure you can see the UI.py and other Python source codes listed.

Enter python3 UI.py.

If you encounter the Python error message "_tkinter.TclError: no display name and no $DISPLAY environment variable", you can try to install python3-tk, tk-dev, and idle3.  

For Linux users,  taking Debian / Ubuntu as an example, the command is as follows:

apt install python3-tk

apt install tk-dev 

apt install idle3

For macOS users, use the following command to install the library:

brew install idle3

After the installation is complete, reboot the computer.

Open Source Codes
The source code is written with Tkinker in Python3 and is open source.

UI.py is the general entry for all the modules:

UI.py

-> FirmwareUploader.py

-> Calibrator.py

-> SkillComposer.py

-> Debugger.py: provides some debugging tools for the Petoi robot.

-> translate.py: provides multi-language support for the UI. You may help to translate the UI into your language.
