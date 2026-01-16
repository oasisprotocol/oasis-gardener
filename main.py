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
secret_keys = os.getenv('SECRET_KEYS', '').split(',')
threshold = float(os.getenv('THRESHOLD', 10))
amount = float(os.getenv('TOPUP_AMOUNT', 100))

def parse_secret_keys(secret_keys: list[str]) -> dict[str, tuple[str, str]]:
    sk_map = {}
    for sk in secret_keys:
        network, algorithm, secret = sk.split(':')
        if '-' not in network:
            network += '-mainnet'
        sk_map[network] = (algorithm, secret)

    return sk_map

def exec_oasis(params: str):
    return subprocess.run(
        f"oasis {params}",
        shell=True,
        capture_output=True,
        text=True
    )

def main():
    sk_map = parse_secret_keys(secret_keys)
    print(f"Imported {len(sk_map)} secret keys")

    while True:
        for wa in watch_addresses:
            a = wa.split(':', 1)
            pt, network = (a[0] if '-' in a[0] else a[0]+"-mainnet").split('-')

            result = exec_oasis(f"account show {a[1]} --network {network} {"--paratime "+pt if pt!="consensus" else "--no-paratime"} --format json")
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
            if pt!="consensus":
                balance = int(acc["paratime_balances"][""]) * 10**(-18)

            print(f"Fetched account {wa}: balance {balance}")
            if balance < int(os.getenv('THRESHOLD', 10)):
                print(f" Transferring {amount} to {wa}")

                # Remove preexisting wallet.
                exec_oasis(f"wallet remove {TMP_WALLET_NAME} -y")

                # Pick the corresponding account.
                if f"{pt}-{network}" not in sk_map:
                    print(f" error: Secret key to fund account {wa} not found. Ignoring.")
                    print(sk_map)
                    print(network)
                    continue
                algorithm, secret = sk_map[f"{pt}-{network}"]

                # Import funding account.
                wallet_import_result = exec_oasis(f"wallet import {TMP_WALLET_NAME} --algorithm {algorithm} --secret {secret} -y")

                if wallet_import_result.returncode != 0:
                    print(f" error: Secret key import failed: {wallet_import_result.stderr}")
                    continue

                transfer_result = exec_oasis(f"account transfer {amount} {a[1]} --network {network} {"--paratime "+pt if pt!="consensus" else "--no-paratime"} --account {TMP_WALLET_NAME} -y")
                if transfer_result.returncode == 0:
                    print(f" Transfer of {amount} successful to {wa}")
                else:
                    print(f" Transfer failed to {wa}: {transfer_result.stderr}")

                # Remove tmp wallet for security.
                exec_oasis(f"wallet remove {TMP_WALLET_NAME} -y")
            else:
                print(f" Threshold {threshold} not reached")

            # Avoid quota limits.
            time.sleep(10)

if __name__ == "__main__":
    main()