"""
TODO:

add gc (garbage colllector)
add device_status class to json.dumps
test ntp server (first convert time to meaningful value to see how off...

This program to test an mqtt set-up is designed for a raspberry pico (v1) with W5100S wiznet ethernet hat.

# fix toggle (only turns off..)
# fix vars() to print status...

"""

import sys
import time
import ntptime
from machine import Pin, SPI, reset, RTC
import binascii
import network
import json
import socket
import struct
import gc

from umqttsimple import MQTTClient
from config import *

###############
### CLASSES ###
###############

class Led:
    def __init__(self, pin):
        # set the LED pin
        self.led = Pin(pin, Pin.OUT)
        # set the default state to off
        self.set_state(0)

    ### getters & setters

    def get_state(self):
        return self.led.value()

    def set_state(self, val):
        return self.led.value(val)

    ### basic

    def status(self):
        return "ON" if self.get_state() else "OFF"

    def on(self):
        self.set_state(1)
        return "On."

    def off(self):
        self.set_state(0)
        return "Off."

    def toggle(self):
        self.set_state(not self.get_state())
        return "Toggled."


class LedController:
    def __init__(self, led):
        self.led = led

        self.commands = {
            "STATUS": self.led.status,
            "ON": self.led.on,
            "OFF": self.led.off,
            "TOGGLE": self.led.toggle,
        }

    def execute(self, command):
        if command in self.commands:
            response = self.commands[command]()
            return response
        else:
            return "Invalid command."


class DeviceStatus:
    def __init__(self, led_ctrl):
        self.time = time.localtime()
        self.led = led_ctrl.execute("STATUS")

#################
### FUNCTIONS ###
#################

def w5x00_init():

    print("Initialising W5x00.")

    # w5100s
    # mosi = spio tx = 19
    # miso = spio rx = 21 or 16...
    # sck = clock = 18
    # cs = 17
    # reset = 20
    
    # w5500
    # mosi = 19
    # miso = 16
    # sck = 18
    # cs = 17
    # reset = 20

    spi = SPI(0, 2_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))  # SPI, CS, Reset pins
    nic.active(True)
    print("Nic activated.")

    if static:
        nic.ifconfig((static_ip, netmask, gateway, dns))
    else:
        nic.ifconfig('dhcp')

    while not nic.isconnected():
        time.sleep(1)
        print("Waiting for network...")

    print("Network connected:", nic.ifconfig()[0])
    mac = binascii.hexlify(nic.config('mac'), ':').decode()
    print("Device MAC:", mac)

#####################

def client_init(lc):
    

    print("Initialising MQTT client.")
    client = mqtt_connect(lc)

    return client


def subscript_init(client):
    
    client.subscribe(sub_topic_1)
    client.subscribe(sub_topic_2)


def reset_device(kind):
    
    print(f"{kind} resetting the device")

    kind = kind.upper()

    if kind == 'HARD':
        # Hard
        reset()
    elif kind == "SOFT":
        # Soft
        sys.exit()
    else:
        print("erroneous reset type requested.")

############
### mqtt ###
############

def sub_cb(topic, msg, lc):
    """
    Fix this
    """
    

    command = msg.decode('utf-8').strip().upper()
    print(f"<- {topic.decode()}: {command}")

    # control
    if topic == sub_topic_1:
        # something here....
        pass

    # led
    if topic == sub_topic_2 and command in lc.commands:
        lc.execute(command)


def mqtt_connect(lc):

    attempts = 3

    for i in range(attempts):
        try:
            print(f"Attempt {i + 1}: Connecting to MQTT Broker...")
            client = MQTTClient(client_id, server=mqtt_server, port=port, user=user, password=word, keepalive=60)
            print("Client created.")
            client.set_callback(lambda topic, msg: sub_cb(topic, msg, lc))
            print("Callback (message handler) set.")
            client.connect()
            print(f'Connected to broker ({mqtt_server}) as: {client_id}')
            return client
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            time.sleep(5)

    print("Max retries reached. Resetting...")
    reset_device('soft')

###################################

def ntptime_init():
    print("Initialising NTP sync.")

    print("Testing connection to NTP server...")
    server = socket.getaddrinfo(ntp_server, 123)
    print(f"Socket address: {server}")

    print("Setting mqtt_server to be NTP host...")

    ntptime.host = ntp_server

    attempts = 6
    for i in range(attempts):
        print(f"ntp attempt {i}")

        try:
            ntptime.settime()
            print("successfully sync time to ntp server.")
            return

        except Exception as e:
            print(f"NTP Time: {e}")
            print("Sleeping 5s...")
            time.sleep(5)

    print("i give up, can't sync, next.")

############
### main ###
############

def main():

    while True:
        try:
            # initialise:
            w5x00_init()
            
            ############
            # ntp sync here
            ntptime_init()
            ############
            
            
            # set-up relays and their controllers
            led = Led(25)
            led_ctrl = LedController(led)
            client = client_init(led_ctrl)

            #
            last_publish = time.time()

            while True:
                try:
                    subscript_init(client)

                    if time.time() - last_publish > status_update_period:

                        status = DeviceStatus(led_ctrl)
                        msg = json.dumps(status.__dict__)
                        
                        client.publish(pub_topic, msg)
                        last_publish = time.time()

                        print(f"-> {pub_topic.decode()}: {msg}")
                        
                  
                    time.sleep(1)

                except OSError:
                    print("Reconnecting...")
                    client = client_init(led_ctrl)

        except Exception as e:
            print(f"Critical: {e}. Resetting...")
            time.sleep(1)
            reset_device('soft')


if __name__ == "__main__":
    main()


"""
Example Config:

###############
### Network ###
###############

# use static ip address
static = True

# network configuration
static_ip = '169.254.244.99'
netmask = '255.255.0.0'
gateway = '0.0.0.0'
dns = '8.8.8.8'

############
### MQTT ###
############

# The brooker deets:
mqtt_server = '169.254.234.191'
user = 'test'
word = 'word'
port = 1883

# The client deets:
client_id = "test"

##############
### topics ###
##############

# NOTE: the basic af client we're using needs these to be byte arrays

# subscribe
sub_topic_1 = b'test/control'
sub_topic_2 = b'test/control/led'

# publish
pub_topic = b'test/status'

###############
### CONTROL ###
###############

status_update_period = 1

"""
