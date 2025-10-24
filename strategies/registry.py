from __future__ import annotations
from typing import List, Tuple
from dataclasses import dataclass

from engine.state import get_setting
from .token_delta import TokenDeltaStrategy

STRATEGIES_META = {
    "eth_delta": {"label": "ETH Balance Delta", "setting_key": "STRAT_ETH_DELTA"},
    "steth_delta": {"label": "stETH Yield Delta", "setting_key": "STRAT_STETH_DELTA"},
    "reth_delta": {"label": "rETH Yield Delta", "setting_key": "STRAT_RETH_DELTA"},
}

def get_enabled_strategies() -> list:
    strategies = []
    if get_setting(STRATEGIES_META["eth_delta"]["setting_key"], "true").lower() == "true":
        strategies.append(TokenDeltaStrategy(token="ETH"))
    if get_setting(STRATEGIES_META["steth_delta"]["setting_key"], "true").lower() == "true":
        strategies.append(TokenDeltaStrategy(token="stETH"))
    if get_setting(STRATEGIES_META["reth_delta"]["setting_key"], "true").lower() == "true":
        strategies.append(TokenDeltaStrategy(token="rETH"))
    return strategies
