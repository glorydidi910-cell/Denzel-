# app.py   ← main file name expected by Streamlit

import streamlit as st
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import random  # placeholder for real fee calc / rate fetch

# Your models (completed / cleaned up)
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

# Fake in-memory "database"
users = {}           # phone -> User
quotes = {}          # quote_id -> Quote

def calculate_fees(amount: float) -> float:
    return round(amount * 0.015 + 1.0, 2)  # example: 1.5% + fixed $1

class PaymentProcessor:
    def resolve_receiver(self, phone: str):
        if phone not in users:
            return None
        user = users[phone]
        return {
            "user": user,
            "currencies": [c.code for c in user.currencies.values()],
            "min_amount": 1.0,
            "max_amount": 10000.0
        }

    def create_quote(self, source: str, target: str, amount: float) -> Quote:
        rate = 0.92 if source == "USD" and target == "EUR" else random.uniform(0.8, 1.2)
        fees = calculate_fees(amount)
        expiry = datetime.now() + timedelta(minutes=5)

        quote = Quote(
            id=str(uuid.uuid4()),
            source_currency=source,
            target_currency=target,
            rate=rate,
            fees=fees,
            expiry=expiry
        )
        quotes[quote.id] = quote
        return quote

# Streamlit UI
st.title("Remittance App Prototype 💸")

# Simulate logged-in sender (in real app use session/auth)
sender_phone = st.sidebar.text_input("Your phone (for demo)", "+234123456789")
sender_id = "user123"  # fake

if sender_phone:
    # Fake create sender if not exists
    if sender_phone not in users:
        users[sender_phone] = User(
            id=sender_id,
            name="Denzel",
            phone=sender_phone,
            currencies={"USD": Currency("USD", 5000.0), "NGN": Currency("NGN", 5000000.0)}
        )

    receiver_phone = st.text_input("Receiver phone number")

    if receiver_phone:
        processor = PaymentProcessor()
        receiver_info = processor.resolve_receiver(receiver_phone)

        if not receiver_info:
            st.warning("Receiver not found. (Demo: use any phone — it will auto-create on confirm)")
            supported_currencies = ["USD", "EUR", "NGN"]
        else:
            st.success(f"Receiver: {receiver_info['user'].name}")
            supported_currencies = receiver_info["currencies"]

        col1, col2 = st.columns(2)
        source_currency = col1.selectbox("Send in", ["USD", "EUR", "NGN"])
        target_currency = col2.selectbox("Receive in", supported_currencies)

        amount_sent = st.number_input("Amount to send", min_value=1.0, max_value=10000.0, step=10.0)

        if st.button("Get Quote") and amount_sent > 0:
            quote = processor.create_quote(source_currency, target_currency, amount_sent)
            amount_received = round(amount_sent * quote.rate - quote.fees, 2)

            st.subheader("Quote (locked for 5 min)")
            st.metric("Rate", f"1 {source_currency} = {quote.rate:.4f} {target_currency}")
            st.metric("You send", f"{amount_sent:,.2f} {source_currency}")
            st.metric("Receiver gets", f"{amount_received:,.2f} {target_currency}")
            st.caption(f"Fees: {quote.fees:,.2f} | Expires: {quote.expiry.strftime('%H:%M:%S')}")
            st.session_state["current_quote"] = quote
            st.session_state["amount_received"] = amount_received

        if "current_quote" in st.session_state:
            if st.button("Confirm & Send"):
                quote = st.session_state["current_quote"]
                tx = Transaction(
                    id=str(uuid.uuid4()),
                    sender_id=sender_id,
                    receiver_id=receiver_phone,  # simplified
                    amount_sent=amount_sent,
                    currency_sent=source_currency,
                    amount_received=st.session_state["amount_received"],
                    currency_received=target_currency,
                    quote_id=quote.id,
                    status="Settled"  # fake success
                )
                st.success(f"Transaction successful! ID: {tx.id}")
                st.json(tx)  # show details
                # In real app: deduct balance, credit receiver, call payment API
                del st.session_state["current_quote"]  # clear
