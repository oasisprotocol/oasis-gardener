from dotenv import load_dotenv
import json
import os
import subprocess
import time

TMP_WALLET_NAME="tmp_oasis_gardener"

# Load environment variables from .env file
load_dotenv()

# Read and parse WATCH_ADDRESSES environment variable
watch_addresses = os.getenv('WATCH_ADDRESSES', '').split(',')
algorithm, secret = os.getenv('SECRET_KEY', '').split(':')

threshold = float(os.getenv('THRESHOLD', 10))
amount = float(os.getenv('TOPUP_AMOUNT', 100))

while True:
    for wa in watch_addresses:
        a = wa.split(':', 1)
        pt, network = (a[0] if '-' in a[0] else a[0]+"-mainnet").split('-')
        if pt=="consensus":
            pt = ""

        result = subprocess.run(
            f"oasis account show {a[1]} --network {network} {"--paratime "+pt if pt else "--no-paratime"} --format json",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout:
            acc = {}
            try:
                acc = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON for {wa}: {e}")
                continue
        else:
            print(f"Error retrieving account data for {wa}: {result.stderr}")
            continue

        balance = int(acc["general"]["balance"]) * 10**(-9)
        if pt:
            balance = int(acc["paratime_balances"][""]) * 10**(-18)

        print(f"Fetched account {wa}: balance {balance}, threshold {threshold}")
        if balance < int(os.getenv('THRESHOLD', 10)):
            print(f"Transferring {amount} to {wa}")

            # Remove preexisting wallet.
            subprocess.run(
                f"oasis wallet remove {TMP_WALLET_NAME} -y",
                shell=True,
                capture_output=True,
                text=True
            )

            print("wallet removed")
            # Import funding account.
            wallet_import_result = subprocess.run(
                f"oasis wallet import {TMP_WALLET_NAME} --algorithm {algorithm} --secret {secret} -y",
                shell=True,
                capture_output=True,
                text=True
            )
            print("wallet imported")

            if wallet_import_result.returncode != 0:
                print(f"Secret key import failed: {wallet_import_result.stderr}")
                continue

            transfer_result = subprocess.run(
                f"oasis account transfer {amount} {a[1]} --network {network} {"--paratime "+pt if pt else "--no-paratime"} --account {TMP_WALLET_NAME} -y",
                shell=True,
                capture_output=True,
                text=True
            )

            if transfer_result.returncode == 0:
                print(f"Transfer of {amount} successful to {wa}")
            else:
                print(f"Transfer failed to {wa}: {transfer_result.stderr}")

            # Remove tmp wallet for security.
            subprocess.run(
                f"oasis wallet remove {TMP_WALLET_NAME} -y",
                shell=True,
                capture_output=True,
                text=True
            )
        else:
            print("Threshold not reached")

        # Avoid quota limits.
        time.sleep(10)