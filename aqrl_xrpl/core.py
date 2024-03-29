from . import util
import json
from xrpl.wallet import generate_faucet_wallet
from xrpl.core import addresscodec
from xrpl.models.requests.account_info import AccountInfo
from xrpl.models.response import Response
from xrpl.models.response import ResponseStatus
from xrpl.models.requests import AccountNFTs
from xrpl.models.requests import AccountOffers
from xrpl.models.requests import AccountTx
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.asyncio.transaction import get_transaction_from_hash
from xrpl.wallet import Wallet

def create_altnet_faucet():
    """Create faucet using altnet client"""
    client = util.get_client(mode='altnet')
    return create_faucet(client)

def create_faucet(client):
    """Create a wallet using the testnet faucet"""
    test_wallet = generate_faucet_wallet(client, debug=True)
    return test_wallet

def create_account(wallet):
    """Create an account str from the wallet"""
    return wallet.classic_address

def create_xaddress(account):
    """Derive an x-address from the classic address"""
    xaddress = addresscodec.classic_address_to_xaddress(account, tag=12345, is_test_network=True)
    print("\nClassic address:\n\n", account)
    print("X-address:\n\n", xaddress)
    return xaddress

def lookup_account_info(test_account):
    """Look up info about your account"""
    client = util.get_client(mode='altnet')
    acct_info = AccountInfo(
        account=test_account,
        ledger_index="validated",
        strict=True,
    )
    response = client.request(acct_info)
    result = response.result
    print(json.dumps(response.result, indent=4, sort_keys=True))
    return response.status == ResponseStatus.SUCCESS

class XRPLAccount:
    """Representaiton of an account on XRPL including wallet"""

    def __init__(self, secret: str, network_url: str) -> None:
        self.secret = secret
        self.network_url = network_url
        self.wallet = Wallet(secret, 0)
        self.address = self.wallet.classic_address
        self.nfts = {}

    def __str__(self):
        return f"ACCOUNT: {self.address}"

    async def get_nfts(self, limit: int = 100, marker: str = None, debug: bool = False):
        async with AsyncWebsocketClient(self.network_url) as client:
            self.get_nfts_response = await client.request(
                AccountNFTs(
                    account=self.address,
                    limit=limit,
                    #marker=marker
                )
            )
            if debug:
                print(self.get_nfts_response.status)
                print(json.dumps(self.get_nfts_response.result, indent=4, sort_keys=True))
            return self.get_nfts_response

    async def get_offers(self, limit: int = 100, marker: str = None, debug: bool = False):
        async with AsyncWebsocketClient(self.network_url) as client:
            self.get_offers_response = await client.request(
                AccountOffers(
                    account=self.address,
                    limit=limit,
                    marker=marker
                )
            )
            if debug:
                print(self.get_offers_response.status)
                print(json.dumps(self.get_offers_response.result, indent=4, sort_keys=True))
            return self.get_offers_response

    async def get_txs(self, limit: int = 100, marker: str = None, debug: bool = False):
        async with AsyncWebsocketClient(self.network_url) as client:
            self.get_txs_response = await client.request(
                AccountTx(
                    account=self.address,
                    limit=limit,
                    marker=marker
                )
            )
            if debug:
                print(self.get_txs_response.status)
                print(json.dumps(self.get_txs_response.result, indent=4, sort_keys=True))
            return self.get_txs_response

    def parse_get_nfts_response(self) -> None:
       response = self.get_nfts_response.result
       for token in response["account_nfts"]:
           tokenID = token["TokenID"]
           self.nfts[tokenID] = token

    def list_nfts(self) -> None:
        for (tid, token) in self.nfts.items():
            print(f"{tid} -> {json.dumps(token, indent=4, sort_keys=True)}")

    def get_wallet(self) -> Wallet:
        return self.wallet

    async def get_tx_info(self, tx_hash: str, debug: bool = False) -> Response:
        async with AsyncWebsocketClient(self.network_url) as client:
            response = await get_transaction_from_hash(tx_hash, client)
            if debug:
                print(json.dumps(response.result, indent=4, sort_keys=True))
                print(response.status)
            return response
