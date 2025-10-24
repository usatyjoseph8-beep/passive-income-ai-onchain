# Passive Income AI — On-Chain (Real, No Passwords)

This build is ready for **real-world use** without any logins:
- Reads your **public EVM wallet address** via a public RPC.
- Tracks **daily balance deltas** for ETH and common yield tokens (stETH, rETH). Any positive delta is logged as earnings.
- Keeps the “Decision Queue” for proposals (still user-approved; no private keys used).

> No usernames or passwords. No private keys. Real data from the blockchain.

## Quickstart
1. Install Python 3.10+
2. In a terminal:
   ```bash
   cd passive-income-ai-onchain
   python -m venv .venv
   . .venv/bin/activate   # Windows: .\.venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. In the sidebar, enter your **public wallet address** (0x...) and save. Toggle strategies and click **Run strategies now**.

## How it logs earnings
- For each enabled token (ETH, stETH, rETH), we read your current on-chain balance and compare it to yesterday’s stored balance.
- If the delta is **positive**, we record it as earnings for that token’s source (e.g., “stETH yield”). If negative (you moved funds), we don’t log it as earnings.
- This is a simple, conservative approach that captures staking yield growth for liquid staking tokens or interest-bearing assets.
- Uses a public RPC by default; you can set `RPC_URL` to your own provider for better reliability.

## Security
- Public address only. No secrets stored.
- To add CEX or affiliate sources later, use API keys **locally** in a `.env` file you control. Do not share secrets here.
