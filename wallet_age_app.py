import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="EVM Wallet Age Checker", layout="wide")
st.title("📊 EVM Wallet Age Checker")

st.markdown("Upload a CSV with wallet addresses and chains (ethereum, polygon, bsc).")

# Supported chains
API_KEYS = st.secrets["API_KEYS"]

BASE_URLS = {
    "ethereum": "https://api.etherscan.io/api",
    "polygon": "https://api.polygonscan.com/api",
    "bsc": "https://api.bscscan.com/api"
}

def get_wallet_age(chain, wallet_address):
    base_url = BASE_URLS.get(chain)
    api_key = API_KEYS.get(chain)

    if not base_url or not api_key:
        return None, f"Unsupported or missing API key for chain: {chain}"

    url = (
        f"{base_url}?module=account&action=txlist&address={wallet_address}"
        f"&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    )
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except Exception as e:
        return None, f"Error: {str(e)}"

    if data["status"] != "1" or not data["result"]:
        return None, "No transactions or invalid wallet."

    first_tx = data["result"][0]
    timestamp = int(first_tx["timeStamp"])
    created_date = datetime.utcfromtimestamp(timestamp)
    age_days = (datetime.utcnow() - created_date).days
    return {
        "first_transaction": created_date.strftime("%Y-%m-%d"),
        "wallet_age_days": age_days
    }, None

def process_uploaded_csv(df):
    results = []

    for _, row in df.iterrows():
        wallet = row["wallet_address"]
        chain = row["chain"].lower()

        result, error = get_wallet_age(chain, wallet)
        if error:
            results.append({
                "wallet_address": wallet,
                "chain": chain,
                "first_transaction": None,
                "wallet_age_days": None,
                "error": error
            })
        else:
            results.append({
                "wallet_address": wallet,
                "chain": chain,
                "first_transaction": result["first_transaction"],
                "wallet_age_days": result["wallet_age_days"],
                "error": None
            })

    return pd.DataFrame(results)

uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

if uploaded_file:
    input_df = pd.read_csv(uploaded_file)

    if "wallet_address" not in input_df.columns or "chain" not in input_df.columns:
        st.error("CSV must contain 'wallet_address' and 'chain' columns.")
    else:
        st.info("Processing wallet ages...")
        result_df = process_uploaded_csv(input_df)

        st.success("Done!")
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="wallet_ages_output.csv",
            mime="text/csv"
        )
