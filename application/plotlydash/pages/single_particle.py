import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import numpy as np
import json
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from ampere import SingleParticleFD, SingleParticleFDSEI
from ampere.base_battery import ChargeResult
from scipy.interpolate import interp1d


def init_page(app):
    layout = html.Div([
        html.H1('Single Particle Model'),
        html.Div([], style={'height': '30px'}),
        html.Img(src='/img/spm/spm_3d.png'),
        html.Div([], style={'height': '30px'}),
        html.P('Select a current for the simulation below.'),
        dcc.Slider(id='spm-current', min=-10, max=10, value=4, step=0.5, updatemode='drag',
                   marks={i: f'{i} amps' for i in range(-10, 12, 2)}),
        html.Div([], style={'height': '30px'}),
        dbc.Button('Run Simulation', id='spm-start-button'),

        html.Div(id='spm-main-plots'),
        html.Div(id='spm-data-div', style={'display': 'none'})
    ])

    @app.callback([Output('spm-main-plots', 'children'),
                   Output('spm-data-div', 'children')],
                  [Input('spm-start-button', 'n_clicks')],
                  [State('spm-current', 'value')])
    def spm_callback(n_clicks, amps):
        if amps != 0:

            spm = SingleParticleFD()
            # run simulation with internal variables
            if amps > 0:
                data = spm.discharge(current=int(amps), internal=True, trim=True)
            if amps <= 0:
                data = spm.charge(current=abs(int(amps)), internal=True, trim=True)
            downsample = 3
            internal_data = data.internal
            data = ChargeResult(data.time[::downsample], data.voltage[::downsample], None, None)
            # data.voltage = data.voltage[::downsample]
            # data.time = data.time[::downsample]
            pos_electrode = spm.initial_parameters['N1']
            neg_electrode = spm.initial_parameters['N2']
            initial_time = 1
            voltage_fig = go.Figure()
            voltage_fig.add_trace(go.Scatter(x=data.time, y=data.voltage, mode='lines', name='Voltage'))
            voltage_fig.add_trace(go.Scatter(x=[data.time[initial_time], data.time[initial_time]], y=[2, 4.2], name='Time Slice'))
            voltage_fig.update_layout(
                margin=dict(l=20, r=20, t=60, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=1000,
                height=250,
                title='Discharge Voltage vs Time with Current Time Indicator'
            )

            dict_data = {'voltage_data': {'time': list(data.time), 'voltage': list(data.voltage)}}
            raw_times = internal_data[:, 0]

            pos_conc = internal_data[:, spm.internal_structure['positive_concentration']]
            pos_conc = linearly_interpolate_concentrations(data.time, raw_times, pos_conc)

            neg_conc = internal_data[:, spm.internal_structure['negative_concentration']]
            neg_conc = linearly_interpolate_concentrations(data.time, raw_times, neg_conc)

            pos_internal_fig = go.Figure()
            pos_internal_fig.add_trace(
                go.Scatter(x=np.linspace(0, 1, pos_electrode + 2), y=pos_conc[0, :].T,
                           mode='lines', name='Original Conc'))
            pos_internal_fig.add_trace(
                go.Scatter(x=np.linspace(0, 1, pos_electrode + 2), y=pos_conc[initial_time, :].T,
                           mode='lines', name='Conc at Time Slice'))
            pos_internal_fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=450,
                height=350,
                legend=dict(
                    x=0,
                    y=.5,
                    traceorder="normal",
                    font=dict(
                        family="sans-serif",
                        size=12,
                        color="black"
                    ),
                ),
                title='Positive Particle Li Concentration'
            )

            neg_internal_fig = go.Figure()
            neg_internal_fig.add_trace(go.Scatter(x=np.linspace(0, 1, neg_electrode + 2),
                                                  y=neg_conc[0, :].T,
                                                  mode='lines', name='Original Conc'))
            neg_internal_fig.add_trace(go.Scatter(x=np.linspace(0, 1, neg_electrode + 2),
                                                  y=neg_conc[initial_time, :].T,
                                                  mode='lines', name='Conc at Time Slice'))
            neg_internal_fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=450,
                height=350,
                legend=dict(
                    x=0,
                    y=.5,
                    traceorder="normal",
                    font=dict(
                        family="sans-serif",
                        size=12,
                        color="black"
                    ),
                ),
                title='Negative Particle Li Concentration'
            )

            dict_data['internal_data'] = {
                'positive': [list(time_slice) for time_slice in pos_conc],
                'negative': [list(time_slice) for time_slice in neg_conc],
                'p_x': list(np.linspace(0, 1, pos_electrode + 2)),
                'n_x': list(np.linspace(0, 1, neg_electrode + 2)),
            }

            l = html.Div([
                html.P('Scrub through the simulated time using the slider below.'),
                dcc.Slider(id='spm-time', min=0, max=len(data.time), value=4, step=1, updatemode='drag', marks={i: f'{int(data.time[i])}s' for i in range(0, len(data.time), 20)}),
                dbc.Row([
                    dcc.Graph(
                        id='spm-voltage-graph',
                        figure=voltage_fig
                    ),
                ]),
                dbc.Row([
                    dcc.Graph(
                        id='spm-pos-graph',
                        figure=pos_internal_fig,
                        style={'width': '50%'}
                    ),
                    dcc.Graph(
                        id='spm-neg-graph',
                        figure=neg_internal_fig,
                        style={'width': '50%'}
                    ),
                ]),
            ])

            return l, json.dumps(dict_data)
        return None, ''

    app.clientside_callback(
        """
        function(time, data) {
            // tuple is (dict of new data, target trace index, number of points to keep)
            const _data = JSON.parse(data)['voltage_data']['time'];
            return [{'x':[[_data[time], _data[time]]], 'y': [[0, 4.2]]}, [1], 2];
        }
        """, Output('spm-voltage-graph', 'extendData'), [Input('spm-time', 'value')], [State('spm-data-div', 'children')]
    )

    app.clientside_callback(
        """
        function(time, data) {
            // tuple is (dict of new data, target trace index, number of points to keep)
            const _data = JSON.parse(data);
            const positive = _data['internal_data']['positive'];
            const _px = _data['internal_data']['p_x'];
            return [{'x': [_px], 'y': [positive[time]]}, [1], _px.length];
        }
        """, Output('spm-pos-graph', 'extendData'), [Input('spm-time', 'value')],[State('spm-data-div', 'children')]
    )

    app.clientside_callback(
        """
        function(time, data) {
            // tuple is (dict of new data, target trace index, number of points to keep)
            const _data = JSON.parse(data);
            const negative = _data['internal_data']['negative'];
            const _nx = _data['internal_data']['n_x'];
            return [{'x': [_nx], 'y': [negative[time]]}, [1], _nx.length];
        }
        """, Output('spm-neg-graph', 'extendData'), [Input('spm-time', 'value')], [State('spm-data-div', 'children')]
    )

    return layout


def linearly_interpolate_concentrations(time, raw_time, concentrations):
    return np.concatenate([interp1d(raw_time, concentrations[:, i], kind='cubic', bounds_error=False)(time)[:, np.newaxis] for i in range(concentrations.shape[1])], axis=1)