import subprocess
import time
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, ConfusionMatrixDisplay
import argparse
import matplotlib.pyplot as plt
from io import StringIO

def collect_data(filename, duration, interface, run_attacker=False):
    """
    Captures network traffic on the specified interface for a given duration.

    Args:
        filename (str): The name of the pcap file to save the data.
        duration (int): The duration of the capture in seconds.
        interface (str): The network interface to capture on.
        run_attacker (bool): Whether to run the attacker client.
    """
    print(f"\n--- Starting data collection for '{filename}' (Duration: {duration}s) ---")
    print(f"Attacker running: {run_attacker}")

    tshark_command = ["tshark", "-i", interface, "-f", "tcp port 1883", "-w", filename]
    processes = []

    try:
        tshark_proc = subprocess.Popen(tshark_command)
        processes.append(tshark_proc)
        print(f"tshark started, capturing on interface '{interface}'.")
        time.sleep(2)  # Give tshark a moment to start capturing

        benign_proc = subprocess.Popen(["python", "benign_client.py"])
        processes.append(benign_proc)
        print("Benign client started.")

        if run_attacker:
            attacker_proc = subprocess.Popen(["python", "attacker_client.py"])
            processes.append(attacker_proc)
            print("Attacker client started.")

        print(f"Collecting data for {duration} seconds...")
        time.sleep(duration)

    finally:
        print("--- Stopping data collection ---")
        for p in reversed(processes):
            try:
                p.terminate()
                p.wait(timeout=5)
                print(f"Process {p.pid} terminated.")
            except subprocess.TimeoutExpired:
                p.kill()
                print(f"Process {p.pid} killed.")

        if os.path.exists(filename):
            print(f"Data collection complete. File saved as '{filename}'.")
        else:
            print(f"Warning: Output file '{filename}' was not created.")

def extract_features(pcap_file, label):
    """
    Extracts features from a pcap file and returns a pandas DataFrame.

    Args:
        pcap_file (str): The path to the pcap file.
        label (int): The label to assign (0 for normal, 1 for attack).

    Returns:
        pandas.DataFrame: A DataFrame with features and labels.
    """
    print(f"\n--- Extracting features from '{pcap_file}' ---")

    tshark_command = [
        "tshark", "-r", pcap_file,
        "-Y", "mqtt",
        "-T", "fields",
        "-e", "frame.time_epoch",
        "-e", "mqtt.msgtype",
        "-e", "frame.len",
        "-E", "header=y", "-E", "separator=,"
    ]

    result = subprocess.run(tshark_command, capture_output=True, text=True, check=True)

    if not result.stdout.strip():
        print(f"No MQTT data found in '{pcap_file}'.")
        return pd.DataFrame()

    df = pd.read_csv(StringIO(result.stdout))
    df.columns = ['time', 'mqtt_type', 'bytes']
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    df['is_publish'] = (df['mqtt_type'] == 3).astype(int)

    features = df.resample('1S').agg(
        publish_count=('is_publish', 'sum'),
        total_packets=('mqtt_type', 'count'),
        total_bytes=('bytes', 'sum')
    ).fillna(0)

    features['label'] = label
    print(f"Feature extraction complete. Found {len(features)} time windows.")
    return features

def main():
    """Main function to run the entire experiment."""
    parser = argparse.ArgumentParser(
        description="Run an IoT intrusion detection experiment.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-i", "--interface",
        default="lo",
        help='Network interface for capturing packets.\nUse "tshark -D" to find the correct interface name.\nDefault is "lo".'
    )
    parser.add_argument(
        "-t", "--time",
        type=int,
        default=60,
        help="Duration in seconds for each data collection phase.\nDefault is 60."
    )
    parser.add_argument(
        "--normal-out",
        default="normal.pcap",
        help='Output filename for normal traffic.\nDefault is "normal.pcap".'
    )
    parser.add_argument(
        "--attack-out",
        default="attack.pcap",
        help='Output filename for attack traffic.\nDefault is "attack.pcap".'
    )
    args = parser.parse_args()

    # Run data collection with parameters from command line
    collect_data(args.normal_out, args.time, args.interface, run_attacker=False)
    collect_data(args.attack_out, args.time, args.interface, run_attacker=True)

    # Extract features from the generated pcap files
    normal_df = extract_features(args.normal_out, 0)
    attack_df = extract_features(args.attack_out, 1)

    if normal_df.empty or attack_df.empty:
        print("Could not proceed with model training due to lack of data.")
        return

    final_df = pd.concat([normal_df, attack_df])

    X = final_df[['publish_count', 'total_packets', 'total_bytes']]
    y = final_df['label']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    print(f"\nData split into training ({len(X_train)} samples) and testing ({len(X_test)} samples).")

    print("\n--- Training RandomForest Classifier ---")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print("Model training complete.")

    print("\n--- Model Evaluation ---")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))

    print("Displaying confusion matrix...")
    fig, ax = plt.subplots(figsize=(8, 6))
    ConfusionMatrixDisplay.from_estimator(
        model, X_test, y_test, display_labels=['Normal', 'Attack'], cmap='Blues', ax=ax
    )
    plt.title('Confusion Matrix')
    plt.show()

if __name__ == '__main__':
    main()
