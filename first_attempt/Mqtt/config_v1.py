"""
An example configuration file.
"""

###############
### Network ###
###############

# use static ip address
static = True

# network configuration
static_ip = '192.168.0.22'
netmask = '255.255.255.0'
gateway = '192.168.0.1'
dns = '8.8.8.8'

############
### MQTT ###
############

# The brooker deets:
mqtt_server = '192.168.0.21'
user = 'test'
word = 'word'
port = 1883
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

status_update_period = 5
