from machine import Pin
import time

# ESP32 built-in LED is usually on GPIO2
led = Pin(2, Pin.OUT)

while True:
    led.value(1)  # Turn LED on
    time.sleep(1)  # Wait for 1 second
    led.value(0)  # Turn LED off
    time.sleep(1)  # Wait for 1 second 