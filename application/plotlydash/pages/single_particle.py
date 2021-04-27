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
from plotly.subplots import make_subplots
from colour import Color


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

            internal_data = data.internal
            raw_times = internal_data[:, 0]
            delta_time = np.diff(raw_times)
            total_capacity = round(abs(delta_time * internal_data[1:, -1]).sum() / 3600 / 30, 2) # convert from seconds to hours
            # positive_colorscale = 'darkmint'
            # negative_colorscale = 'brug'

            start_color = "#b2d8ff"  # light blue
            end_color = "#00264c"  # dark blue

            # list of "N" colors between "start_color" and "end_color"
            colorscale = [x.hex for x in list(Color(start_color).range_to(Color(end_color), 5))][::-1]
            light_green = 'rgb(33, 209, 59)'
            dark_green = 'darkgreen'

            positive_potential = linearly_interpolate_concentrations(data.time, raw_times, internal_data[:, -4:-3])
            negative_potential = linearly_interpolate_concentrations(data.time, raw_times, internal_data[:, -3:-2])
            data = ChargeResult(data.time, data.voltage, None, None)

            pos_electrode = spm.initial_parameters['N1']
            neg_electrode = spm.initial_parameters['N2']
            initial_time = 1
            voltage_fig = go.Figure()
            voltage_fig.add_trace(go.Scatter(x=data.time, y=data.voltage, mode='lines', name='Voltage', marker={'color': dark_green}))
            voltage_fig.add_trace(go.Scatter(x=[data.time[initial_time], data.time[initial_time]], y=[2, 4.2], mode='lines', name='Time Slice', marker={'color': 'darkgrey'}))
            voltage_fig.update_layout(
                margin=dict(l=55, r=20, t=60, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=1000,
                height=350,
                title=f'Discharge Voltage vs Time at {amps} Amps with Current Time Indicator',
                xaxis_title="Time (s)",
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
            )

            internal_pot_fig = make_subplots(specs=[[{"secondary_y": True}]])

            internal_pot_fig.add_trace(go.Scatter(x=data.time, y=positive_potential.T[0], mode='lines', name='Positive Electrode Potential', marker={'color': dark_green}), secondary_y=False)
            internal_pot_fig.add_trace(go.Scatter(x=[data.time[4]], y=[positive_potential.T[0][4]], mode='markers', name='Current PE Potential', marker={'color': light_green, 'size': 10}), secondary_y=False)
            internal_pot_fig.add_trace(go.Scatter(x=data.time, y=negative_potential.T[0], mode='lines', name='Negative Electrode Potential', marker={'color': colorscale[0]}), secondary_y=True)
            internal_pot_fig.add_trace(go.Scatter(x=[data.time[4]], y=[negative_potential.T[0][4]], mode='markers', name='Current NE Potential', marker={'color': colorscale[1], 'size': 10}), secondary_y=True)
            internal_pot_fig.update_layout(
                margin=dict(l=55, r=20, t=60, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=1000,
                height=350,
                title='Positive and Negative Electrode Potentials',
                xaxis_title="Time (s)",
                legend=dict(
                    x=0.05,
                    y=.3,
                    traceorder="normal",
                    font=dict(
                        family="sans-serif",
                        size=12,
                        color="black"
                    ),
                ),
            )
            internal_pot_fig.update_yaxes(title_text="Positive Electrode Potential (V)", secondary_y=False)
            internal_pot_fig.update_yaxes(title_text="Negative Electrode Potential (V)", secondary_y=True)

            dict_data = {'voltage_data': {'time': list(data.time), 'voltage': list(data.voltage)}}

            pos_radius = np.linspace(0, 1, pos_electrode + 2) * spm.initial_parameters['Rp']
            neg_radius = np.linspace(0, 1, neg_electrode + 2) * spm.initial_parameters['Rn']

            pos_conc = internal_data[:, spm.internal_structure['positive_concentration']]
            pos_conc = linearly_interpolate_concentrations(data.time, raw_times, pos_conc) / spm.initial_parameters['cspmax']

            neg_conc = internal_data[:, spm.internal_structure['negative_concentration']]
            neg_conc = linearly_interpolate_concentrations(data.time, raw_times, neg_conc) / spm.initial_parameters['csnmax']

            pos_internal_fig = go.Figure()
            pos_internal_fig.add_trace(
                go.Scatter(x=pos_radius,
                           y=pos_conc[0, :].T,
                           mode='lines',
                           name='Original Li Concentration',
                           marker={'color': dark_green}))
            pos_internal_fig.add_trace(
                go.Scatter(x=pos_radius,
                           y=pos_conc[initial_time, :].T,
                           mode='lines',
                           name='Current Concentration',
                           marker={'color': light_green}))
            pos_internal_fig.update_layout(
                margin=dict(l=55, r=20, t=40, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=500,
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
                title='Positive Particle Li Concentration',
                xaxis_title="Distance From Center Of Particle (m)",
            )

            neg_internal_fig = go.Figure()
            neg_internal_fig.add_trace(go.Scatter(x=neg_radius,
                                                  y=neg_conc[0, :].T,
                                                  mode='lines',
                                                  name='Original Li Concentration',
                                                  marker={'color': colorscale[0]}))
            neg_internal_fig.add_trace(go.Scatter(x=neg_radius,
                                                  y=neg_conc[initial_time, :].T,
                                                  mode='lines',
                                                  name='Current Concentration',
                                                  marker={'color': colorscale[1]}))
            neg_internal_fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=500,
                height=350,
                legend=dict(
                    x=0,
                    y=.3,
                    traceorder="normal",
                    font=dict(
                        family="sans-serif",
                        size=12,
                        color="black"
                    ),
                ),
                title='Negative Particle Li Concentration',
                xaxis_title="Distance From Center Of Particle (m)",
            )

            dict_data['internal_data'] = {
                'positive': [list(time_slice) for time_slice in pos_conc],
                'negative': [list(time_slice) for time_slice in neg_conc],
                'p_x': list(pos_radius),
                'n_x': list(neg_radius),
                'p_pot': list(positive_potential.T[0]),
                'n_pot': list(negative_potential.T[0])
            }

            l = html.Div([
                dbc.Row([
                    dcc.Graph(
                        id='spm-voltage-graph',
                        figure=voltage_fig
                    ),
                    html.Div([], style={'height': '40px'}),
                    html.P(f'Above is the discharge of the simulated battery. By scrubbing through time, you can examine the internal states of the cell. Based on the design parameters, the capacity of this cell is {total_capacity} AH'),
                    html.P('As current increases, the capacity will decrease due to Li depletion at the surface of the particles relative to total Li concentration.')
                ]),
                dcc.Slider(id='spm-time', min=0, max=len(data.time), value=4, step=1, updatemode='drag',
                           marks={i: f'{int(data.time[i])}s' for i in range(0, len(data.time)+1, 30)}),
                dbc.Row([
                    html.Div([], style={'height': '20px'}),
                    html.P('During discharge, the positive electrode concentration rises. During charge, it falls.'),
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
                dbc.Row([
                    html.Div([], style={'height': '40px'}),
                    html.P('The potentials of the positive and negative electrode are based on the Li concentration at the surface of the particles that make up the electrode. It is the changing of these potentials that causes the battery voltage to change with use.'),
                    html.P('When we visualize the positive / negative electrode potentials like this, it becomes clear why the lithium-ion battery voltage seems to fall off a cliff as the battery nears empty - the negative electrode potential skyrockets as the particles near Lithium saturation.'),
                    dcc.Graph(
                        id='spm-potential-graph',
                        figure=internal_pot_fig
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
            return [{'x':[[_data[time], _data[time]]], 'y': [[2, 4.2]]}, [1], 2];
        }
        """, Output('spm-voltage-graph', 'extendData'), [Input('spm-time', 'value')], [State('spm-data-div', 'children')]
    )

    app.clientside_callback(
        """
        function(time, data) {
            // tuple is (dict of new data, target trace index, number of points to keep)
            const _data = JSON.parse(data);
            const _time = _data['voltage_data']['time'];
            const pot = _data['internal_data']['p_pot'];
            const npot = _data['internal_data']['n_pot'];
            return [{'x': [[_time[time]], [_time[time]]], 'y': [[pot[time]], [npot[time]]] }, [1, 3], 1];
        }
        """, Output('spm-potential-graph', 'extendData'), [Input('spm-time', 'value')],
        [State('spm-data-div', 'children')]
    )
    # @app.callback(Output('spm-potential-graph', 'extendData'), [Input('spm-time', 'value')],
    #     [State('spm-data-div', 'children')])
    # def update_potential(time, data):
    #     data = json.loads(data)
    #     _time = data['voltage_data']['time']
    #     pot = data['internal_data']['p_pot']
    #     npot = data['internal_data']['n_pot']
    #     return {'x': [[_time[time]], [_time[time]]], 'y': [[pot[time]], [npot[time]]]}, [1, 3], 1

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