from __future__ import annotations
import os
import requests
from engine.state import get_setting, set_setting

DEFAULT_RPC = "https://ethereum.publicnode.com"

def _rpc_url():
    return os.getenv("RPC_URL", DEFAULT_RPC)

def _rpc(method: str, params: list):
    url = _rpc_url()
    payload = {"jsonrpc":"2.0","id":1,"method":method,"params":params}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise RuntimeError(j["error"])
    return j["result"]

def set_wallet_address(addr: str):
    set_setting("WALLET_ADDRESS", addr.strip())

def get_wallet_address() -> str:
    return get_setting("WALLET_ADDRESS", "")

def _to_checksum(addr: str) -> str:
    # Minimal sanity check; JSON-RPC accepts lowercase hex addresses fine.
    if not addr or not addr.startswith("0x") or len(addr) != 42:
        raise ValueError("Invalid address")
    return addr

def _hex_to_int(h: str) -> int:
    return int(h, 16) if h else 0

def get_eth_balance(addr: str) -> float:
    c = _to_checksum(addr)
    wei_hex = _rpc("eth_getBalance", [c, "latest"])
    return _hex_to_int(wei_hex) / 10**18

# --- ERC20 helpers (minimal) ---
# function selectors
SEL_BALANCE_OF = "0x70a08231"  # balanceOf(address)
SEL_DECIMALS   = "0x313ce567"  # decimals()
SEL_SYMBOL     = "0x95d89b41"  # symbol()

def _pad32(hex_no0x: str) -> str:
    return hex_no0x.rjust(64, "0")

def _eth_call(to_addr: str, data: str) -> str:
    call = {"to": to_addr, "data": data}
    res = _rpc("eth_call", [call, "latest"])
    return res or "0x"

def _decode_uint(hexdata: str) -> int:
    if not hexdata or hexdata == "0x":
        return 0
    return int(hexdata, 16)

def _decode_ascii(hexdata: str) -> str:
    # Try simple bytes -> ascii; handle both dynamic and bytes32 forms
    if not hexdata or hexdata == "0x":
        return ""
    h = hexdata[2:]
    try:
        # dynamic string: first 32 bytes offset, then length, then data
        if len(h) >= 128:
            length = int(h[64:128], 16)
            data = bytes.fromhex(h[128:128+length*2])
        else:
            data = bytes.fromhex(h).rstrip(b"\x00")
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""

KNOWN = {
    "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84": ("stETH", 18),
    "0xae78736Cd615f374D3085123A210448E74Fc6393": ("rETH", 18),
}

def get_erc20_balance(token_addr: str, owner: str) -> tuple[str, float]:
    owner_clean = _to_checksum(owner)
    to = token_addr
    # balanceOf(owner)
    data = SEL_BALANCE_OF + "000000000000000000000000" + owner_clean[2:]
    bal_hex = _eth_call(to, data)
    bal = _decode_uint(bal_hex)

    # decimals
    dec_hex = _eth_call(to, SEL_DECIMALS)
    if dec_hex == "0x" and token_addr in KNOWN:
        symbol, dec = KNOWN[token_addr]
    else:
        dec = _decode_uint(dec_hex)
        # symbol
        sym_hex = _eth_call(to, SEL_SYMBOL)
        symbol = _decode_ascii(sym_hex) or KNOWN.get(token_addr, ("", 18))[0]

    amount = bal / (10 ** (dec or 18))
    return (symbol or "TOKEN", amount)
