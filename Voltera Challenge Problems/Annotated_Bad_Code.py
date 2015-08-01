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
    #not really good practice to set a variable to None, it's always better to set it to a inconsequential value but defines its type
    #variables also shouldn't be defined here, they are currently defined as "class" or "static" variables and are global for the class
    #should be defined in the "__init__" method so that they are individual to each instance of variable defined
    at_speed = False
    target_speed = None
    _speeds = []
    _speed_cap = 10000
    _vibration_callback = None
    reconnect = True

    def __init__(self):
        self._cycle_running = False

    #bad idea to name an argument variable "port" if you are about to define "self.port" in the method, and they are not even the same type of variable
    #just confusing, should rename the argument to "port_number" or "port_name"
    def connect(self, port):
        self.port = Serial(port, timeout=1)
        self.port_lock = Lock()
        self._cycle_running = False
        # Check that we're connected to the right device
        self.port.write("?")
        buffer = ""
        #better practice to set res and buffer as variables outside of this while loop, then say "while !res:"
        #while True is not good for readability of code, Python values explicit over everything else so the end condition of the while loop should
        #be explicit
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
            #self.connect takes two variables, self and port, but this method call does not provide a port, this would raise an error
            self.connect()
            # reset our speed to what it was before
            self.speed(self._speed_cap)

    def speed(self, speed):
        #there's a _speed_cap variable but there's no if statement to block the speed setting if the speed is greater than the speed cap
        #there should be an if statement, if speed < _speed_cap: self.port.write("Speed: " + speed + "RPM\n")
        #and an else statement that just does else: self.port.write("Speed: " + _speed_cap + "RPM\n")
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
            # Too much vibration - shut everything down ASAP before damage occurs
            if self._vibration_callback:
                #there is no _vibration_callback() method, there is only vib_callback() method
                #this should call the vib_callback() method instead of self._vibration_callback()
                self._vibration_callback()
            self.speed(0)
            #this can be disastrous, since this does not set self.reconnect = False
            #should set self.disconnect = False so this fully disconnects the port when disconnect is called
            self.disconnect()
            raise RuntimeError("Excessive vibration - cycle halted")
        # Remove 'RPM' from the end
        result = result[:-4]
        self.got_speed = result
        # Release the port lock so others can use it
        self.port_lock.release()

    def getSpeed(self):
        #get_speed_in_thread doesn't have a return type, so target=self.get_speed_in_thread is not a valid assignment
        thread = Thread(target=self.get_speed_in_thread)
        thread.start()

    def perform_centrifuge_cycle(self, name, cycle):
        # Dont start if door is open
        #is_door_closed doesn't return "yes" or "no" string, it returns one bit, 1 or 0, corresponding to True or False
        #this should be if self.is_door_closed() == 1:
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
            #instead of not self.got_speed > self.target_speed, the not can be taken out and the inequality can be flipped
            #this can become while self.got_speed < self.target_speed:
            while not self.got_speed > self.target_speed:
                self.getSpeed()
            # Run at our desired speed for the given
        
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
        #again, can be replaced by while self.got_speed() <= self.target_speed:
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
        #this is a very bad place to set self._vibration_callback = self.vib_callback, since if find_max_speed_before_vibration(self) is not called
        #then _vibration_callback is never created, and even worse it adds absolutely nothing to self.vib_callback so it is just a
        #superfluous function
        self._vibration_callback = self.vib_callback
        #this is an infinite loop since speed_cap is 10000, and the increment condition is speed += 100
        #although the idea is that the loop will end itself when self.did_vibrate == true, the while condition should be more explicitly set to
        #while speed <= self._speed_cap so that it will end if the centrifuge doesn't vibrate
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
        #in python two this would return a floor of average if average is a float, so in python 2 this should actually be
        #average = accum/len(self._speeds) + accum%len(self._speeds)
        #in python 3 this operation is fine
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

        #this doesn't return the standard deviation, only the total deviation from the average speed
        #in reality, this algorithm should square each difference between speed and average, then sum them, divide it by number of terms, and take the
        #square root of all that
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
    
    #python classes are "public", you don't need a method to return a variable, you can just use the dot operator to return the variable directly
    #this function is superfluous
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