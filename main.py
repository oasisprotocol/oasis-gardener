from dotenv import load_dotenv
import json
import os
import subprocess
import time

TMP_WALLET_NAME="tmp_oasis_gardener"

# Load environment variables from .env file
load_dotenv()

# Read and parse WATCH_ADDRESSES environment variable
oasis_cmd = os.getenv('OASIS_CMD', 'oasis')
watch_addresses = os.getenv('WATCH_ADDRESSES', '').split(',')
secret_keys = os.getenv('SECRET_KEYS', '').split(',')
balance_threshold = float(os.getenv('BALANCE_THRESHOLD', 10))
balance_amount = float(os.getenv('BALANCE_TOPUP_AMOUNT', 100))
watch_rofl_machines = os.getenv('WATCH_ROFL_MACHINES', '').split(',')
rofl_threshold = int(os.getenv('ROFL_THRESHOLD', 1800))
rofl_topup_term = os.getenv('ROFL_TOPUP_TERM', "hour")
rofl_topup_count = int(os.getenv('ROFL_TOPUP_COUNT', 1))

def parse_secret_keys(secret_keys: list[str]) -> dict[str, tuple[str, str]]:
    sk_map = {}
    for sk in secret_keys:
        network, algorithm, secret = sk.split(':')
        if '-' not in network:
            network += '-mainnet'
        sk_map[network] = (algorithm, secret)

    return sk_map

def import_wallet(pt: str, network: str, sk_map: dict[str, tuple[str, str]]) -> bool:
    # Remove preexisting wallet.
    exec_oasis(f"wallet remove {TMP_WALLET_NAME} -y")

    # Pick the corresponding account.
    if f"{pt}-{network}" not in sk_map:
        print(f" error: Secret key to fund ROFL machine not found.")
        return False
    algorithm, secret = sk_map[f"{pt}-{network}"]

    # Import funding account.
    wallet_import_result = exec_oasis(f"wallet import {TMP_WALLET_NAME} --algorithm {algorithm} --secret {secret} -y")

    if wallet_import_result.returncode != 0:
        print(f" error: Secret key import failed: {wallet_import_result.stderr}")
        return False

    return True

def exec_oasis(params: str):
    return subprocess.run(
        f"{oasis_cmd} {params}",
        shell=True,
        capture_output=True,
        text=True
    )

def main():
    sk_map = parse_secret_keys(secret_keys)
    print(f"Imported {len(sk_map)} secret keys")
    print(rofl_topup_term)
    while True:
        for wa in watch_addresses:
            a = wa.split(':', 1)
            pt, network = (a[0] if '-' in a[0] else a[0]+"-mainnet").split('-')

            result = exec_oasis(f"account show {a[1]} --network {network} {"--paratime "+pt if pt!="consensus" else "--no-paratime"} --format json")
            if result.returncode == 0 and result.stdout:
                mOut = {}
                try:
                    mOut = json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON for {wa}: {e}")
                    continue
            else:
                print(f"Error retrieving account data for {wa}: {result.stderr}")
                continue

            balance = int(mOut["general_account"]["balance"]) * 10**(-9)
            if pt!="consensus":
                balance = int(mOut["paratime_balances"][""]) * 10**(-18)

            print(f"Fetched account {wa}: balance {balance}")
            if balance < int(balance_threshold):
                print(f" Transferring {balance_amount} to {wa}")

                if not import_wallet(pt, network, sk_map):
                    print(f" error: Secret key to topup ROFL machine {wa} not found. Ignoring.")
                    continue

                topup_result = exec_oasis(f"account transfer {balance_amount} {a[1]} --network {network} {"--paratime " + pt if pt != "consensus" else "--no-paratime"} --account {TMP_WALLET_NAME} -y")
                if topup_result.returncode == 0:
                    print(f" Transfer of {balance_amount} successful to {wa}")
                else:
                    print(f" Transfer failed to {wa}: {topup_result.stderr}")

                # Remove tmp wallet for security.
                exec_oasis(f"wallet remove {TMP_WALLET_NAME} -y")
            else:
                print(f" Threshold {balance_threshold} not reached")

            # Avoid quota limits.
            time.sleep(10)

        for wrm in watch_rofl_machines:
            m = wrm.split(':', 1)
            pt, network = (m[0] if '-' in m[0] else m[0]+"-mainnet").split('-')

            result = exec_oasis(f"rofl machine show {m[1]} --network {network} --paratime {pt} --format json")
            if result.returncode == 0 and result.stdout:
                mOut = {}
                try:
                    mOut = json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON for {wrm}: {e}")
                    continue
            else:
                print(f"Error retrieving ROFL machine data for {wrm}: {result.stderr}")
                continue

            paid_until = int(mOut["machine"]["paid_until"])

            cur_time = int(time.time())
            print(f"Fetched rofl machine {wrm}: paid_until {paid_until}, cur_time {cur_time}")
            if paid_until - rofl_threshold < cur_time:
                print(f" Topping up {wrm} for {rofl_topup_count}x {rofl_topup_term}")

                if not import_wallet(pt, network, sk_map):
                    print(f" error: Secret key to topup ROFL machine {wrm} not found. Ignoring.")
                    continue

                topup_result = exec_oasis(f"rofl machine top-up {m[1]} --term {rofl_topup_term} --term-count {rofl_topup_count} --network {network} --paratime {pt} --account {TMP_WALLET_NAME} -y")
                if topup_result.returncode == 0:
                    print(f" Top up {wrm} for {rofl_topup_count}x {rofl_topup_term} successful")
                else:
                    print(f" Top up failed for {wrm}: {topup_result.stderr}")

                # Remove tmp wallet for security.
                exec_oasis(f"wallet remove {TMP_WALLET_NAME} -y")
            else:
                print(f" Threshold {rofl_threshold}s not reached")

            # Avoid quota limits.
            time.sleep(10)


if __name__ == "__main__":
    main()