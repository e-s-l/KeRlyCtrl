import sys
import time
import ntptime
from machine import Pin, SPI
import binascii
import network
import json

from umqttsimple import MQTTClient
from config import *

#################
### CLASSES

class RelaySwitch:
    def __init__(self, pin):
        self.state = None
        self.relay = Pin(pin, Pin.OUT)
        self.update()

    def get_state(self):
        return [self.relay.value()]

    def update(self):
        self.state = self.get_state()
        #print(self.status())

    def status(self):
        return f"{self.state[0]}"

    def on(self):
        self.relay.value(1)
        self.update()
        return "On."

    def off(self):
        self.relay.value(0)
        self.update()
        return "Off."

    def toggle(self):
        self.relay.value(not self.relay.value())
        self.update()
        return "Toggled."


class RelayController:
    def __init__(self, relay, mqtt_client=None):
        self.relay = relay
        self.mqtt_client = mqtt_client

        self.commands = {
            "STATUS": self.get_status,
            "ON": self.relay.on,
            "OFF": self.relay.off,
            "TOGGLE": self.relay.toggle,
        }

    def get_status(self):
        status = self.relay.status()
        return status

    def execute(self, command_input):
        if command_input in self.commands:
            response = self.commands[command_input]()
            response_msg = f"{json.dumps({'time': time.time(), 'response': response})}"
            self.mqtt_client.publish(pub_topic, response_msg)
            return response
        return None

###################
### FUNCTIONS

def w5x00_init():

    print("Initialising the w5500.")

    spi = SPI(0, 2_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))  # SPI, CS, Reset pins
    nic.active(True)

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

def time_init():

    print("Initialising NTP sync.")
    ntptime.settime()

def reset():
    # Hard
    # machine.reset()
    # Soft
    sys.exit()

############
### mqtt ###
############

def sub_cb(topic, msg, rc1, rc2):

    command = msg.decode('utf-8').strip().upper()
    print(f"<- {topic.decode()}: {command}")

    # control
    if topic == sub_topic_1:
        # something here....
        pass

    # relay1
    elif topic == sub_topic_2:
        if command in rc1.commands:
            rc1.execute(command)

    # relay2
    elif topic == sub_topic_3:
        if command in rc2.commands:
            rc2.execute(command)

def mqtt_connect(rc1,rc2):
    attempts = 3
    for i in range(attempts):
        try:
            print(f"Attempt {i + 1}: Connecting to MQTT Broker...")
            client = MQTTClient(client_id, server=mqtt_server, port=port, user=user, password=word, keepalive=60)
            client.set_callback(lambda topic, msg: sub_cb(topic, msg, rc1, rc2))
            client.connect()
            print(f'Connected to broker ({mqtt_server}) as: {client_id}')
            return client
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            time.sleep(5)

    print("Max retries reached. Resetting...")
    reset()


def client_init(rc1, rc2):

    print("Initialising mqtt client.")
    client = mqtt_connect(rc1, rc2)
    rc1.mqtt_client = client
    rc2.mqtt_client = client

    return client

def make_status_msg(rc1, rc2):

    # Basic
    #msg = f"STATUS: rly1 = {rc1.get_status()}, rly2 = {rc2.get_status()}"
    # Better
    msg = json.dumps({'time': time.time(), 'relay_1': rc1.get_status(), 'relay_2': rc2.get_status()})

    return msg

############
### main ###
############

def main():

    while True:
        try:
            w5x00_init()
            time_init()

            # set-up relays and their controllers
            relay1 = RelaySwitch(6)
            relay2 = RelaySwitch(7)
            rc1 = RelayController(relay1)
            rc2 = RelayController(relay2)

            client = client_init(rc1, rc2)

            last_publish = time.time()

            while True:
                try:

                    client.subscribe(sub_topic_1)
                    client.subscribe(sub_topic_2)
                    client.subscribe(sub_topic_3)

                    if time.time() - last_publish > status_update_period:
                        status_msg = make_status_msg(rc1,rc2)
                        client.publish(pub_topic, status_msg)
                        print(f"-> {pub_topic.decode()}: {status_msg}")
                        last_publish = time.time()

                    time.sleep(1)

                except OSError:
                    print("MQTT disconnected. Reconnecting...")
                    client = client_init(rc1, rc2)

        except Exception as e:
            print(f"Critical error: {e}. Resetting...")
            time.sleep(5)
            sys.exit()


if __name__ == "__main__":
    main()
