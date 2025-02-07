from machine import Pin, SPI
import network
import time

import binascii
from usocket import socket, AF_INET, SOCK_STREAM
import uasyncio as asyncio

# relay control pins
relayA = Pin(6, Pin.OUT)
relayB = Pin(7, Pin.OUT)

# active connection count
active_conns = 0

# control
static = True

port = 5001

static_ip = '192.168.1.20'
netmask = '255.255.255.0'
gateway = '192.168.1.1'
dns = '8.8.8.8'

"""
# command options
COMMANDS = '''
            COMMANDS:
            [1] STATUS: get relay states,
            [2] SWITCH: toggle between the relays,
            [3] ON: turn on both relays,
            [4] OFF: turn off both relays,
            [5] CLOSE: close the connection,
            [6] A ON: turn on relay a,
            [7] B ON: turn on relay b,
            [8] A OFF: turn off relay a,
            [9] B OFF: turn off relay b,
            [10] A TOGGLE: switch state of relay a,
            [11] B TOGGLE: switch state of relay b,
            [12] HELP: this menu.
'''
"""

################################3

class RelaySwitch:
    def __init__(self, pin_a, pin_b):

        self.state = None
        self.relayA = Pin(pin_a, Pin.OUT)
        self.relayB = Pin(pin_b, Pin.OUT)
        self.update()

    def get_state(self):
        return [self.relayA.value(), self.relayB.value()]

    def update(self):
        print(self.get_state())
        self.state = self.get_state()

    def status(self):
        return "State: (A, B) = " + ", ".join(map(str, self.state))

    def a_on(self):
        self.relayA.value(1)
        self.update()
        return f"RelayA ON.\n{self.status()}"

    def a_off(self):
        self.relayA.value(0)
        self.update()
        return f"RelayA OFF.\n{self.status()}"

    def a_toggle(self):
        self.relayA.value(not self.relayA.value())
        self.update()
        return f"RelayA TOGGLED.\n{self.status()}"

    def b_on(self):
        self.relayB.value(1)
        self.update()
        return f"RelayB ON.\n{self.status()}"

    def b_off(self):
        self.relayB.value(0)
        self.update()
        return f"RelayB OFF.\n{self.status()}"

    def b_toggle(self):
        self.relayB.value(not self.relayB.value())
        self.update()
        return f"RelayB TOGGLED.\n{self.status()}"

    def turn_off(self):
        self.relayA.value(0)
        self.relayB.value(0)
        self.update()
        return f"Off.\n{self.status()}"

    def turn_on(self):
        self.relayA.value(1)
        self.relayB.value(1)
        self.update()
        return f"On.\n{self.status()}"

    def switch_relay(self):
        self.relayA.value(not self.relayA.value())
        self.relayB.value(not self.relayB.value())
        self.update()
        return f"Switching relay.\n{self.status()}"

class Command:
    def __init__(self, name, description, action=None):
        self.name = name
        self.description = description
        self.action = action

    def execute(self):
        if self.action:
            return self.action()
        return f"Command '{self.name}' not implemented."

class RelayController:
    def __init__(self, relay):
        self.relay = relay
        self.commands = {
            "1": ("STATUS", "Get relay states", self.relay.status),
            "2": ("SWITCH", "Toggle both relays", self.relay.switch_relay),
            "3": ("ON", "Turn on both relays", self.relay.turn_on),
            "4": ("OFF", "Turn off both relays", self.relay.turn_off),
            "5": ("CLOSE", "Close the connection", None),
            "6": ("A ON", "Turn on relay A", self.relay.a_on),
            "7": ("B ON", "Turn on relay B", self.relay.b_on),
            "8": ("A OFF", "Turn off relay A", self.relay.a_off),
            "9": ("B OFF", "Turn off relay B", self.relay.b_off),
            "10": ("A TOGGLE", "Toggle relay A", self.relay.a_toggle),
            "11": ("B TOGGLE", "Toggle relay B", self.relay.b_toggle),
            "12": ("HELP", "Show this menu", self.display_help),
        }

        # Create a reverse lookup to allow commands by name as well
        self.command_lookup = {name: (num, desc, action) for num, (name, desc, action) in self.commands.items()}

    def display_help(self):
        help_text = "\nCOMMANDS:\n" + "\n".join(
            [f"[{num}] {name}: {desc}" for num, (name, desc, _) in
             sorted(self.commands.items(), key=lambda x: int(x[0]))]
        )
        return help_text

    def execute_command(self, command_input):
        """ Execute command by either number or name """
        if command_input in self.commands:
            _, _, action = self.commands[command_input]
        elif command_input in self.command_lookup:
            _, _, action = self.command_lookup[command_input]
        else:
            return f"Unknown command: {command_input}. Type 'HELP' for available commands."

        return action() if action else "Closing connection..."

###################

# W5500 initialisation
def w5x00_init():
    spi = SPI(0, 2_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))  # SPI, CS, Reset pins

    nic.active(True)

    #########################

    if static:
        # static
        nic.ifconfig((static_ip, netmask, gateway, dns))
    else:
        # dhcp
        nic.ifconfig('dhcp')

    #########################

    # print(nic.regs())

    while not nic.isconnected():
        time.sleep(1)
        print("Waiting for network...")

    print("Network connected:", nic.ifconfig()[0])
    mac = nic.config('mac')
    print("Device mac:", mac)
    print(binascii.hexlify(mac, ':').decode())


# server initialisation
def server_init(max_conns):

    s = socket(AF_INET,SOCK_STREAM)

    s.bind(('0.0.0.0', port))

    s.listen(max_conns)

    print(f"Server listening on port {port}.")
    return s


def handle_client(conn, relay_controller):
    global active_conns
    active_conns += 1

    try:
        print("Client connected.")
        conn.send(f"{relay_controller.display_help()}\n".encode())

        while True:
            try:
                request = conn.recv(1024)
                if not request:
                    break

                request = request.decode().strip().upper()
                print(f"Received: {request}")

                # Handle close command separately
                if request in ("5", "CLOSE"):
                    conn.send("Closing connection...\n".encode())
                    break

                response = relay_controller.execute_command(request)
                conn.send(f"{response}\n".encode())

            except OSError:
                print("Client lost.")
                break

    except Exception as e:
        print(f"Error: {e}")

    finally:
        conn.close()
        active_conns -= 1
        print("Client disconnected. Active connections:", active_conns)


def main():
    global active_conns
    max_conns = 10

    w5x00_init()

    s = server_init(max_conns)
    relay = RelaySwitch(6, 7)
    relay_controller = RelayController(relay)

    try:
        while True:
            conn, addr = s.accept()
            print(f"Connection from {addr}.")
            handle_client(conn, relay_controller)
    except OSError as ose:
        print(f"OSE... {ose}")
    except Exception as e:
        print(f"Exception... {e}")


if __name__ == "__main__":
    main()
