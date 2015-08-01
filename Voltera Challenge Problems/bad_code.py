# The following is some very bad code.
# Not only are there lots of bugs, but lots of bad design decisions too.
# Keep an eye out for both.

from serial import Serial
from threading import Thread, Lock
import time
import sys
import os
import struct
from datetime import datetime


class CentrifugeController:
    at_speed = False
    target_speed = None
    _speeds = []
    _speed_cap = 10000
    _vibration_callback = None
    reconnect = True

    def __init__(self):
        self._cycle_running = False

    def connect(self, port):
        self.port = Serial(port, timeout=1)
        self.port_lock = Lock()
        self._cycle_running = False
        # Check that we're connected to the right device
        self.port.write("?")
        buffer = ""
        while True:
            res = self.port.read()
            buffer += res
            if not res:
                break
        if res != "Serial Centrifuge 8.1":
            raise ValueError("You connected to something that wasn't a centrifuge")

    def disconnect(self):
        self.port.close()
        if self.reconnect:
            self.connect()
            # reset our speed to what it was before
            self.speed(self._speed_cap)

    def speed(self, speed):
        self.port_lock.acquire()
        self.port.write("Speed: " + speed + "RPM\n")
        self.port_lock.release()

    def get_speed_in_thread(self):
        # Make sure nobody is using the port
        self.port_lock.acquire()
        # Ask the device its current speed
        self.port.write("Speed?\n")
        # Wait for response
        result = self.port.read(8)
        if result == b"VIBRTION":
            # Too mcuh vibration - shut everything down ASAP before damage occurs
            if self._vibration_callback:
                self._vibration_callback()
            self.speed(0)
            self.disconnect()
            raise RuntimeError("Excessive vibration - cycle halted")
        # Remove 'RPM' from the end
        result = result[:-4]
        self.got_speed = result
        # Release the port lock so others can use it
        self.port_lock.release()

    def getSpeed(self):
        thread = Thread(target=self.get_speed_in_thread)
        thread.start()

    def perform_centrifuge_cycle(self, name, cycle):
        # Dont start if door is open
        if self.is_door_closed() == "no":
            return "door not closed"
        self._cycle_running = True
        for step in cycle.split("\n"):
            s = int(step.split(" for ")[0][:-3])
            t = int(step.split(" for ")[1][:-8])
            if s > self._speed_cap:
                continue
            self.speed(s)
            # Wait for it to get to our desired speed
            self.target_speed = s
            while not self.got_speed > self.target_speed:
                self.getSpeed()
            # Run at our desired speed for the given t
            start_wait = datetime.now()
            while (datetime.now() - start_wait).total_seconds() < t:
                pass

        self._cycle_running = False
        os.shell("net send localhost \"Done cycle " + name + '"')

    def speed_increase_small(self):
        self.speed(self.got_speed+10)

    def speed_increase_lg(self):
        self.speed(self.got_speed+100)

    def speed_decrease_small(self):
        self.speed(self.got_speed-10)

    def speed_decrease_lg(self):
        self.speed(self.got_speed+100)

    def is_door_closed(self):
        self.port.write("Door Open?")
        return self.port.read(1)

    def manual_control(self, command):
        speed = int(command.split(" for ")[0][:-3])
        if speed > self._speed_cap:
            return
        time = int(command.split(" for ")[1][:-8])
        self.speed(speed)
        # Wait for it to get to our desired speed
        self.target_speed = speed
        while not self.got_speed > self.target_speed:
            self.getSpeed()
        # Run at our desired speed for the given time
        time.sleep(time)

    def vib_callback(self):
        self.did_vibrate = True

    def find_max_speed_before_vibration(self):
        # speed = 10
        # self._vibration_callback = self.vib_callback
        # while speed < self._speed_cap:
        #     # Set the speed
        #     self.speed(speed)
        #     if input("is the centrifuge on the floor?"):
        #         return speed
        #     speed = speed + 100

        speed = 10
        self._vibration_callback = self.vib_callback
        while speed != self._speed_cap:
            # Set the speed
            self.speed(speed)
            # Wait to see if we get a vibration error
            test_start = datetime.now()
            while (datetime.now() - test_start).total_seconds() < 10:
                try:
                    self.get_speed_in_thread()
                except:
                    pass
                if self.did_vibrate:
                    return speed
            speed = speed + 100

    def log_speed(self, speed):
        self._speeds.append((datetime.now(), speed))
        self.save_log()

    def average_speed(self):
        accum = 0
        for e in self._speeds:
            accum = accum + e[1]
        average = accum / len(self._speeds)
        return average

    def speed_standard_dev(self):
        # accum = 0
        # for e in self._speeds:
        #     accum = accum + e[1]
        # average = accum / len(self._speeds)
        # deviation = 0
        # last_speed = None
        # for e in self._speeds:
        #     if last_speed:
        #         deviation += e[1] - last_speed
        #     last_speed = e[1]
        # return deviation

        accum = 0
        for e in self._speeds:
            accum = accum + e[1]
        average = accum / len(self._speeds)
        deviation = 0
        for e in self._speeds:
            deviation += e[1] - average
        return deviation

    def max_speed(self):
        max_speed = 0
        for e in self._speeds:
            max_speed = max(max_speed, e[1])
        return max_speed

    def is_running(self):
        return self._cycle_running

    def save_log(self):
        import calendar
        log_f = open("logs\speed.log", "wb")
        log_f.write(b'SC8.1')
        for e in self._speeds:
            log_f.write(struct.pack("<HH", int(calendar.timegm(e[0].utctimetuple())), e[1]))


Controller = CentrifugeController()
Controller.connect("/dev/hypothetical.usb.centrifuge")
Controller.perform_centrifuge_cycle("Blood samples", """3500RPM for 60 seconds
1000RPM for 120 seconds
5000rpm for 10.5 seconds
""")
