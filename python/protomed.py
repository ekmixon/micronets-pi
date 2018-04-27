#!/usr/bin/env python

import sys, time, argparse, logging, atexit
from subprocess import call

from utils.syslogger import SysLogger
logger = SysLogger().logger()

from pio.gbutton import GButton
from pio.gled import GLed
#from pio.gdisp_5110 import GDisp_5110
from pio.gdisp_st7735 import GDisp_st7735
from onboard import *
import threading
from threading import Timer

import RPi.GPIO as GPIO
from PIL import ImageFont
from device_ui import DeviceUI


############################################################
# GPIO 
############################################################

GPIO.setmode(GPIO.BCM)
restoring = False
onboarding = False
batteryLow = 0

display = DeviceUI()

# Demented python scoping.
context = {'restoring':False, 'onboarding':False}

def clickOnboard():
    print "click onboard"
    if context['onboarding']:
        #end_onboard()
        #context['onboarding'] = False
        cancelOnboard()
    else: 
        begin_onboard()
        context['onboarding'] = True

def clickReset():
    restore_defaults()

def shutdown():
    display.clear_messages()
    display.add_message("Shutting Down..")
    time.sleep(1)
    call("sudo shutdown -h now", shell=True)

def lowBattery():
    global batteryLow
    display.clear_messages()
    display.add_message("Low Battery!!!")
    batteryLow = 60

buttonOnboard = GButton(22)
buttonOnboard.set_callback(clickOnboard)

buttonReset = GButton(7)
buttonReset.set_callback(clickReset)

buttonMode = GButton(9)

buttonShutdown = GButton(18, True)
buttonShutdown.set_callback(shutdown)

buttonLowBattery = GButton(15)
buttonLowBattery.set_callback(lowBattery)


# LED pin 25

ledOnboard = GLed(17)

def restore_defaults():
    print "restore defaults"
    display.clear_messages()
    display.add_message("Restore Defaults")

    ledOnboard.blink(.05, 10, restore_complete)
    restoring = True
    resetDevice()

def restore_complete():
    print "end restore"
    display.add_message("Restore Complete")
    restoring = False
    set_state()

def begin_onboard():
    print "begin onboard"
    display.clear_messages()
    display.add_message("Begin Onboard")
    ledOnboard.blink(.1)
    context['onboarding'] = True

    # Read clear private key switch
    newKey = buttonMode.is_set()
    #print "newKey: {}".format(newKey)
    thr = threading.Thread(target=onboardDevice, args=(newKey, end_onboard, status_message,)).start()

def status_message(message):
    display.add_message(message)

def end_onboard(status):
    print "end onboard: {}".format(status)
    display.add_message(status)
    context['onboarding'] = False
    set_state()

def set_state():
    if wpa_subscriber_exists():
        ledOnboard.on()
    else:
        ledOnboard.off()

############################################################
# LED Display
############################################################

def cleanup():
    print("Cleaning up")

    # Clear display
    display.clear_messages()

    # Release GPIO
    GPIO.cleanup()


atexit.register(cleanup)

# Setup power down and low battery monitor
# Have green LED reflect subscriber configured status
set_state()
while True:
    display.refresh()
    time.sleep(1)
    #print "batteryLow: {}".format(batteryLow)
    if batteryLow > 0:
        if (not buttonLowBattery.is_set()):
            print "plugged back in.."
            # plugged back in
            batteryLow = 0
            display.clear_messages()
            display.setLowBattery(batteryLow)
        else:
            # still discharging
            batteryLow = batteryLow - 1
            if batteryLow == 0:
                display.clear_messages()
                display.add_message("Shutting Down..")
                display.refresh()
                time.sleep(1)
                call("sudo shutdown -h now", shell=True)
                shutdown()
            else:
                display.setLowBattery(batteryLow)
                display.update_message("Shutdown in 0:{0:0>2}".format(batteryLow))
        


        


