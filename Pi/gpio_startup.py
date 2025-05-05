#!/usr/bin/env python3

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.OUT)
GPIO.output(5, GPIO.HIGH)
