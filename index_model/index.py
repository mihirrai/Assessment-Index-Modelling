import datetime as dt

import numpy as np
import pandas as pd
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.offsets import CustomBusinessMonthBegin
from pandas.tseries.offsets import CustomBusinessMonthEnd


class IndexModel:
    def __init__(self) -> None:
        # Initialize business rule values
        self.index_business_days = 'Mon Tue Wed Thu Fri'
        self.holidays = []
        self.top_stock_tickers = []
        self.weights = [0.5, 0.25, 0.25]
        self.index_start_date = dt.date(year=2020, month=1, day=1)

        # Read historical stock prices
        self.stock_prices_df = pd.read_csv("./data_sources/stock_prices.csv")
        self.stock_prices_df['Date'] = pd.to_datetime(self.stock_prices_df.Date, format='%d/%m/%Y')
        self.stock_prices_df.set_index('Date', inplace=True)
        self.index_end_date = self.stock_prices_df.index[-1]

        # Setup index level values DataFrame
        self.index_values_df = pd.DataFrame(
            index=pd.bdate_range(start=self.index_start_date, end=self.index_end_date,
                                 weekmask=self.index_business_days,
                                 freq='C',
                                 holidays=self.holidays), columns=['index_level'])

        # Initialize the index level
        self.index_values_df.at[pd.to_datetime(self.index_start_date), 'index_level'] = 100

        # Initialize top_stock_tickers
        self._update_tickers(self.index_values_df.index[0])

    def _get_previous_business_day(self, date: dt.date) -> dt:
        return date - CustomBusinessDay(weekmask=self.index_business_days, holidays=self.holidays)

    def _get_previous_month_last_business_day(self, date: dt.date) -> dt:
        offset = CustomBusinessMonthEnd(n=1, weekmask=self.index_business_days, holidays=self.holidays)
        return offset.rollback(date)

    def _get_first_business_day_month(self, date: dt.date) -> dt:
        offset = CustomBusinessMonthBegin(n=1, weekmask=self.index_business_days, holidays=self.holidays)
        return offset.rollback(date)

    # Updates top_stock_tickers to previous month last business day's 3 highest stock tickers by price
    def _update_tickers(self, date: dt.date):
        previous_month_last_business_day = self._get_previous_month_last_business_day(date)
        previous_month_end_prices = self.stock_prices_df.loc[pd.to_datetime(previous_month_last_business_day)]
        self.top_stock_tickers = previous_month_end_prices.sort_values(ascending=False)[:3].index.values.tolist()

    def calc_index_level(self, start_date: dt.date, end_date: dt.date) -> None:
        # Throw error if end date is greater than end date
        if start_date > end_date:
            raise ValueError("Start date cannot be greater than end date")
        # Throw error if start or end date don't fit the historical date range from stock_prices.csv
        if (pd.to_datetime(start_date) > self.index_end_date) or \
                (pd.to_datetime(end_date) > self.index_end_date) or end_date < self.index_start_date:
            raise ValueError("Not enough historical stock data")

        # Initialize cumulative returns (in this case monthly) and index at rebalance date
        cumulative_returns = [1, 1, 1]
        index_at_rebalance_date = self.index_values_df.index_level.dropna()[-1]

        # Loop over valid business days except index start date as we already have that value (100)
        for date in filter(lambda x: x <= pd.to_datetime(end_date), self.index_values_df.index[1:]):
            previous_business_day = self._get_previous_business_day(date)

            # Get data for previous and current business day to get % change in prices and add 1 (change from 0.xxx to 1.xxx)
            pct_change_df = self.stock_prices_df[pd.to_datetime(previous_business_day): pd.to_datetime(date)][
                                self.top_stock_tickers].pct_change().dropna() + 1
            pct_change = pct_change_df.values.flatten().tolist()

            # Update cumulative returns
            cumulative_returns = np.multiply(cumulative_returns, pct_change)

            # Index level = Index at rebalance * Sumproduct of weights and cumulative returns
            index_level = np.dot(cumulative_returns, self.weights) * index_at_rebalance_date
            self.index_values_df.at[date, 'index_level'] = index_level

            if date == self._get_first_business_day_month(date):
                # Update top stocks based on previous months last business day
                self._update_tickers(date)
                # Reset cumulative returns since we updated top stocks
                cumulative_returns = [1, 1, 1]
                # Update Index at rebalance to current index level
                index_at_rebalance_date = index_level

        # Filter index level results by start date
        self.index_values_df = self.index_values_df.loc[self.index_values_df.index >= pd.to_datetime(start_date)]

    # Exporting index level values (no float formatting to provide the highest level of precision)
    def export_values(self, file_name: str) -> None:
        self.index_values_df.index = self.index_values_df.index.strftime('%d/%m/%Y')
        self.index_values_df.dropna(inplace=True)
        self.index_values_df.to_csv(f'{file_name}', index_label='Date')
