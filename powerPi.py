#!/usr/bin/env python3

"""An MQTT connected power outlet controller"""
import sys
import json
import logging
import paho.mqtt.client as mqtt
import RPi.GPIO as gpio

def setupGPIO(pin):
    """Sets up GPIO pins"""

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
        logging.info("ON command received")
        on_flag = True
    if (payload == "OFF"):
        logging.info("OFF command received")
        off_flag = True

    logging.debug("message received %s", payload)
    logging.debug("message topic=%s",message.topic)
    logging.debug("message qos=%s",message.qos)
    logging.debug("message retain flag=%s",message.retain)

def listen(host, port, username, password, command_topic, state_topic, availability_topic):
    """Listen on an MQTT topic"""
    mqttc = mqtt.Client()

    # Attach function to callback
    mqttc.on_message=on_message 
    
    if username:
        mqttc.username_pw_set(username, password)
    
    mqttc.connect(host, port)
    mqttc.subscribe(command_topic)

    # Tell server that we're available
    #mosquitto_pub -d -h 192.168.86.15 -p 1883 -t home-assistant/powerPi0/outlet0/availability -m "ON"
    mqttc.publish(availability_topic, "ON")

    global on_flag
    on_flag = False
    global off_flag
    off_flag = False

    while True:
        mqttc.loop()
        if (on_flag):
            mqttc.publish(state_topic, "ON")
            on_flag = False
            gpio.output(3, gpio.HIGH)
            inPin = gpio.input(5)
            logging.info("publishing ON state")
            logging.debug("Outputting %d", inPin)
        if (off_flag):
            mqttc.publish(state_topic, "OFF")
            off_flag = False
            gpio.output(3, gpio.LOW)
            inPin = gpio.input(5)
            logging.info("publishing OFF state")
            logging.debug("Outputting %d", inPin)

def main(config_path):
    """main entry point, load and validate config and call generate"""
    try:
        with open(config_path) as handle:
            logging.basicConfig(filename='powerPi.log', filemode='w', level=logging.DEBUG)

            config = json.load(handle)
            mqtt_config = config.get("mqtt", {})
            misc_config = config.get("misc", {})
            sensors = config.get("sensors")

            interval_ms = misc_config.get("interval_ms", 500)
            verbose = misc_config.get("verbose", False)

            host = mqtt_config.get("host", "localhost")
            port = mqtt_config.get("port", 1883)
            username = mqtt_config.get("username")
            password = mqtt_config.get("password")
            # topic = mqtt_config.get("topic", "sensors")
            command_topic = "home-assistant/powerPi0/outlet0/command"
            state_topic = "home-assistant/powerPi0/outlet0/state"
            availability_topic = "home-assistant/powerPi0/outlet0/availability"
            pin = 3

            setupGPIO(pin)
            listen(host, port, username, password, command_topic, state_topic, availability_topic)

            # generate(host, port, username, password, topic, sensors, interval_ms, verbose)
    except IOError as error:
        print("Error opening config file '%s'" % config_path, error)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("usage %s config.json" % sys.argv[0])
