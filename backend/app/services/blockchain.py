import hashlib
import json
from pathlib import Path

from web3 import Web3


# ============================================================
# REPAIR HASHING
# ============================================================

def generate_repair_hash(
    repair_id: str,
    product_id: int,
    issue_description: str,
    diagnosis: str | None
) -> str:
    """
    Generate a deterministic SHA-256 hash for a repair record.

    The same repair data will always generate the same hash.
    """

    repair_data = {
        "repair_id": repair_id,
        "product_id": product_id,
        "issue_description": issue_description,
        "diagnosis": diagnosis
    }

    serialized_data = json.dumps(
        repair_data,
        sort_keys=True,
        default=str
    )

    return hashlib.sha256(
        serialized_data.encode("utf-8")
    ).hexdigest()


def verify_repair_hash(
    repair_id: str,
    product_id: int,
    issue_description: str,
    diagnosis: str | None,
    stored_hash: str
) -> bool:
    """
    Verify that the current repair data produces the
    same SHA-256 hash that was originally stored.
    """

    if not stored_hash:
        return False

    current_hash = generate_repair_hash(
        repair_id=repair_id,
        product_id=product_id,
        issue_description=issue_description,
        diagnosis=diagnosis
    )

    return current_hash == stored_hash


# ============================================================
# BLOCKCHAIN CONFIGURATION
# ============================================================

BLOCKCHAIN_RPC_URL = "http://127.0.0.1:8545"

# Hardhat local development account.
# This private key is ONLY for the local Hardhat network.
BLOCKCHAIN_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)

# Deployed RepairChain contract on the local Hardhat network.
REPAIR_CHAIN_ADDRESS = (
    "0x5FbDB2315678afecb367f032d93F642f64180aa3"
)


# ============================================================
# WEB3 CONNECTION
# ============================================================

def get_repair_chain_contract():
    """
    Connect to the local blockchain and return:

        web3
        contract

    Raises an exception if the blockchain is unavailable.
    """

    web3 = Web3(
        Web3.HTTPProvider(
            BLOCKCHAIN_RPC_URL,
            request_kwargs={"timeout": 5}
        )
    )

    if not web3.is_connected():
        raise ConnectionError(
            "Could not connect to the local blockchain. "
            "Make sure the Hardhat node is running on "
            "http://127.0.0.1:8545."
        )

    abi_path = (
        Path(__file__).resolve().parents[2]
        / "RepairChain.json"
    )

    if not abi_path.exists():
        raise FileNotFoundError(
            f"RepairChain ABI file not found: {abi_path}"
        )

    with abi_path.open("r", encoding="utf-8") as file:
        contract_json = json.load(file)

    contract = web3.eth.contract(
        address=Web3.to_checksum_address(
            REPAIR_CHAIN_ADDRESS
        ),
        abi=contract_json["abi"]
    )

    return web3, contract


# ============================================================
# ADD REPAIR TO BLOCKCHAIN
# ============================================================

def add_repair_to_blockchain(
    repair_id: str,
    record_hash: str
) -> str:
    """
    Store the repair ID and SHA-256 record hash on-chain.

    Returns the blockchain transaction hash.
    """

    if not repair_id:
        raise ValueError("repair_id is required")

    if not record_hash:
        raise ValueError("record_hash is required")

    web3, contract = get_repair_chain_contract()

    account = web3.eth.account.from_key(
        BLOCKCHAIN_PRIVATE_KEY
    )

    nonce = web3.eth.get_transaction_count(
        account.address,
        "pending"
    )

    transaction = contract.functions.addRepairRecord(
        repair_id,
        record_hash
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": web3.eth.gas_price,
        "chainId": web3.eth.chain_id
    })

    signed_transaction = account.sign_transaction(
        transaction
    )

    tx_hash = web3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )

    receipt = web3.eth.wait_for_transaction_receipt(
        tx_hash,
        timeout=120
    )

    # Transaction status:
    # 1 = successful
    # 0 = failed
    if receipt["status"] != 1:
        raise RuntimeError(
            "Blockchain transaction failed"
        )

    return receipt["transactionHash"].hex()


# ============================================================
# VERIFY REPAIR ON BLOCKCHAIN
# ============================================================

def verify_repair_on_blockchain(
    repair_id: str,
    record_hash: str
) -> bool:
    """
    Verify that the given repair ID and hash exist
    correctly on the blockchain.
    """

    if not repair_id or not record_hash:
        return False

    try:
        _, contract = get_repair_chain_contract()

        result = contract.functions.verifyRepair(
            repair_id,
            record_hash
        ).call()

        return bool(result)

    except Exception:
        return False


# ============================================================
# GET REPAIR RECORD FROM BLOCKCHAIN
# ============================================================

def get_repair_record_from_blockchain(
    repair_id: str
):
    """
    Retrieve a repair record directly from the
    RepairChain smart contract.

    Returns None if the blockchain is unavailable
    or the record cannot be retrieved.
    """

    if not repair_id:
        return None

    try:
        _, contract = get_repair_chain_contract()

        record = contract.functions.getRepairRecord(
            repair_id
        ).call()

        return record

    except Exception:
        return None


# ============================================================
# COMPLETE BLOCKCHAIN VERIFICATION
# ============================================================

def verify_repair_blockchain_integrity(
    repair_id: str,
    product_id: int,
    issue_description: str,
    diagnosis: str | None,
    stored_hash: str
) -> dict:
    """
    Perform complete verification:

    1. Recalculate SHA-256 hash from database data.
    2. Compare it with the stored database hash.
    3. Verify the same hash on the blockchain.

    This gives us a clearer verification result than
    simply checking whether a transaction hash exists.
    """

    if not stored_hash:
        return {
            "verified": False,
            "hash_valid": False,
            "blockchain_valid": False,
            "reason": "No stored repair hash found"
        }

    current_hash = generate_repair_hash(
        repair_id=repair_id,
        product_id=product_id,
        issue_description=issue_description,
        diagnosis=diagnosis
    )

    hash_valid = current_hash == stored_hash

    if not hash_valid:
        return {
            "verified": False,
            "hash_valid": False,
            "blockchain_valid": False,
            "reason": "Repair data has changed since the stored hash was generated"
        }

    blockchain_valid = verify_repair_on_blockchain(
        repair_id=repair_id,
        record_hash=stored_hash
    )

    return {
        "verified": hash_valid and blockchain_valid,
        "hash_valid": hash_valid,
        "blockchain_valid": blockchain_valid,
        "current_hash": current_hash,
        "stored_hash": stored_hash
    }