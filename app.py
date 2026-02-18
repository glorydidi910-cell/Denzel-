# app.py - Modern Remittance App (Dark Fintech Style)

import streamlit as st
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import random
import time

# ── Theme Setup (add to .streamlit/config.toml for persistence, but inline here too)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stButton>button { background-color: #2962ff; color: white; border-radius: 8px; padding: 10px 24px; font-weight: bold; }
    .stButton>button:hover { background-color: #0039cb; }
    .card { background: linear-gradient(135deg, #1e293b, #111827); border-radius: 16px; padding: 24px; margin: 16px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }
    .quote-card { background: #1e40af22; border: 1px solid #3b82f6; }
    .success { color: #10b981; font-size: 1.4em; font-weight: bold; }
    .metric { font-size: 2.2em !important; }
    </style>
""", unsafe_allow_html=True)

# ── Models (your originals, enhanced)
@dataclass
class Currency:
    code: str
    balance: float = 0.0

@dataclass
class User:
    id: str
    name: str
    currencies: dict[str, Currency]
    phone: str

@dataclass
class Quote:
    id: str
    source_currency: str
    target_currency: str
    rate: float
    fees: float
    expiry: datetime
    amount_sent: float
    amount_received: float

@dataclass
class Transaction:
    id: str
    sender_id: str
    receiver_id: str
    amount_sent: float
    currency_sent: str
    amount_received: float
    currency_received: str
    quote_id: str
    status: str = "Pending"
    timestamp: datetime = datetime.now()

# ── In-memory DB (prototype; use SQLite/Supabase for real)
if "users" not in st.session_state:
    st.session_state.users = {}
if "quotes" not in st.session_state:
    st.session_state.quotes = {}
if "transactions" not in st.session_state:
    st.session_state.transactions = []

def calculate_fees(amount: float) -> float:
    return round(amount * 0.012 + 0.50, 2)  # 1.2% + $0.50 (modern low-fee vibe)

def format_currency(amount: float, code: str) -> str:
    symbols = {"USD": "$", "EUR": "€", "NGN": "₦"}
    return f"{symbols.get(code, code)} {amount:,.2f}"

# ── Processor
class PaymentProcessor:
    def resolve_receiver(self, phone: str):
        user = st.session_state.users.get(phone)
        if not user:
            return None
        return {
            "user": user,
            "currencies": list(user.currencies.keys()),
            "min_amount": 5.0,
            "max_amount": 15000.0
        }

    def create_quote(self, source: str, target: str, amount: float) -> Quote:
        # Simulate real rate fetch (in prod: call API)
        base_rates = {("USD", "EUR"): 0.93, ("USD", "NGN"): 1620.0, ("EUR", "NGN"): 1750.0}
        rate = base_rates.get((source, target), random.uniform(0.85, 1.15))
        fees = calculate_fees(amount)
        received = round(amount * rate - fees, 2)

        quote = Quote(
            id=str(uuid.uuid4()),
            source_currency=source,
            target_currency=target,
            rate=rate,
            fees=fees,
            expiry=datetime.now() + timedelta(minutes=10),
            amount_sent=amount,
            amount_received=received
        )
        st.session_state.quotes[quote.id] = quote
        return quote

# ── UI
st.title("✨ Denzel's Remit – Fast & Secure Transfers")
st.caption("International money transfers with locked rates & low fees • Port Harcourt powered 💪")

# Sidebar: User Profile / Balances
with st.sidebar:
    st.header("Your Wallet")
    phone = st.text_input("Phone Number", value="+234", key="phone")
    
    if phone and phone not in st.session_state.users:
        # Demo user creation
        user = User(
            id=str(uuid.uuid4()),
            name="Denzel",
            phone=phone,
            currencies={
                "USD": Currency("USD", 2500.00),
                "EUR": Currency("EUR", 1800.00),
                "NGN": Currency("NGN", 4500000.00)
            }
        )
        st.session_state.users[phone] = user
    
    if phone in st.session_state.users:
        user = st.session_state.users[phone]
        for curr in user.currencies.values():
            st.metric(f"{curr.code} Balance", format_currency(curr.balance, curr.code))

# Main Flow
receiver_phone = st.text_input("Receiver's Phone Number", placeholder="+234... or international")

if receiver_phone:
    processor = PaymentProcessor()
    receiver_info = processor.resolve_receiver(receiver_phone)

    supported = ["USD", "EUR", "NGN"]
    receiver_name = "Unknown (will create on send)" if not receiver_info else receiver_info["user"].name

    st.info(f"Recipient: **{receiver_name}** • Supported currencies: {', '.join(supported)}")

    col1, col2, col3 = st.columns([2, 2, 1])
    source_curr = col1.selectbox("You Send", ["USD", "EUR", "NGN"], index=0)
    target_curr = col2.selectbox("They Receive", supported, index=supported.index("NGN") if "NGN" in supported else 0)
    amount = col3.number_input("Amount", min_value=5.0, max_value=15000.0, step=10.0, format="%.2f")

    if st.button("🔒 Get Locked Quote", type="primary", use_container_width=True) and amount > 0:
        with st.spinner("Fetching best rate..."):
            time.sleep(1.2)  # simulate API call
            quote = processor.create_quote(source_curr, target_curr, amount)
            st.session_state.current_quote = quote
            st.session_state.quote_time = time.time()

    if "current_quote" in st.session_state:
        quote = st.session_state.current_quote

        # Expiry countdown
        elapsed = time.time() - st.session_state.quote_time
        remaining = max(0, (quote.expiry - datetime.now()).total_seconds())
        if remaining <= 0:
            st.warning("Quote expired. Get a new one.")
            del st.session_state.current_quote
        else:
            mins, secs = divmod(int(remaining), 60)
            st.caption(f"Quote expires in {mins}m {secs}s")

            with st.container():
                st.markdown('<div class="card quote-card">', unsafe_allow_html=True)
                st.subheader("Your Locked Quote")
                col_a, col_b = st.columns(2)
                col_a.metric("Rate", f"1 {quote.source_currency} = {quote.rate:,.4f} {quote.target_currency}")
                col_b.metric("Fees", format_currency(quote.fees, quote.source_currency), delta="-low fees")
                
                st.divider()
                st.metric("You Send", format_currency(quote.amount_sent, quote.source_currency), label_visibility="visible")
                st.metric("They Get (after fees)", format_currency(quote.amount_received, quote.target_currency), 
                          delta_color="normal", label_visibility="visible")
                st.markdown('</div>', unsafe_allow_html=True)

            if st.button("🚀 Confirm & Transfer", type="primary", use_container_width=True):
                with st.spinner("Processing secure transfer..."):
                    time.sleep(2.5)  # simulate processing
                    tx = Transaction(
                        id=str(uuid.uuid4()),
                        sender_id=st.session_state.users[phone].id,
                        receiver_id=receiver_phone,
                        amount_sent=quote.amount_sent,
                        currency_sent=quote.source_currency,
                        amount_received=quote.amount_received,
                        currency_received=quote.target_currency,
                        quote_id=quote.id,
                        status="Settled"
                    )
                    st.session_state.transactions.append(tx)
                    
                    # Fake balance update
                    sender_bal = st.session_state.users[phone].currencies[quote.source_currency]
                    sender_bal.balance -= (quote.amount_sent + quote.fees)
                    
                    st.balloons()  # fun success
                    st.success(f"**Transfer Complete!** 🎉 ID: {tx.id[:8]}")
                    st.markdown(f"<p class='success'>Sent {format_currency(quote.amount_sent, quote.source_currency)} → Received {format_currency(quote.amount_received, quote.target_currency)}</p>", unsafe_allow_html=True)
                    
                    # Clear quote
                    del st.session_state.current_quote

# Recent Transactions
if st.session_state.transactions:
    st.subheader("Recent Activity")
    for tx in reversed(st.session_state.transactions[-5:]):
        st.markdown(f"<div class='card'><strong>{tx.status}</strong> • {tx.timestamp.strftime('%b %d, %H:%M')} • {format_currency(tx.amount_sent, tx.currency_sent)} → {format_currency(tx.amount_received, tx.currency_received)}</div>", unsafe_allow_html=True)
