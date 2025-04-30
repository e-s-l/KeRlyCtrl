# MQTT BROOKERS

## MOSQUITTO (ON MAC)

### Set-up
On mac
```commandline
brew install mosquitto
brew services start mosquitto
brew services info mosquitto
```

### Config

`/usr/local/etc/mosquitto/mosquitto.conf`

### CLIS
```commandline
mosquitto_sub -t topic/state
mosquitto_pub -t topic/state -m "Hello World"

```