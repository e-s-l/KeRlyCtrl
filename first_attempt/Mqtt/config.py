"""
Configuration file for the program.
Minimise the magic (numbers).
"""

# TOC
# network       (device ip)
# mqtt          (broker settings)
# control       (loop-times, attempt counts)
# timing        (ntp)
# hardware      (pins)

###############
### Network ###
###############

# use static ip address
static = True

# network configuration

# using mt. pleasant local network
static_ip = '131.217.63.138'        # testho, make sure not already in use
netmask = '255.255.255.0'
gateway = '131.217.63.129'
dns = '131.217.0.19'

############
### MQTT ###
############

# The brooker deets:
mqtt_server = 'godzilla.phys.utas.edu.au'   # using godzilla for testing
port = 1883         # this is just the default

# authentication if enabled (haven't tested this)
user = 'test'
word = 'word'

# The client deets:
client_id = "relay_switch"

##############
### topics ###
##############

# NOTE: the basic af client we're using needs these to be byte arrays

# subscribe
sub_topic_1 = b'test/control'
sub_topic_2 = b'test/control/relay1'
sub_topic_3 = b'test/control/relay2'

# publish
pub_topic = b'test/status'

###############
### CONTROL ###
###############

# how often should we publish status messages
status_update_period = 30       # unit: [s]

# this is the period of the central loop
response_time = 0.05             # units: [s]

# softly reset if we reach this limit
broker_connect_attempts = 3

##############
### timing ###
##############

ntp_server = mqtt_server

################
### HARDWARE ###
################

relay_1_pin = 6
relay_2_pin = 7

