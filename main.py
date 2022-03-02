#!/usr/bin/env pybricks-micropython

# import os
from pybricks.hubs import EV3Brick
from pybricks.media.ev3dev import Image, ImageFile
from pybricks.ev3devices import (Motor, ColorSensor, InfraredSensor)
from pybricks.parameters import (Port, Stop, Direction, Align, Color)
from pybricks.tools import print, wait, StopWatch

from threading import Thread
import random
from time import time

EDGE_THRESHOLD = 50
ENEMY_DISTANCE = 30
SPEED_RUN = 100  # Power %
SPEED_SEARCH = 360  # Deg/s

ev3 = EV3Brick()


def countdown():
    # Wait 5 seconds, as per DA RULEZ
    for i in range(5):
        wait(900)
        ev3.speaker.beep(frequency=1000, duration=100)


def lower_wedge():
    # Lower the wedge while the other stuff is initialising
    motor_W.run_until_stalled(speed=500, then=Stop.HOLD, duty_limit=50)
    # Lift the wedge just a bit to avoid dragging it on the floor and losing traction
    motor_W.run_angle(speed=500, rotation_angle=-
                      10, then=Stop.HOLD, wait=False)


def check_boundaries():
    # Continuously check if the boundary is reached, and, if so, blocks the other behaviours and moves away from it
    global roam_enabled
    print("base colour", ground_colour)
    while True:
        value_L = sensor_L.reflection()
        value_R = sensor_R.reflection()
        if abs(value_L-ground_colour) >= EDGE_THRESHOLD or abs(value_R-ground_colour) >= EDGE_THRESHOLD:
            roam_enabled = False  # Stop the other behaviours
            print("Edge detected!", ground_colour, value_L, value_R)
            ev3.light.on(Color.YELLOW)
            ev3.screen.load_image("images/cat_afraid.png")

            # Back away from the edge
            motor_L.dc(-SPEED_RUN)
            motor_R.dc(-SPEED_RUN)
            wait(500)

            # Rotate away from the edge, depending on which sensor got triggered
            if abs(value_L-ground_colour) >= abs(value_R-ground_colour):
                motor_L.dc(SPEED_RUN)
            else:
                motor_R.dc(SPEED_RUN)
            wait(500)
            motor_L.stop(Stop.BRAKE)
            motor_R.stop(Stop.BRAKE)

            # Resume the other behaviours
            roam_enabled = True
            print("Roaming again")
        wait(10)


# Initialisation
motor_L = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_R = Motor(Port.C, Direction.COUNTERCLOCKWISE)
motor_W = Motor(Port.D)
sensor_L = ColorSensor(Port.S1)
sensor_R = ColorSensor(Port.S2)
sensor_D = InfraredSensor(Port.S3)
# sensor_D.mode = "IR-PROX"
timer = StopWatch()
ground_colour = 0
turn_right = 0
roam_enabled = False  # Global flag to enable/disable the roaming behaviour
random.seed(int(time()*1000))
turn_right = random.randint(0, 1)
print("Initial turn right", turn_right)
ground_colour = (sensor_L.reflection() + sensor_R.reflection()) / 2
ev3.speaker.set_volume(volume=100, which="_all_")
# ev3.speaker.set_speech_options(language="en", voice="whisperf")
# ev3.speaker.say("Ready to rumble!")
ev3.speaker.set_speech_options(language="pt-pt", voice="whisperf")
ev3.speaker.say("Pronto para o combate!")

# Wait for a hand to be placed in front of the sensor, then removed, to start the initial countdown
ev3.speaker.beep(frequency=1000, duration=100)
while sensor_D.distance() > 5:
    pass
ev3.speaker.beep(frequency=1000, duration=100)
while sensor_D.distance() < 5:
    pass
countdown()

# Match begin: run towards the edge before turning around
# motor_W.run_angle(speed=500, rotation_angle=135,
#                   then=Stop.HOLD, wait=False)
Thread(target=lower_wedge).start()
Thread(target=check_boundaries).start()  # Begin edge detection
motor_L.dc(SPEED_RUN)
motor_R.dc(SPEED_RUN)
while roam_enabled == False:
    pass  # Wait for the edge detection to detect the edge before starting the main behaviour

# Main behaviour
while True:
    if roam_enabled:
        timer.reset()
        motor_L.run(SPEED_SEARCH*turn_right)
        motor_R.run(SPEED_SEARCH*int(not turn_right))
        ev3.light.on(Color.GREEN)
        if turn_right:
            ev3.screen.load_image("images/cat_right.png")
        else:
            ev3.screen.load_image("images/cat_left.png")
        while timer.time() < random.randint(1, 3)*2000 and roam_enabled:
            # print("distance", sensor_D.distance())
            if sensor_D.distance() <= ENEMY_DISTANCE:
                print("ENEMY!", sensor_D.distance())
                # Enemy found: full speed ahead
                motor_L.dc(SPEED_RUN)
                motor_R.dc(SPEED_RUN)
                ev3.light.on(Color.RED)
                ev3.screen.load_image("images/cat_angry.png")
                while sensor_D.distance() <= ENEMY_DISTANCE and roam_enabled:
                    # Keep going while the enemy is visible
                    wait(10)
            wait(10)
        turn_right = int(not turn_right)  # Now turn the other way
        wait(10)
