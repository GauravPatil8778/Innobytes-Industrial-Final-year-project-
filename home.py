import requests
import streamlit as st


def app():
    API_URL = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 60,
        "page": 1,
        "sparkline": False,
    }

    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
    else:
        data = []

    css = """
    .title {
        font-family: "Arial", sans-serif;
        color: #E0F0E3; /* Change color to your preference */
    }
    """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.markdown('<h1 class="title">Cryptocurrency Coins</h1>', unsafe_allow_html=True)
    st.markdown("Price values are in USD.")

    for coin in data:
        # Add HTML/CSS styling to decrease image size
        coin_info = f'<img src="{coin["image"]}" style="width: 50px; height: 50px; object-fit: cover; margin-right: ' \
                    f'10px;" />'
        coin_info += f'<span style="color: ##fffff;">{coin["name"]} ({coin["symbol"].upper()})  </span>   '
        coin_info += f'<span style="color: #00FF00;">   Price: ${coin["current_price"]}</span>   '
        coin_info += f'<span style="color: #0075d3;">   Market Cap: {coin["market_cap"]}</span>   '
        coin_info += f'<span style="color: #ef0303;">   24h Change: {coin["price_change_percentage_24h"]}%</span>'
        st.markdown(coin_info, unsafe_allow_html=True)

        # coin_id = coin["id"]
        # fig = go.Figure(go.Scatter(x=[1, 2, 3, 4, 5], y=[10, 12, 8, 16, 14], line=dict(color='blue')))
        # fig.update_xaxes(showline=False, showticklabels=False, zeroline=False, showgrid=False)
        # fig.update_yaxes(showline=False, showticklabels=False, zeroline=False, showgrid=False)
        # fig.update_layout(height=250, width=100)  # Adjust the height and width as needed
        # st.plotly_chart(fig)

        st.markdown('---')
