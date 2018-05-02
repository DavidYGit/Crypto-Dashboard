import os
from subprocess import call
import sys
from datetime import datetime as dt
import time
import dash
import dash_core_components as dcc
import dash_html_components as html
import sqlite3
from dash.dependencies import Input, Output, State, Event
import plotly.plotly as py
from plotly.graph_objs import *
import numpy as np
from scipy.stats import rayleigh
from flask import Flask, send_from_directory

server = Flask('CryptoMAvgs')

app = dash.Dash('CryptoMAvgs-App', server=server,
                url_base_pathname='/dash/',
                csrf_protect=False)
app.config.supress_callback_exceptions=True


app.layout = html.Div([

    html.Div([
        html.H2("Crypto Prices in USD (" + str(dt.now().date()) + ")")
    ], className='banner'),

    html.Div([

    html.Div([
        html.P("Period"),
        dcc.Dropdown(id='period', options=[
                     {'label': i, 'value': i} for i in ['5', '10', '15']], value='5')
    ], style={'width': '31%', 'display': 'inline-block'}),

    html.Div([
        html.P("Box plot Period"),
        dcc.Dropdown(id='box_plot_period', options=[
                     {'label': i, 'value': i} for i in ['5', '10', '15']], value='5')
    ], style={'width': '31%', 'margin-left': '3%', 'display': 'inline-block'}),


    html.Div([
        html.P("Cryptocurrency"),
        dcc.Dropdown(id='crypto', options=[
                     {'label': i, 'value': i} for i in ['BTC', 'ETH', 'LTC']], value='BTC')
    ], style={'width': '31%', 'margin-left': '3%', 'display': 'inline-block'}),

    html.Div([
        html.P("Time frame"),
        dcc.Dropdown(id='timeframe', options=[
                     {'label': i, 'value': i} for i in ['1', '2', '3', '4']], value='2')
    ], style={'width': '31%', 'float': 'right', 'display': 'none'}),

    html.Div([
        dcc.Graph(id='bpi'),
        ], style={'width': '75%', 'vertical-align': 'middle'}, className='twelve columns bpi'),

    html.Div([
    	html.Label('Last Price'),
    	     html.Div(id='lastprice'),

        html.Label('Market Cap'),
    		html.Div(id='market'),

        html.Label('Accuracy of SMA'),
    		html.Div(id='accuracy'),

    	html.Label('Accuracy of EMA'),
    		html.Div(id='eaccuracy'),

    	html.Button('STOP',id='stop-button',n_clicks=0),

        html.Div(id='status'),

    	], style={'width': '20%', 'margin-top' : '5%', 'margin-left' : '5%', 'display': 'inline-block', 'vertical align' : 'middle'}),

    dcc.Interval(id='bpi-update', interval=12000)
    ], className='row bpi-row'),

    html.Div([
        html.Div([
            html.H3("Sentiment")
        ], className='Title'),

    html.Div([
        dcc.Graph(id='bpi1'),
        ], className='twelve columns bpi'),

    dcc.Interval(id='bpi-update', interval=12000)
    ], className='row bpi-row'),


], className='main-div')

@app.callback(Output('lastprice', 'children'),  [Input(component_id='crypto', component_property='value')],[],
              [Event('bpi-update', 'interval')])
def retrieve_lastprice(CC):
    conn = sqlite3.connect('DS.db')
    c = conn.cursor()
    sql_cmd = "SELECT * FROM price WHERE CC ='{}'".format(CC)
    c.execute(sql_cmd)
    #data = db.search(BPI.updatedTime > begin_time)
    data = c.fetchall()
    prices1=[]
    for i in range(len(data)):
        prices1.append(data[i][1])

    return '${:,.2f}'.format(prices1[-1])

@app.callback(Output('market', 'children'),
             [
              Input(component_id='crypto', component_property='value')
             ],
             [],
             [Event('bpi-update', 'interval')])

def retrieve_marketcap(CC):
    conn = sqlite3.connect('DS.db')
    c = conn.cursor()
    sql_cmd = "SELECT * FROM price WHERE CC ='{}'".format(CC)
    c.execute(sql_cmd)
    #data = db.search(BPI.updatedTime > begin_time)
    data = c.fetchall()
    marketcap=[]
    for i in range(len(data)):
        marketcap.append(data[i][2])

    return '${:,.2f}'.format(marketcap[-1])

@app.callback(Output(component_id='accuracy',component_property='children'),
    [
        Input(component_id='period', component_property='value'),
        Input(component_id='crypto', component_property='value')
    ],
    [],
    [Event('bpi-update', 'interval')])
def compute_SMAaccuracy(N,CC):
    conn = sqlite3.connect('DS.db')
    c = conn.cursor()
    sql_cmd = "SELECT * FROM price WHERE CC ='{}'".format(CC)
    c.execute(sql_cmd)
    #data = db.search(BPI.updatedTime > begin_time)
    data = c.fetchall()

    prices = []
    SMA = []
    dtime = []
    aSMA = 0
    acc = 0

    N = int(N)  # period
    CC = str(CC) # Crypto

    #get time difference
    for i in range(len(data)):

	prices.append(data[i][1])
        a = dt.strptime(data[i][3],'%Y-%m-%d %H:%M:%S')
    	dtime.append(str('{:02d}'.format(a.hour)) + ":" + str('{:02d}'.format(a.minute)) + ":" + str('{:02d}'.format(a.second)))

    plen = len(prices)

    if plen > N:

        SMA = [None for i in range(N - 1)]

        for i in xrange(0, plen - N + 1, 1):

            y = prices[i: i + N]
            sma = reduce(lambda x, y__: x + y__, y) / len(y)
            SMA.append(sma)

        if len(SMA) != 0:
            for i in xrange(0,N,1):
                acc = acc + abs((float)(y[len(y)-1] - SMA[len(SMA)-1])/(float)(y[len(y)-1]))

        aSMA = (1-((float)(acc) / (float)(N)))*100

    return '{:,.4f}%'.format((float)(aSMA))

@app.callback(Output(component_id='eaccuracy',component_property='children'),
    [
        Input(component_id='period', component_property='value'),
        Input(component_id='crypto', component_property='value')
    ],
    [],
    [Event('bpi-update', 'interval')])

def compute_EMAaccuracy(N,CC):
    conn = sqlite3.connect('DS.db')
    c = conn.cursor()
    sql_cmd = "SELECT * FROM price WHERE CC ='{}'".format(CC)
    c.execute(sql_cmd)
    #data = db.search(BPI.updatedTime > begin_time)
    data = c.fetchall()

    prices = []
    SMA = []
    dtime = []
    aEMA = 0
    eacc = 0

    N = int(N)  # period
    CC = str(CC) # Crypto

    #get time difference
    for i in range(len(data)):

	prices.append(data[i][1])
        a = dt.strptime(data[i][3],'%Y-%m-%d %H:%M:%S')
    	dtime.append(str('{:02d}'.format(a.hour)) + ":" + str('{:02d}'.format(a.minute)) + ":" + str('{:02d}'.format(a.second)))

    plen = len(prices)

    if plen > N:

        EMA = [None for i in range(N - 1)]

        y = prices[0:N]
        avg = reduce(lambda x, y_: x + y_, y) / len(y)
        EMA.append(avg)

        for i in xrange(N, plen, 1):

            new_ema = ((prices[i] - EMA[-1])
                       * 2.0 / (N + 1)) + EMA[-1]

            EMA.append(new_ema)

	k = prices[i : i+ N]
        if len(EMA) != 0:
            for i in xrange(0,N,1):
                eacc = eacc = eacc + abs((float)(k[len(k)-1] - EMA[len(EMA)-1])/(float)(k[len(k)-1]))

        aEMA = (1-((float)(eacc) / (float)(N)))*100

    return '{:,.4f}%'.format((float)(aEMA))

@app.callback(Output('status', 'children'),
    [Input('stop-button','n_clicks')],
    [],
    [],
)
def kill_all(n):
    if n > 0:
        conn = sqlite3.connect('DS.db')
        c = conn.cursor()

        #Create the tables first
        c.execute('''DROP TABLE Sentiment''')
        c.execute('''DROP TABLE Price''')
        conn.commit
        conn.close
	rc = call("./stop_server.sh")

@app.callback(
    Output(component_id='bpi', component_property='figure'),
    [
        Input(component_id='period', component_property='value'),
        Input(component_id='box_plot_period', component_property='value'),
        Input(component_id='timeframe', component_property='value'),
        Input(component_id='crypto', component_property='value')
    ],
    [],
    [Event('bpi-update', 'interval')]
)
def get_bpi(N, bN, T, CC):

    #T hour time frame

    T = int(T)
    curr_time = time.time()
    begin_time = curr_time - T * 60 * 60


    conn = sqlite3.connect('DS.db')
    c = conn.cursor()
    sql_cmd = "SELECT * FROM price WHERE CC='{}'".format(CC)
    c.execute(sql_cmd)
    data = c.fetchall()

    prices = []
    EMA = []
    SMA = []
    dtime = []
    names = []

    N = int(N)  # period
    bN = int(bN)  # box-plot period
    CC = str(CC)

    #get time difference
    for i in range(len(data)):

	prices.append(data[i][1])
        a = dt.strptime(data[i][3],'%Y-%m-%d %H:%M:%S')
    	dtime.append(str('{:02d}'.format(a.hour)) + ":" + str('{:02d}'.format(a.minute)) + ":" + str('{:02d}'.format(a.second)))

    plen = len(prices)

    #build data for boxplots
    boxtraces = []

    for i in xrange(0, plen, bN):

        y = prices[i:i + bN]
        ind = i + bN - 1

        if (i + bN) > len(dtime):

            ind = len(dtime) - 1

        name = dtime[ind]
        names.append(name)

        trace = Box(y=y, name=name, showlegend=False,
                    x=[i for j in range(len(y))])
        boxtraces.append(trace)

    #build data for EMA

    if plen > N:

        EMA = [None for i in range(N - 1)]

        y = prices[0:N]
        avg = reduce(lambda x, y_: x + y_, y) / len(y)
        EMA.append(avg)

        for i in xrange(N, plen, 1):

            new_ema = ((prices[i] - EMA[-1])
                       * 2.0 / (N + 1)) + EMA[-1]

            EMA.append(new_ema)

    #build data for SMA
    if plen > N:

        SMA = [None for i in range(N - 1)]

        for i in xrange(0, plen - N + 1, 1):

            y = prices[i: i + N]
            sma = reduce(lambda x, y__: x + y__, y) / len(y)
            SMA.append(sma)

    trace2 = Scatter(
        y=SMA,
        x=[i for i in xrange(1, plen+3, 1)],
        line=Line(
            color='#42C4F7',
            dash='dash'
        ),
        mode='lines',
        name=str(N) + '-period-SMA'
    )

    trace = Scatter(
        y=prices,
        x=[i for i in xrange(0, plen, 1)],
        line=Line(
            color='#32DD32'
        ),
        mode='lines',
        name='Price'
    )

    trace3 = Scatter(
        y=EMA,
        x=[i for i in xrange(1, plen+3, 1)],
        line=Line(
            color='#53A39B',
            dash='dash'
        ),
        mode='lines',
        name= str(N) + '-period-EMA'
    )

    layout = Layout(
        xaxis=dict(
            title='Time',
            tickmode="array",
            ticktext=names,
            tickvals=[i for i in xrange(0, plen, bN)],
            showticklabels=True
        ),
        yaxis=dict(
            title='Prices',
            #tickangle=45,
            tickmode="array",
            autorange=True,
            tickformat="$,.2f",
            ticktext=names,
            showticklabels=True
        ),
        height=500,
        margin=Margin(
            t=30,
            l=80,
            r=30)
            )

    traces = []

    traces.append(trace)
    traces.append(trace2)
    traces.append(trace3)
    boxtraces.extend(traces)

    return Figure(data=boxtraces, layout=layout)

@app.callback(
    Output(component_id='bpi1', component_property='figure'),
    [
        Input(component_id='crypto', component_property='value')
    ],
    [],
    [Event('bpi-update', 'interval')]

)
def get_sentiment(CC):

    #T hour time frame

    curr_time = time.time()

    conn = sqlite3.connect('DS.db')
    c = conn.cursor()
    sql_cmd = "SELECT * FROM sentiment WHERE cc='{}'".format(CC)
    c.execute(sql_cmd)
    #data = db.search(BPI.updatedTime > begin_time)
    data = c.fetchall()

    dtime = []
    dtime1 = []
    names = []
    positive = []
    neutral = []
    negative = []

    CC = str(CC)

    #get time difference
    for i in range(len(data)):

        a = dt.strptime(data[i][0],'%Y-%m-%d %H:%M:%S')
    	dtime1.append(str('{:02d}'.format(a.hour)) + ":" + str('{:02d}'.format(a.minute)) + ":" + str('{:02d}'.format(a.second)))
    	dtime = dtime1[0::3]
	if data[i][2] == 'Positive':
        	positive.append(data[i][3]*100)
   	elif data[i][2] == 'Neutral':
        	neutral.append(data[i][3]*100)
   	else:
        	negative.append(data[i][3]*100)

    plen = len(positive)

    pos_stck=positive
    ntr_stck=[y0+y1 for y0, y1 in zip(positive, neutral)]
    neg_stck=[y0+y1+y2 for y0, y1, y2 in zip(positive, neutral, negative)]

    pos_txt=[str("%0.2f" % (y0,))+'%' for y0 in positive]
    ntr_txt=[str("%0.2f" % (y1,))+'%' for y1 in neutral]
    neg_txt=[str("%0.2f" % (y2,))+'%' for y2 in negative]

    trace = Scatter(
        x=dtime,
    	y=pos_stck,
    	text=pos_txt,
    	hoverinfo='x+text',
    	mode='lines',
    	line=dict(width=0.5,
              color='rgb(45, 188, 50)'),
    	fill='tonexty',
    	name='Positive'
    )

    trace2 = Scatter(
        x=dtime,
    	y=ntr_stck,
    	text=ntr_txt,
    	hoverinfo='x+text',
    	mode='lines',
    	line=dict(width=0.5,
              color='rgb(224, 220, 8)'),
    	fill='tonexty',
    	name='Neutral'
    )
    trace3 = Scatter(
        x=dtime,
    	y=neg_stck,
    	text=neg_txt,
    	hoverinfo='x+text',
    	mode='lines',
    	line=dict(width=0.5,
              color='rgb(214, 6, 37)'),
    	fill='tonexty',
    	name='Negative'
    )



    #layout = Layout(
     #   xaxis=dict(
      #      tickmode="array",
       #     ticktext=names,
        #    tickvals=[i for i in xrange(0, plen, 5)],
         #   showticklabels=True
        #),
        #height=450,
        #margin=Margin(
         #   t=45,
          #  l=50,
           # r=50))

    traces = []

    traces.append(trace)
    traces.append(trace2)
    traces.append(trace3)

    layout = Layout(
        showlegend=True,
        xaxis=dict(
            title='Time',
            type='category',
            tickmode="array",
            tickvals=[i for i in xrange(0, plen, 5)],
            showticklabels=True
        ),
        yaxis=dict(
            title='Sentiment',
            type='linear',
            range=[0, 100],
            dtick=20,
            ticksuffix='%'
        ),
        height=450,
        margin=Margin(
            t=30,
            l=50,
            r=30)
    )

    return Figure(data=traces, layout=layout)

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                "https://fonts.googleapis.com/css?family=Raleway:400,400i,700,700i",
                "https://fonts.googleapis.com/css?family=Product+Sans:400,400i,700,700i"]



for css in external_css:
    app.css.append_css({"external_url": css})

css_directory = os.getcwd()
stylesheets = ['BitcoinMAvgs.css']
static_css_route = '/static/'


@app.server.route('{}<stylesheet>'.format(static_css_route))
def serve_stylesheet(stylesheet):
    if stylesheet not in stylesheets:
        raise Exception(
            '"{}" is excluded from the allowed static files'.format(
                stylesheet
            )
        )
    return send_from_directory(css_directory, stylesheet)


for stylesheet in stylesheets:
    app.css.append_css({"external_url": "/static/{}".format(stylesheet)})

if __name__ == '__main__':
    app.run_server()
