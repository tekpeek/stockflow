import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from signal_functions import calculate_bollinger_bands

class BollingerBandsBacktest:
    def __init__(self, symbol, start_date, end_date, window=20, num_std=2, initial_capital=100000):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.window = window
        self.num_std = num_std
        self.initial_capital = initial_capital
        self.positions = []
        self.capital = initial_capital
        self.shares = 0
        
    def fetch_data(self):
        """Fetch historical data for the symbol"""
        self.data = yf.download(self.symbol, start=self.start_date, end=self.end_date, interval='1d')
        if self.data.empty:
            raise ValueError(f"No data found for {self.symbol}")
        return self.data
    
    def calculate_signals(self):
        """Calculate Bollinger Bands and generate trading signals"""
        # Calculate Bollinger Bands
        self.data['middle_band'] = self.data['Close'].rolling(window=self.window).mean()
        self.data['std_dev'] = self.data['Close'].rolling(window=self.window).std()
        self.data['upper_band'] = self.data['middle_band'] + (self.data['std_dev'] * self.num_std)
        self.data['lower_band'] = self.data['middle_band'] - (self.data['std_dev'] * self.num_std)
        
        # Generate signals
        self.data['signal'] = 0
        self.data.loc[self.data['Close'] < self.data['lower_band'], 'signal'] = 1  # Buy signal
        self.data.loc[self.data['Close'] > self.data['upper_band'], 'signal'] = -1  # Sell signal
        
        # Remove NaN values
        self.data = self.data.dropna()
        
    def backtest(self):
        """Run the backtest"""
        self.fetch_data()
        self.calculate_signals()
        
        # Initialize portfolio tracking
        self.data['position'] = 0
        self.data['capital'] = self.initial_capital
        self.data['shares'] = 0
        self.data['portfolio_value'] = self.initial_capital
        
        current_position = 0
        
        for i in range(1, len(self.data)):
            # Get current price and signal
            current_price = self.data['Close'].iloc[i]
            current_signal = self.data['signal'].iloc[i]
            
            # Update position based on signal
            if current_signal == 1 and current_position == 0:  # Buy signal
                shares_to_buy = self.data['capital'].iloc[i-1] // current_price
                self.data.loc[self.data.index[i], 'shares'] = shares_to_buy
                self.data.loc[self.data.index[i], 'capital'] = self.data['capital'].iloc[i-1] - (shares_to_buy * current_price)
                current_position = 1
            elif current_signal == -1 and current_position == 1:  # Sell signal
                shares_to_sell = self.data['shares'].iloc[i-1]
                self.data.loc[self.data.index[i], 'shares'] = 0
                self.data.loc[self.data.index[i], 'capital'] = self.data['capital'].iloc[i-1] + (shares_to_sell * current_price)
                current_position = 0
            else:  # Hold position
                self.data.loc[self.data.index[i], 'shares'] = self.data['shares'].iloc[i-1]
                self.data.loc[self.data.index[i], 'capital'] = self.data['capital'].iloc[i-1]
            
            # Update portfolio value
            self.data.loc[self.data.index[i], 'portfolio_value'] = (
                self.data['capital'].iloc[i] + 
                (self.data['shares'].iloc[i] * current_price)
            )
            
            # Update position column
            self.data.loc[self.data.index[i], 'position'] = current_position
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        # Calculate returns
        self.data['returns'] = self.data['portfolio_value'].pct_change()
        
        # Calculate metrics
        total_return = (self.data['portfolio_value'].iloc[-1] - self.initial_capital) / self.initial_capital * 100
        annual_return = (1 + total_return/100) ** (252/len(self.data)) - 1
        sharpe_ratio = np.sqrt(252) * self.data['returns'].mean() / self.data['returns'].std()
        max_drawdown = (self.data['portfolio_value'] / self.data['portfolio_value'].cummax() - 1).min() * 100
        
        return {
            'Total Return (%)': round(total_return, 2),
            'Annual Return (%)': round(annual_return * 100, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Final Portfolio Value': round(self.data['portfolio_value'].iloc[-1], 2)
        }
    
    def plot_results(self):
        """Plot the backtest results"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
        
        # Plot price and Bollinger Bands
        ax1.plot(self.data.index, self.data['Close'], label='Price', color='blue')
        ax1.plot(self.data.index, self.data['upper_band'], label='Upper Band', color='red', linestyle='--')
        ax1.plot(self.data.index, self.data['middle_band'], label='Middle Band', color='green', linestyle='--')
        ax1.plot(self.data.index, self.data['lower_band'], label='Lower Band', color='red', linestyle='--')
        
        # Plot buy/sell signals
        buy_signals = self.data[self.data['signal'] == 1]
        sell_signals = self.data[self.data['signal'] == -1]
        ax1.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', label='Buy Signal')
        ax1.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', label='Sell Signal')
        
        ax1.set_title(f'Bollinger Bands Backtest - {self.symbol}')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True)
        
        # Plot portfolio value
        ax2.plot(self.data.index, self.data['portfolio_value'], label='Portfolio Value', color='purple')
        ax2.set_ylabel('Portfolio Value')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()

def main():
    # Example usage
    symbol = "RELIANCE.NS"  # Example stock
    start_date = "2023-01-01"
    end_date = "2024-01-01"
    
    # Create and run backtest
    backtest = BollingerBandsBacktest(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        window=20,
        num_std=2,
        initial_capital=100000
    )
    
    backtest.backtest()
    metrics = backtest.calculate_metrics()
    
    # Print results
    print("\nBacktest Results:")
    print("-" * 50)
    for metric, value in metrics.items():
        print(f"{metric}: {value}")
    
    # Plot results
    backtest.plot_results()

if __name__ == "__main__":
    main() 