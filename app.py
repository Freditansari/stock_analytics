from flask import Flask, render_template
import random
from bokeh.models import (HoverTool, FactorRange, Plot, LinearAxis, Grid,
                          Range1d)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure, output_file, show, save, ColumnDataSource
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
import yfinance as yf
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import os

app = Flask(__name__)


def create_cummulative_chart(stock, stock_ticker):
    p = figure(
        x_axis_type="datetime",
        width=1200,
        height=800,
        tools="pan,box_zoom,reset,save,hover",
        x_axis_label='date',
        y_axis_label="gains",

    )

    p.title = stock_ticker + " cumulative gains"

    gain_df = stock.tail(600)
    p.line(x="Date", y="cum_gain", source=gain_df)
    # p.line(x="Date", y = "ema", source = gain_df.tail(90), color='red')

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [("date", "@Date{%F}"),
                      ("Gains", "@gains{0,0.00 %}")]
    hover.formatters = {"@Date": 'datetime'}
    return p


def create_monthly_chart(stock, stock_ticker):
    logic = {'Open': 'first',
             'High': 'max',
             'Low': 'min',
             'Close': 'last',
             'Volume': 'sum'}

    offset = pd.DateOffset(days=-30)
    monthly_stock = stock.resample('M', loffset=offset).apply(logic)
    monthly_stock['gains'] = monthly_stock['Close'].pct_change()
    monthly_stock['cum_gain'] = monthly_stock['gains'].cumsum()
    monthly_stock['ema'] = monthly_stock['gains'].ewm(span=20, adjust=False).mean()
    y = figure(
        x_axis_type="datetime",
        width=1200,
        height=800,
        tools="pan,box_zoom,reset,save,hover",
        x_axis_label='date',
        y_axis_label="gains",

    )

    y.title = stock_ticker + " monthly gains"

    gain_df = monthly_stock.tail(48)
    y.line(x="Date", y="gains", source=gain_df)
    y.line(x="Date", y="ema", source=gain_df, color='red')

    hover = y.select(dict(type=HoverTool))
    hover.tooltips = [("date", "@Date{%F}"),
                      ("Gains", "@gains{0,0.00 %}")]
    hover.formatters = {"@Date": 'datetime'}

    return y


@app.route('/<string:ticker>')
def hello_world(ticker):  # put application's code here
    # start = datetime.datetime(2018,1,1)
    # end = datetime.datetime(2019,1,30)
    import datetime
    from datetime import timedelta

    stock_ticker = ticker

    end = datetime.datetime.now()
    start = datetime.datetime.now() - timedelta(365 * 5)

    stock = yf.download(stock_ticker, start, end)
    filtered_data = stock
    filtered_data['gains'] = filtered_data['Adj Close'].pct_change()
    filtered_data['cum_gain'] = filtered_data['gains'].cumsum()
    filtered_data['ema'] = filtered_data['gains'].ewm(span=20, adjust=False).mean()

    output_file('bokeh_chart.html')

    p = figure(
        x_axis_type="datetime",
        width=1200,
        height=800,
        tools="pan,box_zoom,reset,save,hover",
        x_axis_label='date',
        y_axis_label="gains",

    )

    p.title = stock_ticker + " daily gains"

    gain_df = filtered_data.tail(350)
    p.line(x="Date", y="gains", source=gain_df.tail(90))
    p.line(x="Date", y="ema", source=gain_df.tail(90), color='red')

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [("date", "@Date{%F}"),
                      ("Gains", "@gains{0,0.00 %}")]
    hover.formatters = {"@Date": 'datetime'}

    monthly_chart = create_monthly_chart(stock, stock_ticker)
    cummulative_chart = create_cummulative_chart(stock, stock_ticker)

    cummulative_script, cummulative_div = components(cummulative_chart)
    monthly_script, monthly_div = components(monthly_chart)

    # show(p)
    script, div = components(p)

    return render_template('chart.html', script=script, div=div, monthly_script=monthly_script, monthly_div=monthly_div,
                           cummulative_script=cummulative_script, cummulative_div=cummulative_div)


@app.route('/')
def banana():  # put application's code here
    return "Analytics chart"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
