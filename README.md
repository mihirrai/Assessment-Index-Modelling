# Libraries Used
1. Pandas (1.4.2)
2. NumPy (1.22.3)

# White Board Algorithm
- Business rules are initialized w.r.t to business days, holidays, start date and weights
- Index level initialized at starting value of 100
- Initialize top stock tickers 
- Error check for valid start and end dates of back-testing input
- Loop over the valid business days
	- Calculate the cumulative returns
	- Set index level of date (level = level on re-balance date * sum-product of weights and cumulative returns)
	- If current date is the first business day of the month (re-balance date):
		- Update top stock tickers by prices on previous month's last business day
		- Reset cumulative returns
		- Update index level on re-balance date
- Filter the results by start date of back-testing
- Export to CSV

# Setup
Python 3.10

PyCharm 2021.3.3 CE
