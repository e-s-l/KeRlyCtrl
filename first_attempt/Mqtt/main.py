import sys
import time
import socket
import ntptime
from machine import Pin, SPI, reset
import binascii
import network
import json
import gc
from umqttsimple import MQTTClient
from config import *

###############
### CLASSES ###
###############

class RelaySwitch:
    def __init__(self, pin):
        self.state = None
        self.relay = Pin(pin, Pin.OUT)
        self.update()

    def get_state(self):
        return [self.relay.value()]

    def update(self):
        self.state = self.get_state()

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
        """
        Get the state of the relay associated with this controller.
        """

        status = self.relay.status()
        return status

    def execute(self, command_input):
        """
        If passed a valid command, execute it and report back.
        """

        if command_input in self.commands:
            response = self.commands[command_input]()
            self.mqtt_client.publish(pub_topic, f"{json.dumps({'time': time.time(), 'response': response})}")
            return response

        return None

##################
### FUNCTIONS ###
#################

# set-up

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

    # some (probably) unnecessary extra info...
    mac = binascii.hexlify(nic.config('mac'), ':').decode()
    print("Device MAC:", mac)

def time_init():
    """
    Connect to the NTP server, and set the time.
    Will this time drift off? Does settime() need to be called more regularly?
    """

    print("Initialising NTP sync.")

    # a superfluous test...
    print("Testing connection to NTP server...")
    server = socket.getaddrinfo(ntp_server, 123)
    print(f"Socket address: {server}")

    print("Setting mqtt_server to be NTP host...")
    ntptime.host = ntp_server
    ntptime.settime()

# utilities

def show_memory():
    """
    A little debug script, can probably delete this in deployment.
    """

    gc.collect()
    print(f"free: {gc.mem_free()} bytes")
    print(f"allocated: {gc.mem_alloc()} bytes")


def reset_device(kind):
    """
    Restart the device-program, either the software or hardware.
    """

    print(f"{kind} resetting the device")

    kind = kind.upper()

    if kind == "HARD":
        # Hard
        reset()
    elif kind == "SOFT":
        # Soft
        sys.exit()
    else:
        print("Erroneous reset type requested.")

############
### mqtt ###
############

def sub_cb(topic, msg, rc1, rc2):
    """
    Subscription callbacks.
    Do something different for each topic...
    """

    command = msg.decode('utf-8').strip().upper()
    print(f"<- {topic.decode()}: {command}")

    # test/control
    if topic == sub_topic_1:
        # someday, something here...
        pass

    # test/control/relay1
    elif topic == sub_topic_2:
        if command in rc1.commands:
            rc1.execute(command)

    # test/control/relay2
    elif topic == sub_topic_3:
        if command in rc2.commands:
            rc2.execute(command)

def mqtt_connect(rc1,rc2):
    """
    Set the device to be a mqtt client to the broker.
    If  this fails more than broker_connect_attempts, softly reset the device, and so begin again.
    """

    for i in range(broker_connect_attempts):
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
    reset_device('soft')


def client_init(rc1, rc2):
    """
    For each relay, set up the client (see above), and assign as member variables.
    """

    print("Initialising mqtt client.")
    client = mqtt_connect(rc1, rc2)
    rc1.mqtt_client = client
    rc2.mqtt_client = client

    return client

def make_status_msg(rc1, rc2):
    """
    Return some kind of summary of the state of the relays.
    Maybe better to use vars(object) or object.__dict__
    """

    return json.dumps({'time': time.time(), 'relay_1': rc1.get_status(), 'relay_2': rc2.get_status()})

############
### main ###
############

def main():

    while True:
        try:
            w5x00_init()
            time_init()

            # set-up relays and their controllers
            relay1 = RelaySwitch(relay_1_pin)
            relay2 = RelaySwitch(relay_2_pin)
            rc1 = RelayController(relay1)
            rc2 = RelayController(relay2)

            client = client_init(rc1, rc2)
            # subscriptions
            client.subscribe(sub_topic_1)
            client.subscribe(sub_topic_2)
            client.subscribe(sub_topic_3)

            last_publish = time.time()

            while True:
                try:
                    client.check_msg()

                    if time.time() - last_publish > status_update_period:
                        status_msg = make_status_msg(rc1,rc2)
                        client.publish(pub_topic, status_msg)
                        print(f"-> {pub_topic.decode()}: {status_msg}")
                        gc.collect()

                        last_publish = time.time()

                    time.sleep(response_time)

                except OSError:
                    print("MQTT disconnected. Reconnecting...")
                    client = client_init(rc1, rc2)

        except Exception as e:
            print(f"Critical error: {e}. Resetting...")
            time.sleep(1)
            reset_device('soft')

if __name__ == "__main__":
    main()
