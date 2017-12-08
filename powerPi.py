#!/usr/bin/env python3

"""An MQTT connected power outlet controller"""
import sys
import json
import time
import random

import paho.mqtt.client as mqtt
import RPi.GPIO as gpio

def setupGPIO(pin):
    """Sets up GPIO"""

    # Use Raspberry Pi board pin numbers
    gpio.setmode(gpio.BOARD)

    # set up the GPIO pin
    gpio.setup(pin, gpio.OUT)
    gpio.setup(5, gpio.IN)


def on_message(client, userdata, message):
    """Callback function for subscriber"""
    global on_flag
    global off_flag    

    payload = str(message.payload.decode("utf-8"))
    if (payload == "ON"):
        print("payload is ON")
        on_flag = True
    if (payload == "OFF"):
        print("payload is OFF")
        off_flag = True

    print("message received ", payload)
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

def listen(host, port, username, password, command_topic, state_topic):
    """Listen on an MQTT topic"""
    mqttc = mqtt.Client()

    # Attach function to callback
    mqttc.on_message=on_message 
    
    if username:
        mqttc.username_pw_set(username, password)
    
    mqttc.connect(host, port)
    mqttc.subscribe(command_topic)

    global on_flag
    on_flag = False
    global off_flag
    off_flag = False

    while True:
        mqttc.loop()
        inPin = gpio.input(5)
        print("Outputting ", inPin)
        if (on_flag):
            print("publishing ON")
            mqttc.publish(state_topic, "ON")
            on_flag = False
            gpio.output(3, gpio.HIGH)
        if (off_flag):
            print("publishing OFF")
            mqttc.publish(state_topic, "OFF")
            off_flag = False
            gpio.output(3, gpio.LOW)

def main(config_path):
    """main entry point, load and validate config and call generate"""
    try:
        with open(config_path) as handle:
            config = json.load(handle)
            mqtt_config = config.get("mqtt", {})
            misc_config = config.get("misc", {})
            sensors = config.get("sensors")

            interval_ms = misc_config.get("interval_ms", 500)
            verbose = misc_config.get("verbose", False)

            if not sensors:
                print("no sensors specified in config, nothing to do")
                return

            host = mqtt_config.get("host", "localhost")
            port = mqtt_config.get("port", 1883)
            username = mqtt_config.get("username")
            password = mqtt_config.get("password")
            # topic = mqtt_config.get("topic", "sensors")
            command_topic = "home-assistant/powerPi0/outlet0/command"
            state_topic = "home-assistant/powerPi0/outlet0/state"

            pin = 3
            setupGPIO(pin)
            listen(host, port, username, password, command_topic, state_topic)

            # generate(host, port, username, password, topic, sensors, interval_ms, verbose)
    except IOError as error:
        print("Error opening config file '%s'" % config_path, error)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("usage %s config.json" % sys.argv[0])
