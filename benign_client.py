import paho.mqtt.client as mqtt
import time
import json
import random

# --- Configuration ---
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "iot/sensor/temp"
CLIENT_ID = "benign_client"

def on_connect(client, userdata, flags, rc):
    """Callback function for when the client connects to the broker."""
    if rc == 0:
        print(f"Connected to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"Failed to connect, return code {rc}\n")

def main():
    """Main function to run the benign IoT client."""
    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect

    try:
        client.connect(BROKER_HOST, BROKER_PORT, 60)
    except ConnectionRefusedError:
        print("Connection refused. Is the MQTT broker running?")
        return

    client.loop_start()

    print(f"Starting to send messages to topic '{TOPIC}' every 5 seconds.")
    try:
        while True:
            # Simulate a temperature reading
            temperature = round(random.uniform(20.0, 30.0), 2)
            payload = json.dumps({"temp": temperature})

            # Publish the message
            result = client.publish(TOPIC, payload)

            # Check if publish was successful
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Sent: {payload}")
            else:
                print(f"Failed to send message to topic {TOPIC}")

            time.sleep(5)
    except KeyboardInterrupt:
        print("\nDisconnecting benign client.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()
