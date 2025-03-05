
Debug:

Check listing via:
sudo lsof -i :123


chronyc tracking
chronyc sources -v


sudo /usr/local/sbin/chronyd -f /usr/local/etc/chrony.conf\n
```commandline
cat chrony.conf
# Stratum 1 server:
server ntp.per.nml.csiro.au iburst

# Allow all link-local clients
allow 169.254.0.0/16

# Serve time even if no external NTP
local stratum 10

# Use system as reference
refclock SHM 0 offset 0.0 delay 0.0 refid LOCL

# Drift file
driftfile /var/lib/chrony/drift
```

As an example, first attempt:
```commandline
/etc$cat chrony.conf
# syncronisation sources
server ntp.monash.edu iburst
server 0.au.pool.ntp.org iburst
server 1.au.pool.ntp.org iburst
server 2.au.pool.ntp.org iburst
server 3.au.pool.ntp.org iburst

# level (10 i slowest)
local stratum 10

# network
#allow 169.254.0.0/16
#allow 169.254.244.0/24

allow 169.254/16

allow 169.254.244.99

#driftfile /var/lib/chrony/drift
#rtcsync

# clock
#refclock PHC /dev/ptp0 poll 3 dpoll -2 offset 0

# log
#logdir /opt/homebrew/var/log/chrony
#log statistics tracking measurements

#
makestep 1 -1
```

And also
```commandline
/etc$ cat ntp.conf
server ntp.per.nml.csiro.au iburst
server ntp.nml.csiro.au iburst
server ntp.mel.nml.csiro.au iburst
###########
# Servers #
###########

server 0.au.pool.ntp.org iburst
server 1.au.pool.ntp.org iburst
server 2.au.pool.ntp.org iburst
server 3.au.pool.ntp.org iburst

# This ones down
#server ntp.monash.edu

# get registered with CSIRO

############
# Settings #
############

# drift
driftfile /var/db/ntp.drift

# log
logfile /var/log/ntpd.log

# local fallback
# server 127.127.1.0
# fudge 127.127.1.0 stratum 10

###############
# Connections #
###############

# allow localhost
restrict 127.0.0.1
restrict ::1

# block others
restrict default ignore

# allow LAN
restrict 192.168.0.0 mask 255.255.255.0 nomodify notrap

# allow specific
# restrict 169.254.0.0 mask 255.255.0.0 nomodify notrap
```

