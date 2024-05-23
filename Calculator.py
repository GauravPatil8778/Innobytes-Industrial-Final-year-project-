import streamlit as st
import requests

# Function to fetch exchange rates
def fetch_exchange_rate(api_key, base_currency, target_currency="INR"):
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{base_currency}/{target_currency}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("conversion_rate", None)
        else:
            st.warning(f"Failed to fetch exchange rate. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"An error occurred while fetching exchange rate: {str(e)}")
        return None

# Function to convert commodity price to INR
def convert_price(price, exchange_rate, conversion_factor=1.0):
    return price * exchange_rate * conversion_factor

# Function to display the converter
def display_converter(api_key):
    st.title("Commodity Price Converter to INR")

    # List of commodities and their respective currencies and conversion factors
    commodities = {
        "Gold (Troy Ounce)": {"currency": "USD", "conversion_factor": 1.0},  # Price per troy ounce
        "Silver (Troy Ounce)": {"currency": "USD", "conversion_factor": 1.0},  # Price per troy ounce
        "Wheat (Bushel)": {"currency": "USD", "conversion_factor": 1.0},  # Price per bushel
        "Corn (Bushel)": {"currency": "USD", "conversion_factor": 1.0},  # Price per bushel
        "Natural Gas (MMBtu)": {"currency": "USD", "conversion_factor": 1.0}  # Price per MMBtu
    }

    # User selects commodity and enters price
    commodity = st.selectbox("Select Commodity", list(commodities.keys()))
    price = st.number_input(f"Enter {commodity} Price in {commodities[commodity]['currency']}:", min_value=0.0, format="%.2f")

    # Fetch and display conversion rate and converted price
    if st.button("Convert to INR"):
        exchange_rate = fetch_exchange_rate(api_key, commodities[commodity]["currency"])
        if exchange_rate:
            inr_price = convert_price(price, exchange_rate, commodities[commodity]["conversion_factor"])
            st.write(f"The price of {commodity} in INR is: ₹{inr_price:.2f}")

def app():
    # API Key for Exchange Rate API
    api_key = "06789e22063b908cc6293ee1"  # Replace with your actual API key

    display_converter(api_key)

if __name__ == "__main__":
    app()
