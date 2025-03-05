/usr/local/opt/mosquitto/sbin/mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf

mosquitto_sub -t "test/status" -d
 
mosquitto_pub -t 'test/control/led' -m 'ON' -d