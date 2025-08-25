# linea_bridge_comp.py
# pip install web3 python-dotenv eth_account

import os, sys, time
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()  # .env: LINEA_RPC, PRIV_KEY, ETH_RPC (если будете клеймить авто)

LINEA_RPC   = "https://rpc.linea.build"
PRIVATE_KEY = os.getenv("L1_PK")
ACCOUNT     = Web3.to_checksum_address(Account.from_key(PRIVATE_KEY).address.lower())

TOKEN  = Web3.to_checksum_address("0x0ECE76334Fb560f2b1a49A60e38Cf726B02203f0")
BRIDGE = Web3.to_checksum_address("0x353012dc4a9A6cF55c941bADC267f82004A8ceB9")
RECIPIENT = ACCOUNT        # получатель на L1; можно любой другой EOA

ERC20_ABI = [
    {"name":"balanceOf","type":"function","stateMutability":"view",
     "inputs":[{"name":"owner","type":"address"}],"outputs":[{"type":"uint256"}]},
    {"name":"allowance","type":"function","stateMutability":"view",
     "inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],
     "outputs":[{"type":"uint256"}]},
    {"name":"approve","type":"function","stateMutability":"nonpayable",
     "inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],
     "outputs":[{"type":"bool"}]},
    {"name":"decimals","type":"function","stateMutability":"view",
     "inputs":[],"outputs":[{"type":"uint8"}]},
]

BRIDGE_ABI = [
    {"name":"bridgeToken","type":"function","stateMutability":"payable",
     "inputs":[
        {"name":"_token","type":"address"},
        {"name":"_amount","type":"uint256"},
        {"name":"_recipient","type":"address"}
     ],
     "outputs":[]},
]

w3 = Web3(Web3.HTTPProvider(LINEA_RPC))
if not w3.is_connected():
    sys.exit("❌  RPC not reachable")

token = w3.eth.contract(TOKEN, abi=ERC20_ABI)
bridge = w3.eth.contract(BRIDGE, abi=BRIDGE_ABI)

decimals = token.functions.decimals().call()
balance  = token.functions.balanceOf(ACCOUNT).call()

if balance == 0:
    sys.exit("⚠️  COMP balance is zero – nothing to bridge")

human = Decimal(balance) / (10 ** decimals)
print(f"✓  COMP balance on Linea: {human:,}")

allowance = token.functions.allowance(ACCOUNT, BRIDGE).call()
nonce     = w3.eth.get_transaction_count(ACCOUNT)

def send(tx):
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"→  sent {tx['nonce']} | {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✔︎  confirmed in block {receipt.blockNumber}")
    return receipt

gas_price = w3.eth.gas_price          # можно заменить своей логикой

# 1) approve, если нужно
if allowance < balance:
    tx = token.functions.approve(BRIDGE, balance).build_transaction({
        "from": ACCOUNT,
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": 60_000,               # достаточный лимит для approve
    })
    receipt = send(tx)
    nonce += 1
    time.sleep(3)

# 2) bridgeToken (payableAmount=0 => claim придётся делать вручную)
tx = bridge.functions.bridgeToken(TOKEN, balance, RECIPIENT).build_transaction({
    "from": ACCOUNT,
    "nonce": nonce,
    "gasPrice": gas_price,
    "gas": 150_000,                  # чуть с запасом
    "value": 100000000000000,                       # хотели бы авто-claim – укажите ~0.002 ETH
})

send(tx)
print("🎉  Bridge initiated!  Check LineaScan for L2→L1 message.")
