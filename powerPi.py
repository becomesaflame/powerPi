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

    payload = str(message.payload.decode("utf-8"))
    state_topic = userdata.get("state_topic")
    pin = userdata.get("gpio_pin")

    if (payload == "ON"):
        client.publish(state_topic, "ON")
        gpio.output(pin, gpio.HIGH)
        inPin = gpio.input(5) # debug
        logging.info("Turning ON")
        logging.debug("Outputting %d", inPin)
    if (payload == "OFF"):
        client.publish(state_topic, "OFF")
        gpio.output(pin, gpio.LOW)
        inPin = gpio.input(5) # debug
        logging.info("Turning OFF")
        logging.debug("Outputting %d", inPin)

    logging.debug("message payload %s", payload)
    logging.debug("message topic=%s",message.topic)
    logging.debug("message qos=%s",message.qos)
    logging.debug("message retain flag=%s",message.retain)
    logging.debug("userdata: %s", repr(userdata))

def listen(host, port, username, password, outlet):
    """Listen on an MQTT topic"""
    command_topic = outlet.get("command_topic")
    state_topic = outlet.get("state_topic")
    availability_topic = outlet.get("availability_topic")

    mqttc = mqtt.Client(userdata=outlet)

    # Attach function to callback
    mqttc.on_message=on_message 
    
    if username:
        mqttc.username_pw_set(username, password)
    
    mqttc.connect(host, port)
    mqttc.subscribe(command_topic)

    # Tell server that we're available
    mqttc.publish(availability_topic, "ON")

    while True:
        mqttc.loop()

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
            outlets = config.get("outlets")
            outlet0 = outlets.get("outlet0")
            pin = outlet0.get("gpio_pin")

            setupGPIO(pin)
            listen(host, port, username, password, outlet0)

            # generate(host, port, username, password, topic, sensors, interval_ms, verbose)
    except IOError as error:
        print("Error opening config file '%s'" % config_path, error)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("usage %s config.json" % sys.argv[0])
