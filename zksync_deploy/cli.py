"""Console script for zksync_deploy."""
import sys
import click

import json
import os
from pathlib import Path
from eth_typing import HexStr
from web3 import Web3
from web3.types import TxParams
from zksync2.manage_contracts.contract_deployer import ContractDeployer
from zksync2.manage_contracts.nonce_holder import NonceHolder
from zksync2.module.module_builder import ZkSyncBuilder
from zksync2.core.types import ZkBlockParams, EthBlockParams
from eth_account import Account
from eth_account.signers.local import LocalAccount
from zksync2.signer.eth_signer import PrivateKeyEthSigner
from zksync2.transaction.transaction712 import TxCreateContract


def generate_random_salt() -> bytes:
    return os.urandom(32)


def read_hex_binary(name: str) -> bytes:
    p = Path(f"./{name}")
    with p.open(mode='r') as contact_file:
        lines = contact_file.readlines()
        data = "".join(lines)
        return bytes.fromhex(data)


def read_binary(p: Path) -> bytes:
    with p.open(mode='rb') as contact_file:
        data = contact_file.read()
        return data


def get_abi(p: Path):
    with p.open(mode='r') as json_f:
        return json.load(json_f)


def read_abi(file_path: str):
    with open(file_path, 'r') as json_f:
        return json.load(json_f)


class ContractEncoder:
    def __init__(self, web3: Web3, bin_path: Path, abi_path: Path):
        self.web3 = web3
        self.contract_instance = self.web3.eth.contract(abi=get_abi(abi_path),
                                                        bytecode=read_hex_binary(str(bin_path)))

    def encode_method(self, fn_name, args: list) -> HexStr:
        return self.contract_instance.encodeABI(fn_name, args)


def deploy_contract_create(contract_hex: str = "contract.hex", abi: str = "contract_abi.json"):
    account: LocalAccount = Account.from_key("PRIVATE_KEY")
    zksync_web3 = ZkSyncBuilder.build("ZKSYNC_NETWORK_URL")
    chain_id = zksync_web3.zksync.chain_id
    signer = PrivateKeyEthSigner(account, chain_id)

    contract_bin = read_hex_binary(contract_hex)

    nonce = zksync_web3.zksync.get_transaction_count(account.address, EthBlockParams.PENDING.value)
    gas_price = zksync_web3.zksync.gas_price

    nonce_holder = NonceHolder(zksync_web3, account)
    deployment_nonce = nonce_holder.get_deployment_nonce(account.address)
    deployer = ContractDeployer(zksync_web3)
    precomputed_address = deployer.compute_l2_create_address(account.address, deployment_nonce)

    print(f"precomputed address: {precomputed_address}")

    random_salt = generate_random_salt()
    create_contract = TxCreateContract(web3=zksync_web3,
                                       chain_id=chain_id,
                                       nonce=nonce,
                                       from_=account.address,
                                       gas_limit=0,  # unknown at this state, will be replaced by estimate_gas
                                       gas_price=gas_price,
                                       bytecode=contract_bin,
                                       salt=random_salt)
    estimate_gas = zksync_web3.zksync.eth_estimate_gas(create_contract.tx)
    print(f"Fee for transaction is: {estimate_gas * gas_price}")

    tx_712 = create_contract.tx712(estimate_gas)

    singed_message = signer.sign_typed_data(tx_712.to_eip712_struct())
    msg = tx_712.encode(singed_message)
    tx_hash = zksync_web3.zksync.send_raw_transaction(msg)
    print(f"tx_hash:{tx_hash.hex()}")
    tx_receipt = zksync_web3.zksync.wait_for_transaction_receipt(tx_hash, timeout=240, poll_latency=0.5)
    print(f"tx status: {tx_receipt['status']}")

    contract_address = tx_receipt["contractAddress"]
    print(f"contract address: {contract_address}")
    contract_encoder = ContractEncoder(zksync_web3, Path(contract_hex), Path(abi))

    call_data = contract_encoder.encode_method(fn_name="get", args=[])
    eth_tx: TxParams = {
        "from": account.address,
        "to": contract_address,
        "data": call_data
    }
    # Value is type dependent so might need to be converted to corresponded type under Python
    eth_ret = zksync_web3.zksync.call(eth_tx, ZkBlockParams.COMMITTED.value)
    converted_result = int.from_bytes(eth_ret, "big", signed=True)
    print(f"Call method for deployed contract, address: {contract_address}, value: {converted_result}")


@click.group()
def cli():
    pass


@click.command()
@click.argument("contract_hex")
@click.argument("abi")
def deploy(contract_hex, abi):
    """Console script for zksync_deploy."""
    deploy_contract_create(contract_hex, abi)



if __name__ == "__main__":
    # sys.exit(main())  # pragma: no cover
    cli.add_command(deploy)
    cli()
