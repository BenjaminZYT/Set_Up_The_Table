#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import sqlite3
import pandas as pd
from datetime import datetime
from dash import dcc, html, Input, Output, State, callback, Dash, dash_table
import dash_bootstrap_components as dbc
import dash

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

# Helper functions
def list_databases(directory):
    # List all SQLite database files in the specified directory
    return [f for f in os.listdir(directory) if f.endswith('.db')]

def list_tables(db_path):
    # List all tables in the specified SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return [table[0] for table in tables]

def fetch_table_data(db_path, table_name):
    # Fetch data from the specified table in the SQLite database
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# App layout
app.layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.Label('Select Database'),
            dcc.Dropdown(
                id='database-dropdown',
                options=[{'label': db, 'value': db} for db in list_databases('/mnt/data')],
                placeholder="Select a database"
            )
        ]),
        dbc.Col([
            html.Label('Select Table'),
            dcc.Dropdown(
                id='table-dropdown',
                placeholder="Select a table",
                disabled=True
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.Button('Go', id='go-button', n_clicks=0)
        ]),
        dbc.Col([
            html.Button('Download CSV', id='download-button', n_clicks=0, disabled=True)
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(id='table-output')
        ])
    ]),
    dcc.Download(id="download-csv")
])

# Callbacks
@app.callback(
    Output('table-dropdown', 'options'),
    Output('table-dropdown', 'disabled'),
    Input('database-dropdown', 'value')
)
def update_table_dropdown(database):
    if not database:
        return [], True
    tables = list_tables(f'/mnt/data/{database}')
    return [{'label': table, 'value': table} for table in tables], False

@app.callback(
    Output('table-output', 'children'),
    Output('download-button', 'disabled'),
    Input('go-button', 'n_clicks'),
    State('database-dropdown', 'value'),
    State('table-dropdown', 'value')
)
def display_table(n_clicks, database, table):
    if n_clicks == 0 or not database or not table:
        return '', True

    df = fetch_table_data(f'/mnt/data/{database}', table)
    table_div = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in df.columns],
        page_size=10
    )
    return table_div, False

@app.callback(
    Output('download-csv', 'data'),
    Input('download-button', 'n_clicks'),
    State('database-dropdown', 'value'),
    State('table-dropdown', 'value')
)
def download_csv(n_clicks, database, table):
    if n_clicks == 0 or not database or not table:
        return None

    df = fetch_table_data(f'/mnt/data/{database}', table)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{database}_{table}_{timestamp}.csv"
    return dcc.send_data_frame(df.to_csv, filename=filename)

if __name__ == '__main__':
    app.run_server(debug=True)

