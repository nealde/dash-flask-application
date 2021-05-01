"""Instantiate a Dash application."""
import numpy as np
import pandas as pd

import dash_table
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from .layout import html_layout
from .pages.single_particle import init_page as single_particle_page
from .pages.p2d import init_page as p2d_page

base = '/dashapp'


def init_dashboard(server, pages):
    """Create a Plotly Dash dashboard."""
    from .pages.app_base import init_app
    dash_app = init_app(server)
    spm_layout = single_particle_page(dash_app)
    p2d_layout = p2d_page(dash_app)

    # Custom HTML layout
    dash_app.index_string = html_layout

    navbar = dbc.NavbarSimple(
        children=[
            dbc.DropdownMenu(
                nav=True,
                in_navbar=True,
                label='Menu',
                children=[
                    dbc.DropdownMenuItem(dbc.NavLink("Home Page", href=f'{base}/')),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem(dbc.NavLink("Single Particle Model", href=f'{base}/single-particle')),
                    dbc.DropdownMenuItem(dbc.NavLink("Pseudo Two-Dimensional Model", href=f'{base}/pseudo-two-dim'))
                ]
            )
        ],
        brand="Dash App",
        brand_href="/",
        sticky="top",
        style={'width': '90%'}
    )

    dash_app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        navbar,
        # content
        dbc.Row([
            dbc.Col([], md=1),
            dbc.Col([
                dbc.Container([
                    html.Div(id='page-content'),
                ], className='mt-4')
            ], md=10)
        ])
    ])
    index_page = html.Div([
        html.H3('Please select an item from the dropdown to begin')
    ])

    @dash_app.callback(Output('page-content', 'children'),
                       [Input('url', 'pathname')])
    def display_page(pathname):
        print(pathname)
        if pathname == f'{base}/single-particle':
            return spm_layout
        elif pathname == f'{base}/pseudo-two-dim':
            return p2d_layout
        else:
            return index_page
    return dash_app.server
