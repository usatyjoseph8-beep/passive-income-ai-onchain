from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, List

from connectors.eth_readonly import get_wallet_address, get_eth_balance, get_erc20_balance
from engine.state import upsert_daily_balance, get_prev_balance

# Known token addresses on Ethereum mainnet
TOKENS = {
    "ETH": {"type": "native", "symbol": "ETH"},
    "stETH": {"type": "erc20", "address": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84", "symbol": "stETH"},
    "rETH": {"type": "erc20", "address": "0xae78736Cd615f374D3085123A210448E74Fc6393", "symbol": "rETH"},
}

@dataclass
class Earning:
    source: str
    amount: float
    note: str = ""

@dataclass
class DecisionProposal:
    strategy: str
    action: str
    payload: dict
    estimated_value: float
    note: str = ""

class TokenDeltaStrategy:
    name: str = "TokenDelta"

    def __init__(self, token: str):
        if token not in TOKENS:
            raise ValueError("Unsupported token")
        self.token = token

    def scan(self) -> Tuple[List[Earning], List[DecisionProposal]]:
        addr = get_wallet_address()
        if not addr:
            return [], []
        today = datetime.utcnow().date().isoformat()

        # Fetch balance
        meta = TOKENS[self.token]
        if meta["type"] == "native":
            bal = get_eth_balance(addr)
            symbol = "ETH"
        else:
            symbol, bal = get_erc20_balance(meta["address"], owner=addr)

        # Store today's balance
        upsert_daily_balance(symbol, bal, today)

        # Compare to yesterday
        prev = get_prev_balance(symbol, today)
        earnings: List[Earning] = []
        if prev is not None:
            delta = bal - prev
            # Only positive delta counts as "earnings"
            if delta > 0:
                earnings.append(Earning(source=f"{symbol} yield", amount=delta, note=f"Balance delta vs yesterday: +{delta:.8f} {symbol}"))
        return earnings, []
