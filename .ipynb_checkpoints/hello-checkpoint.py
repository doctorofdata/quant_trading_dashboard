# Import libraries
import streamlit as st
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd
import datetime
import numpy as np
import time
from millify import millify

st.set_page_config(layout = 'wide')

# Load the data
@st.cache_data
def load_snp_data():
        
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        
    return table[0]

@st.cache_data
def load_stock_prices():

    return pd.read_csv('snp500prices.csv')  

# Use a function to define the landing page for the site
def landing():
    
    # Top banner
    st.image('finance_banner.jpg', use_container_width = True)
    st.write("# Welcome to the Trader's Cove! 👋")
    st.sidebar.success("Select a page to navigate.")

    st.markdown("""
                      This site is a simulation page for backtesting the performance of automated trade strategies w/ user preferences!
                      Please use the sidebar on the left to navigate through the components
                """)
# Function top define the page where the user can create a portfolio
def portfolio():

    st.session_state.portfolio_submission = False

    c0 = st.container()
    c1 = st.container()
    c2 = st.container()
        
    # Define the intiial contents
    c0.image('finance_banner.jpg', use_container_width = True)

    c0.markdown(f"# {list(page_names_to_funcs.keys())[1]}")
    c0.markdown('Shown below is information regarding all members of the S&P 500, and related information..')
    c0.markdown('*Please review this data to select a portfolio for trading*')

    stocks = load_snp_data()
    c0.dataframe(stocks)

    # Isolate tickers into blocks
    c1.markdown('## Ticker Options- ')
    options = stocks.groupby('GICS Sector')['Symbol'].unique()
    
    with c1.form('portfolio_creation'):

        user_portfolio = []

        # Add items to each column
        for i, item in enumerate(options.index):

            # Get options
            opts = [i for i in options[item]]
    
            choices = st.pills(item, opts, selection_mode = "multi", label_visibility = "visible")

            for i in choices:
            
                user_portfolio.append(i)
                
        portfolio_submission = st.form_submit_button('Click here to initialize the portfolio with your chosen stocks!')
        
    if portfolio_submission:

        st.session_state.portfolio_submission = True
        st.session_state['portfolio'] = user_portfolio

        c2.write(f"### Chosen Portfolio Includes: ")
        c2.write(f"{[i for i in user_portfolio]}")

    else:

        c2.warning('Portfolio uninitialized, backtesting will use the entire S&P')
    
        
def parameters():

    st.image('stocktrading.jpg', use_container_width = True)

    st.session_state.df = load_stock_prices()
    
    symbols = [i for i in st.session_state.df['ticker'].unique()]

    if st.session_state.portfolio_submission == True:
        
        user_portfolio = [i for i in st.session_state['portfolio']]
    
    else:
        
        user_portfolio = symbols
        st.session_state['portfolio'] = user_portfolio
        
    st.markdown(f"# {list(page_names_to_funcs.keys())[2]} - Moving Averages")

    # Short explanation of trading strategy
    c = st.container()
    c0, c1 = c.columns(2)

    c0.markdown('''
                    - The idea behind this approach is that traders can capitalise on sustained price movements by identifying and following trends using moving averages.

                    - Traders can choose between multiple time frames, also known as the “look-back” periods, and can range from a few hours to several months. Shorter timeframes may make the moving average indicator more sensitive to price 
                      movements, while longer time frames may provide a smoother indication of the underlying trend.
                ''')

    c1.image('trading.png')
    c1.markdown('---')
    
    c0.markdown(f"---\n# Your Portfolio:\n {[i for i in user_portfolio]}")
    st.markdown('---')
    st.markdown('# Backtesting Your Selections: ')

    # Initialize the parameters for trading
    with st.form('backtesting_submission'):

        header = st.columns(4)
        header[2].subheader('Start Date- ')

        start = header[2].date_input('Choose a start date for backtesting', datetime.date(2020, 1, 1))
        
        header[2].subheader('End Date- ')

        end = header[2].date_input('Choose an end date', 'today')

        startingcash = header[0].number_input('Initialize a $ amount attribution for each stock', 10000)
        numshares = header[0].number_input('Initialize a # of shares to start with for each stock', 100)
        shortwindow = header[1].slider('Size of Short Window- ', 0, 180, 30)
        longwindow = header[1].slider('Size of Long Window- ', 90, 270, 90)
        
        store_parameters = header[3].form_submit_button('Store the chosen parameters..')

    if store_parameters:

        st.session_state.start = start
        st.session_state.end = end
        st.session_state.startingcash = startingcash
        st.session_state.numshares = numshares
        st.session_state.shortwindow = shortwindow
        st.session_state.longwindow = longwindow
    
def backtesting():

    st.image('stocktrading.jpg', use_container_width = True)
    st.markdown(f"# {list(page_names_to_funcs.keys())[3]}")

    c0, c1 = st.columns([.2, .8])

    # Pull parameters from memory
    start = pd.to_datetime(st.session_state.start)
    end = pd.to_datetime(st.session_state.end)
    userportfolio = st.session_state.portfolio
    startingcash = st.session_state.startingcash
    numshares = st.session_state.numshares
    
    df = st.session_state.df
    df['Date'] = pd.to_datetime(df['Date'])

    shortwindow = st.session_state.shortwindow
    longwindow = st.session_state.longwindow
    
    # Init df to store aggregate
    backtest = pd.DataFrame()
    signals = pd.DataFrame()

    @st.cache_data
    def generate_signals(ticker):

        # Get the data isolate
        grp = df[df['ticker'] == ticker]
        
        # Calculate
        grp['signal'] = 0.0

        # Calculate sma
        grp['short'] = grp['price'].rolling(window = shortwindow, min_periods = 1, center = False).mean()

        # Calculate lma
        grp['long'] = grp['price'].rolling(window = longwindow, min_periods = 1, center = False).mean()

        # Create signals
        grp['signal'][shortwindow:] = np.where(grp['short'][shortwindow:] > grp['long'][shortwindow:], 1.0, 0.0)

        # Generate trading orders
        grp['positions'] = grp['signal'].diff()

        grp.index = pd.DatetimeIndex(grp['Date'])
    
        return grp
    
    # Button to store statefulness
    execute_backtesting = c0.button("Execute backtesting!", type = "primary", icon = '📈')

    if execute_backtesting:
        
        # Iterate the stock symbols to calculate trade signals
        for nm in userportfolio:

            signals = pd.concat([signals, generate_signals(nm)])

        signals = signals.set_index('Date')

        # Iterate the trades to calculate earnings
        for nm, grp in signals.groupby('ticker'):

            pos = pd.DataFrame(index = grp.index).fillna(0)

            # Trigger to purchase specificed shares of each stock
            pos['shares'] = numshares * grp['signal']

            portfolio = pos.multiply(grp['price'], axis = 0)
            pos_diff = pos.diff()

            # Add `holdings` to portfolio
            portfolio['holdings'] = (pos.multiply(grp['price'], axis = 0)).sum(axis = 1)

            # Add `cash` to portfolio
            portfolio['cash'] = startingcash - (pos_diff.multiply(grp['price'], axis = 0)).sum(axis = 1).cumsum()   

            # Add `total` to portfolio
            portfolio['total'] = portfolio['cash'] + portfolio['holdings']

            # Add `returns` to portfolio
            portfolio['returns'] = portfolio['total'].pct_change() 
    
            portfolio['ticker'] = nm
    
            backtest = pd.concat([backtest, portfolio])

            if 'backtest' not in st.session_state:

                st.session_state['backtest'] = backtest

    c0.info(f'Backtesting is complete!')
        
    # Compile the performance from all stocks
    performance = backtest.groupby(backtest.index).agg({'holdings': 'sum',
                                                            'cash': 'sum',
                                                            'total': 'sum'})
    st.session_state.performance = performance
    st.session_state.endingcash = performance['total'].iloc[-1]
    
    # Compile the performance result
    stats1, stats2, stats3 = c1.columns(3)

    # Compute the returns
    delta = st.session_state.endingcash / (startingcash * len(userportfolio))
        
    stats1.metric('# of Stocks in Portfolio- ', len(userportfolio))
    stats2.metric('Total Investment:         ', f"${millify(startingcash * len(userportfolio))}")
    stats3.metric('Ending Balance:           ', f"${round(st.session_state.endingcash)}", delta = round(delta, 3)) 

    st.markdown(f'<p align="center">Aggregate Performance of Portfolio from: {str(start)[0:10]} :: {str(end)[0:10]}', unsafe_allow_html = True)

    st.line_chart(performance, y = 'total', y_label = 'Total ($)', x_label = 'Month')

# Define the layout for all pages
page_names_to_funcs = {"—": landing,
                       "Portfolio Selection": portfolio,
                       "Parameterization": parameters,
                       "Backtesting": backtesting,}
#                       "Outcomes": results,}
#                       "Visualizations": visuals}

demo_name = st.sidebar.selectbox("Choose a demo", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()