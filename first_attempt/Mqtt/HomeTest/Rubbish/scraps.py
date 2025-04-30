def set_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B

    host = mqtt_server

    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))


def ntptime_init():
    print("Initialising NTP sync.")

    print("Testing connection to server...")
    ntp_server = socket.getaddrinfo(mqtt_server, 123)
    print(f"Socket address: {ntp_server}")

    print("Setting mqtt_server to be NTP host.")
    ntptime.host = mqtt_server

    try:
        ntptime.settime()

    except Exception as e:
        print(f"NTP Time: {e}")


def ntp_time(server):
    NTP_DELTA = 2208988800  # Seconds between 1900-01-01 and 1970-01-01
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B  # LI, Version, Mode

    addr = socket.getaddrinfo(server, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5)  # Set timeout to 5 seconds
    try:
        s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        return val - NTP_DELTA
    except Exception as e:
        print("NTP request failed:", e)
        return None


def ntp_connect_test():
    attempts = 6

    for i in range(attempts):
        print(f"ntp attempt {i}")
        try:
            # ntptime.host = mqtt_server
            ntptime.time()
        # print("ntp take 1:")
        #  sync_time()
        #  print_time()

        # print("ntp take 2:")
        # ntptime_init()

        # print("ntp take 3:")
        # set_time()

        except Exception as e:
            print(f"NTP: {e}")
            time.sleep(5)

        gc.collect()

    print("Max retries reached. Giving up on this...")
