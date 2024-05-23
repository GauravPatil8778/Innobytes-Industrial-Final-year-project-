import streamlit as st
import pandas as pd
import numpy as np
from pandas_datareader import data as pdr
import yfinance as yf
import plotly.express as px
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import ruptures as rpt

# Initialize Yahoo Finance
yf.pdr_override()

# Define the LSTM model using PyTorch
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size, dropout_rate=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout_rate)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

# Define the app
def app():
    st.title("Cryptocurrency Forecasting")
    crypto_symbol = st.text_input("Enter a cryptocurrency symbol (e.g., BTC, ETH):")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    if crypto_symbol and start_date and end_date:
        try:
            crypto_data = pdr.get_data_yahoo(f"{crypto_symbol}-USD", start=start_date, end=end_date)

            if not crypto_data.empty:
                # Table data
                st.write("Cryptocurrency Historical Data:")
                st.write(crypto_data[['High', 'Low', 'Open', 'Close', 'Volume']])

                # 1st Graph
                st.subheader("Closing Price vs Time")
                fig = px.line(crypto_data, x=crypto_data.index, y='Close', title=f"{crypto_symbol} Closing Price Over Time")
                fig.update_traces(line=dict(color='green'))
                fig.update_layout(plot_bgcolor='black')
                fig.update_layout(paper_bgcolor='black')
                fig.update_layout(font_color='white')
                st.plotly_chart(fig)

                # 2nd Graph - 100-day and 200-day moving averages
                st.subheader("100-day and 200-day moving averages")
                crypto_data['100MA'] = crypto_data['Close'].rolling(window=100).mean()
                crypto_data['200MA'] = crypto_data['Close'].rolling(window=200).mean()

                fig_ma = px.line(crypto_data, x=crypto_data.index, y=['100MA', '200MA'],
                                 title=f"{crypto_symbol} Moving Averages Over Time")
                fig_ma.update_traces(line=dict(color='green'), selector=dict(name='100MA'))
                fig_ma.update_traces(line=dict(color='blue'), selector=dict(name='200MA'))
                fig_ma.update_layout(plot_bgcolor='black')
                fig_ma.update_layout(paper_bgcolor='black')
                fig_ma.update_layout(font_color='white')
                fig_ma.update_xaxes(title_text='Date', showgrid=True, gridcolor='gray')
                fig_ma.update_yaxes(title_text='Moving Average', showgrid=True, gridcolor='gray')
                st.plotly_chart(fig_ma)

                # Prepare data for LSTM
                # Check shapes of X and y
                print("X shape:", X.shape)
                print("y shape:", y.shape)
                X = crypto_data[['High', 'Low', 'Open', 'Volume']]
                y = crypto_data['Close']
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                # Use a single MinMaxScaler instance for both training and testing data
                scaler_X = MinMaxScaler()
                scaler_y = MinMaxScaler()
                X_scaled = scaler_X.fit_transform(X)
                y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1))

                X_train = torch.FloatTensor(X_scaled[:-365]).view(-1, 1, 4)  # Exclude last 365 days for training
                y_train = torch.FloatTensor(y_scaled[:-365])
                X_test = torch.FloatTensor(X_scaled[-365:]).view(-1, 1, 4)  # Use last 365 days for testing
                
                # Check shapes after splitting
                print("X_train shape:", X_train.shape)
                print("y_train shape:", y_train.shape)
                print("X_test shape:", X_test.shape)
                # LSTM Model
                model = LSTMModel(input_size=4, hidden_size=128, num_layers=3, output_size=1, dropout_rate=0.2)
                criterion = nn.MSELoss()
                optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

                # Training the model with early stopping
                best_loss = float('inf')
                patience = 5
                early_stop_counter = 0

                for epoch in range(100):
                    outputs = model(X_train)
                    optimizer.zero_grad()
                    loss = criterion(outputs, y_train)
                    loss.backward()
                    optimizer.step()

                    # Early stopping
                    if loss.item() < best_loss:
                        best_loss = loss.item()
                        early_stop_counter = 0
                    else:
                        early_stop_counter += 1
                        if early_stop_counter >= patience:
                            break

                # Evaluate the model on the test set
                model.eval()
                with torch.no_grad():
                    test_outputs = model(X_test)
                    test_loss = criterion(test_outputs.view(-1)[-365:],
                                          torch.FloatTensor(y_test.values[-365:]).view(-1))

                    print(f'Test Loss: {test_loss.item()}')

                # Make predictions for the next year
                model.eval()
                with torch.no_grad():
                    future_X = torch.FloatTensor(X_scaled[-365:]).view(-1, 1, 4)  # Use the last 365 days to predict the future
                    predicted_y = []
                    for _ in range(365):  # Predicting for the next 365 days (1 year)
                        future_y = model(future_X)
                        future_X = torch.cat((future_X[:, :, 1:], future_y.view(-1, 1, 1)), dim=2)
                        predicted_y.append(future_y.item())
                    predicted_y = scaler_y.inverse_transform(np.array(predicted_y).reshape(-1, 1))

                # Visualize the LSTM prediction
                st.subheader("Prediction")
                fig_pred = px.line(x=pd.date_range(start=end_date, periods=365, freq='D'), y=predicted_y.flatten(),
                                   title=f"{crypto_symbol} Predicted Closing Price for the Next Year")
                fig_pred.update_traces(line=dict(color='green'))
                fig_pred.update_layout(plot_bgcolor='black')
                fig_pred.update_layout(paper_bgcolor='black')
                fig_pred.update_layout(font_color='white')
                fig_pred.update_xaxes(title_text='Date', showgrid=True, gridcolor='gray')
                fig_pred.update_yaxes(title_text='Predicted Price', showgrid=True, gridcolor='gray')
                st.plotly_chart(fig_pred)

                # PELT Change Point Detection
                crypto_close = crypto_data[['Close']]
                model = "l1"
                algo = rpt.Pelt(model=model).fit(crypto_close)
                result = algo.predict(pen=1.5)  # You can adjust the penalty value

                # Visualize Change Points
                st.subheader("Change Points Detection with PELT")
                plt.figure(figsize=(10, 6))
                plt.plot(crypto_data.index, crypto_close, label="Actual Data", color='blue')
                plt.plot(crypto_data.index[result], crypto_close.iloc[result], 'ro', markersize=8, label="Change Points", color='red')
                plt.title(f"{crypto_symbol} Price with PELT Change Points")
                plt.xlabel("Date")
                plt.ylabel("Price")
                plt.legend()
                st.pyplot(plt)

            else:
                st.write("No data available for " + crypto_symbol + " between " + str(start_date) + " and " + str(end_date))
        except Exception as e:
            st.write("Error: " + str(e))
    else:
        st.write("Please enter a cryptocurrency symbol, start date, and end date.")

if __name__ == '__main__':
    app()
