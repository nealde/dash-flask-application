import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

def init_app(server):
    dash_app = dash.Dash(
            server=server,
            routes_pathname_prefix='/dashapp/',
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
                '/static/css/milligram.min.css',
                '/static/css/style.css',
            ]
        )
    dash_app.config.suppress_callback_exceptions = True

    # dash_app.layout = html.Div([
    #
    #     html.Div(id='page-content')
    # ])

    return dash_app
