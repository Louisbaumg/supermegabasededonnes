# Import des librairies nécessaires
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import sqlite3
from flask import Flask, session
import pandas as pd
import dash_bootstrap_components as dbc

# Création de l'application Flask et Dash
server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)


# Configure Flask pour utiliser des sessions
app.server.config['SECRET_KEY'] = 'un_secret_très_secret'

def user_is_authenticated():
    return session.get('authenticated', False)

# Définition du layout de l'app Dash avec une page de connexion initiale
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Layout de la page de connexion
layout_login_page = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H2("Connexion", className="text-center mb-4"),
            width=12
        )
    ),
    dbc.Row(
        dbc.Col(
            [
                dbc.Input(id='username', type='text', placeholder='Identifiant', className="mb-3"),
                dbc.Input(id='password', type='password', placeholder='Mot de passe', className="mb-3"),
                dbc.Button('Connexion', id='login-button', className="w-100"),
                html.Div(id='login-feedback', className="mt-3")
            ],
            width=6
        ),
        justify="center"
    )
], fluid=True, className="mt-5")


# Layout du menu principal après connexion
layout_main_menu = html.Div([
    html.H3('Menu principal'),
    dcc.Link('Tables primaires', href='/page-1'),
    html.Br(),
    dcc.Link('Aller à la page 2', href='/page-2')
])

# Layout de la page 1
layout_page_1 = html.Div([
    html.H3('Page 1'),
    dcc.Link('Retour au menu principal', href='/main-menu'),
    html.Div(id='table-container')
])

# Callback pour afficher les données de la base de données
@app.callback(Output('table-container', 'children'),
              [Input('url', 'pathname')])
def display_db_data(pathname):
    if pathname == '/page-1':
        # Connexion à la base de données
        conn = sqlite3.connect('base3.sqlite')
        # Obtention de la liste des tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        # Lecture des données de chaque table et création d'un tableau Dash pour chaque table
        table_divs = []
        for table_name in tables:
            df = pd.read_sql_query("SELECT * from %s" % table_name[0], conn)
            table = dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                page_size=10,
                style_cell={'textAlign': 'left'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ]
            )

            table_divs.append(html.H4('Table : ' + table_name[0]))
            table_divs.append(table)
        conn.close()
        return table_divs

# Callback pour la gestion de la navigation
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])

def display_page(pathname):
    if pathname == '/':
        return layout_login_page
    elif pathname == '/main-menu' or pathname == '/page-1':
        if user_is_authenticated():  # Vérifie si l'utilisateur est authentifié
            if pathname == '/main-menu':
                return layout_main_menu
            elif pathname == '/page-1':
                return layout_page_1
        else:
            return 'Veuillez vous connecter pour accéder à cette page.', dcc.Link('Aller à la page de connexion', href='/')
    else:
        return '404'


# Callback pour vérifier les identifiants de connexion
@app.callback(Output('url', 'pathname'),
              [Input('login-button', 'n_clicks')],
              [State('username', 'value'), State('password', 'value')])

def login_auth(n_clicks, username, password):
    if n_clicks is not None and n_clicks > 0:
        try:
            conn = sqlite3.connect('base3.sqlite')
            cur = conn.cursor()
            cur.execute("SELECT UTI_ID FROM UTILISATEUR WHERE UTI_login = ? AND UTI_mdp = ?", (username, password))
            resultat = cur.fetchone()
            if resultat:
                session['authenticated'] = True  # L'utilisateur est authentifié
                return '/main-menu'
            else:
                session['authenticated'] = False  # L'authentification a échoué
                return '/'
        except sqlite3.Error as e:
            print("Erreur lors de l'accès à la base de données", e)
            return '/'
        finally:
            if conn:
                cur.close()
                conn.close()
    else:
        return '/'

if __name__ == '__main__':
    app.run_server(debug=True)
