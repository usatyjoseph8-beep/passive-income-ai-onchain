import os
import streamlit as st
from dotenv import load_dotenv

from engine.state import ensure_db, get_totals, get_earnings_df, get_decisions_df, set_setting, get_setting
from engine.scheduler import SchedulerThread
from services.income_tracker import summarize_earnings_by_source, earnings_timeseries
from services.decision_engine import approve_decision, reject_decision
from connectors.eth_readonly import set_wallet_address, get_wallet_address

load_dotenv()
st.set_page_config(page_title="Passive Income AI — On-Chain", layout="wide")

if "booted" not in st.session_state:
    ensure_db()
    st.session_state.booted = True
    st.session_state.scheduler = SchedulerThread(interval_seconds=int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "300")))
    st.session_state.scheduler.start()

st.title("Passive Income AI — On-Chain")
st.caption("Real on-chain tracking. No passwords, no private keys.")

c1, c2, c3 = st.columns(3)
totals = get_totals()
c1.metric("Total Earned (All-Time)", f"${totals['all_time']:.6f}")
c2.metric("Last 7 Days", f"${totals['last_7']:.6f}")
c3.metric("Pending Decisions", f"{totals['pending']}")

df = get_earnings_df(days=30)
if not df.empty:
    st.subheader("Earnings — last 30 days")
    ts = earnings_timeseries(df)
    st.line_chart(ts.set_index("date")["amount"])
    st.subheader("By source")
    by_src = summarize_earnings_by_source(df)
    st.bar_chart(by_src.set_index("source")["amount"])
else:
    st.info("No earnings yet. Save your wallet and run strategies.")

st.divider()
st.subheader("Decision Queue")
dec = get_decisions_df(status="pending")
if dec.empty:
    st.success("No actions need approval right now.")
else:
    for _, row in dec.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['strategy']}** proposes: **{row['action']}**")
            st.caption(f"Created: {row['created_at']}  •  Est. impact: ${row['estimated_value']:.2f}")
            if row["note"]:
                st.write(row["note"])
            b1, b2, _ = st.columns([1,1,6])
            if b1.button("Approve", key=f"a-{row['id']}"):
                approve_decision(row["id"])
                st.rerun()
            if b2.button("Reject", key=f"r-{row['id']}"):
                reject_decision(row["id"])
                st.rerun()

with st.sidebar:
    st.header("Settings")
    auto = get_setting("AUTO_APPROVE_ENABLED", default="false").lower() == "true"
    cap = float(get_setting("AUTO_APPROVE_THRESHOLD", default="1.0"))
    n_auto = st.toggle("AI Auto-Approve (cap)", value=auto)
    n_cap = st.number_input("Auto-Approve cap (units)", value=cap, min_value=0.0, step=0.1)
    if (n_auto != auto) or (n_cap != cap):
        set_setting("AUTO_APPROVE_ENABLED", str(n_auto).lower())
        set_setting("AUTO_APPROVE_THRESHOLD", str(n_cap))
        st.toast("Settings saved")

    st.divider()
    st.subheader("On-Chain Read-Only")
    w = st.text_input("Public wallet address (EVM)", value=get_wallet_address(), placeholder="0x...")
    if st.button("Save wallet address"):
        set_wallet_address(w.strip())
        st.toast("Wallet address saved")

    st.caption("RPC URL (optional). Set RPC_URL env var for persistence.")

    st.divider()
    st.subheader("Strategies")
    st.caption("Toggle which on-chain readers are active.")
    import strategies.registry as reg
    toggles = {}
    for key, meta in reg.STRATEGIES_META.items():
        val = (get_setting(meta['setting_key'], "true").lower()=="true")
        toggles[key] = st.toggle(meta["label"], value=val)
    if st.button("Save strategy toggles"):
        for key, val in toggles.items():
            set_setting(reg.STRATEGIES_META[key]['setting_key'], str(val).lower())
        st.toast("Strategy toggles saved")

    if st.button("Run strategies now"):
        st.session_state.scheduler.nudge()
        st.toast("Scan triggered")

st.caption("© Passive Income AI — On-Chain. Public-address only; no passwords collected.")
