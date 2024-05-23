import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
import numpy as np

# Define the LSTM model using PyTorch
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

# Function to fetch commodity data from Alpha Vantage
def fetch_commodity_data(symbol):
    api_key = "ZZA6ZQYAZKJFSIPK"
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    if "Time Series (Daily)" in data:
        # Convert data to DataFrame
        commodity_data = pd.DataFrame(data["Time Series (Daily)"]).T
        commodity_data.index = pd.to_datetime(commodity_data.index)
        # Reverse the DataFrame to have the latest date first
        commodity_data = commodity_data[::-1]
        return commodity_data
    else:
        return None

# Function to train LSTM model and make predictions
def train_and_predict_lstm(data):
    # Prepare data
    scaler = MinMaxScaler(feature_range=(-1, 1))
    scaled_data = scaler.fit_transform(data[['4. close']].values)
    sequence_length = 10
    x, y = [], []
    for i in range(len(scaled_data) - sequence_length):
        x.append(scaled_data[i:i+sequence_length])
        y.append(scaled_data[i+sequence_length])
    x_train, y_train = torch.tensor(x), torch.tensor(y)
    
    # Define and train LSTM model
    model = LSTMModel(input_size=1, hidden_size=50, num_layers=2, output_size=1)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    num_epochs = 100
    for epoch in range(num_epochs):
        outputs = model(x_train.float())
        optimizer.zero_grad()
        loss = criterion(outputs, y_train.float())
        loss.backward()
        optimizer.step()
    
    # Make predictions
    model.eval()
    with torch.no_grad():
        test_seq = x[-1].reshape(-1, sequence_length, 1)
        predicted_prices = []
        for _ in range(len(data)):
            test_seq = torch.tensor(test_seq).float()
            predicted_price = model(test_seq)
            predicted_prices.append(predicted_price.item())
            test_seq = torch.cat((test_seq[:, 1:, :], predicted_price.unsqueeze(0)), dim=1)
    
    # Inverse scale the predicted prices
    predicted_prices = scaler.inverse_transform(np.array(predicted_prices).reshape(-1, 1)).flatten()
    
    return predicted_prices

# Define the app
def app():
    st.title("Commodity Price Prediction")
    
    # Dictionary to map commodities to their respective symbols
    commodity_symbols = {
        "Crude Oil (Brent)": "BNO",
        "Crude Oil (WTI)": "OIL",
        "Natural Gas": "NG",
        "Gold": "XAUUSD",
        "Silver": "XAGUSD",
        "Copper": "HG",
        "Corn": "C",
        "Wheat": "W",
        "Soybeans": "S",
        "Coffee": "KC",
        "Cotton": "CT"
    }
    
    # Updated commodity selection
    commodity_symbol = st.selectbox("Select a commodity", list(commodity_symbols.keys()))

    if commodity_symbol:
        symbol = commodity_symbols[commodity_symbol]
        commodity_data = fetch_commodity_data(symbol)
        if commodity_data is not None:
            st.subheader(f"{commodity_symbol} Historical Data")
            st.write(commodity_data[['2. high', '3. low', '1. open', '4. close', '5. volume']])

            st.subheader(f"{commodity_symbol} Closing Price vs Time")
            fig = px.line(commodity_data, x=commodity_data.index, y='4. close', title=f"{commodity_symbol} Closing Price Over Time")
            st.plotly_chart(fig)

            st.subheader("LSTM Price Prediction")
            predicted_prices = train_and_predict_lstm(commodity_data)
            predicted_dates = pd.date_range(start=commodity_data.index[-1] + pd.Timedelta(days=1), periods=len(predicted_prices))
            predicted_df = pd.DataFrame({'Date': predicted_dates, 'Predicted Price': predicted_prices})
            st.write("Predicted Prices:")
            st.write(predicted_df.set_index('Date'))

            st.subheader("Actual vs Predicted Prices")
            actual_prices = commodity_data['4. close'][-len(predicted_prices):]
            comparison_df = pd.DataFrame({'Date': predicted_dates[:len(actual_prices)],
                                          'Actual Price': actual_prices.values,
                                          'Predicted Price': predicted_prices[:len(actual_prices)]})
            
            # Data type conversions
            comparison_df['Date'] = pd.to_datetime(comparison_df['Date'])
            comparison_df['Actual Price'] = pd.to_numeric(comparison_df['Actual Price'])
            comparison_df['Predicted Price'] = pd.to_numeric(comparison_df['Predicted Price'])
            
            # Plotting
            fig = px.line(comparison_df, x='Date', y=['Actual Price', 'Predicted Price'], 
                          title="Actual vs Predicted Prices",
                          color_discrete_map={'Actual Price': 'blue', 'Predicted Price': 'red'},
                          line_dash_sequence=['solid', 'dash'])
            
            # Add markers for actual prices
            fig.update_traces(mode='lines+markers', marker=dict(size=5))
            
            # Smooth the predicted line using rolling mean
            window_size = 7
            comparison_df['Smoothed Predicted Price'] = comparison_df['Predicted Price'].rolling(window=window_size).mean()
            
            # Plotting
            fig.add_scatter(x=comparison_df['Date'], y=comparison_df['Smoothed Predicted Price'], 
                            mode='lines', line=dict(color='red', width=2), 
                            name='Smoothed Predicted Price')
            
            # Update layout for better readability
            fig.update_layout(xaxis_title="Date", yaxis_title="Price", legend_title="Legend")
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            # Display MAE on the graph
            mae = np.mean(np.abs(comparison_df['Actual Price'] - comparison_df['Predicted Price']))
            fig.add_annotation(text=f"MAE: {mae:.2f}", x=comparison_df['Date'].iloc[-1], 
                               y=comparison_df['Actual Price'].max(), showarrow=False)

            st.plotly_chart(fig)
        else:
            st.write(f"No data available for {commodity_symbol}.")
    else:
        st.write("Please select a commodity.")

if __name__ == '__main__':
    app()
