import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import numpy as np
import json
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from ampere import PseudoTwoDimFD
from ampere.base_battery import ChargeResult
from scipy.interpolate import interp1d
from plotly.subplots import make_subplots
from colour import Color


def init_page(app):
    layout = html.Div([
        html.H1('Pseudo Two-Dimensional Model'),
        html.Div([], style={'height': '30px'}),
        html.A('A model walkthrough is available for the P2D Model', href='/articles/p2d/'),
        html.Div([], style={'height': '30px'}),
        html.Img(src='/img/p2d/p2d_3d.png'),
        html.Div([], style={'height': '30px'}),
        html.P('Select a current for the simulation below.'),
        dcc.Slider(id='p2d-current', min=-10, max=10, value=4, step=0.1, updatemode='drag',
                   marks={i: f'{i} amps' for i in range(-10, 12, 2)}),
        html.Div([], style={'height': '30px'}),
        dbc.Button('Run Simulation', id='p2d-start-button'),

        html.Div(id='p2d-main-plots'),
        html.Div(id='p2d-data-div', style={'display': 'none'}),
        html.Div(id='p2d-data-internal-pos-div', style={'display': 'none'}),
        html.Div(id='p2d-data-internal-neg-div', style={'display': 'none'})
    ])

    @app.callback([Output('p2d-main-plots', 'children'),
                   Output('p2d-data-div', 'children'),
                   Output('p2d-data-internal-pos-div', 'children'),
                   Output('p2d-data-internal-neg-div', 'children')],
                  [Input('p2d-start-button', 'n_clicks')],
                  [State('p2d-current', 'value')])
    def p2d_callback(n_clicks, amps):
        if amps != 0:
            p2d = PseudoTwoDimFD(initial_parameters={'Nr1': 9, 'Nr2': 9, 'N1': 11, 'N3': 11, 'ln': 40e-6, 'Dsp': 3.5e-13})
            # run simulation with internal variables
            if amps > 0:
                amps = max(amps, 0.2)
                data = p2d.discharge(current=amps, internal=True, trim=True)
            if amps <= 0:
                amps = min(amps, -0.2)
                data = p2d.charge(current=abs(amps), internal=True, trim=True)

            internal_data = data.internal
            raw_times = internal_data[:, 0]
            delta_time = np.diff(raw_times)
            total_capacity = round(abs(delta_time * internal_data[1:, -1]).sum() / 3600 / 17.1, 2) # convert from seconds to hours

            start_color_neg = "#b2d8ff"  # light blue
            end_color_neg = "#00264c"  # dark blue

            start_color_pos = "#a0f093"  # light green
            end_color_pos = "#1b6c0f"  # dark green

            start_color_sep = '#ee8686'  # light red
            end_color_sep = '#a21616'  # dark red

            positive_particles = p2d.initial_parameters['N1'] + 1  # 2 boundary conditions and a base color
            negative_particles = p2d.initial_parameters['N3'] + 1  # 2 boundary conditions and a base color
            sep_nodes = p2d.initial_parameters['N2'] + 1  # 2 boundary conditions and a base color

            # list of "N" colors between "start_color" and "end_color"
            colorscale_neg = [x.hex for x in list(Color(start_color_neg).range_to(Color(end_color_neg), negative_particles))][::-1]
            colorscale_pos = [x.hex for x in list(Color(start_color_pos).range_to(Color(end_color_pos), positive_particles))][::-1]
            colorscale_sep = [x.hex for x in list(Color(start_color_sep).range_to(Color(end_color_sep), sep_nodes))][::-1]

            positive_potential = linearly_interpolate_concentrations(data.time, raw_times, internal_data[:, p2d.internal_structure['solid_phase_potential']['positive'][:1]])
            negative_potential = linearly_interpolate_concentrations(data.time, raw_times, internal_data[:, p2d.internal_structure['solid_phase_potential']['negative'][-1:]])
            data = ChargeResult(data.time, data.voltage, None, None)

            pos_electrode = p2d.initial_parameters['Nr1']
            neg_electrode = p2d.initial_parameters['Nr2']
            initial_time = 1
            voltage_fig = go.Figure()
            voltage_fig.add_trace(go.Scatter(x=data.time, y=data.voltage, mode='lines', name='Voltage', marker={'color': colorscale_pos[0]}))
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

            sep_nodes = p2d.initial_parameters['N2']+2
            liquid_keys = p2d.internal_structure['liquid_phase_potential']
            liquid_conc_keys = p2d.internal_structure['electrolyte_lithium_concentration']
            liquid_inds = []
            liquid_conc_inds = []
            for key in liquid_keys:
                liquid_inds.extend(liquid_keys[key])
                liquid_conc_inds.extend(liquid_conc_keys[key])
            # liquid_pot = linearly_interpolate_concentrations(data.time, raw_times, internal_data[:, liquid_inds])
            # liquid_conc = linearly_interpolate_concentrations(data.time, raw_times, internal_data[:, liquid_conc_inds])
            #
            # liquid_x = list(range(positive_particles + negative_particles + sep_nodes))
            # liquid_pot_conc_fig = make_subplots(specs=[[{"secondary_y": True}]])
            # liquid_pot_conc_fig.add_trace(go.Scatter(x=liquid_x, y=liquid_pot.T[0], mode='lines',
            #                                       name='Liquid Potential',
            #                                       marker={'color': colorscale_pos[1], 'size': 10}), secondary_y=False)
            #
            # liquid_pot_conc_fig.add_trace(go.Scatter(x=liquid_x, y=liquid_conc.T[0], mode='lines',
            #                                       name='Liquid Li Conc',
            #                                       marker={'color': colorscale_sep[1], 'size': 10}), secondary_y=True)
            # liquid_pot_conc_fig.update_layout(
            #     margin=dict(l=55, r=20, t=60, b=20),
            #     paper_bgcolor="rgb(240, 240, 240)",
            #     plot_bgcolor='rgb(220, 220, 220)',
            #     width=1000,
            #     height=350,
            #     title='Positive and Negative Electrode Potentials',
            #     xaxis_title="Time (s)",
            #     legend=dict(
            #         x=0.05,
            #         y=.3,
            #         traceorder="normal",
            #         font=dict(
            #             family="sans-serif",
            #             size=12,
            #             color="black"
            #         ),
            #     ),
            # )
            # liquid_pot_conc_fig.update_yaxes(title_text="Liquid Potential (V)", secondary_y=False)
            # liquid_pot_conc_fig.update_yaxes(title_text="Liquid Li Concentration", secondary_y=True)

            internal_pot_fig = make_subplots(specs=[[{"secondary_y": True}]])
            internal_pot_fig.add_trace(go.Scatter(x=data.time, y=positive_potential.T[0], mode='lines', name='Positive Electrode Potential', marker={'color': colorscale_pos[0]}), secondary_y=False)
            internal_pot_fig.add_trace(go.Scatter(x=[data.time[4]], y=[positive_potential.T[0][4]], mode='markers', name='Current PE Potential', marker={'color': colorscale_pos[1], 'size': 10}), secondary_y=False)
            internal_pot_fig.add_trace(go.Scatter(x=data.time, y=negative_potential.T[0], mode='lines', name='Negative Electrode Potential', marker={'color': colorscale_neg[0]}), secondary_y=True)
            internal_pot_fig.add_trace(go.Scatter(x=[data.time[4]], y=[negative_potential.T[0][4]], mode='markers', name='Current NE Potential', marker={'color': colorscale_neg[1], 'size': 10}), secondary_y=True)
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

            pos_radius = np.linspace(0, 1, pos_electrode + 2) * p2d.initial_parameters['Rp']
            neg_radius = np.linspace(0, 1, neg_electrode + 2) * p2d.initial_parameters['Rn']

            dict_data['internal_data'] = {
                'p_pot': list(positive_potential.T[0]),
                'n_pot': list(negative_potential.T[0]),
                # 'liquid_pot': [list(time_slice) for time_slice in liquid_pot],
                # 'liquid_conc': [list(time_slice) for time_slice in liquid_conc],
                # 'total_nodes': liquid_x
            }
            dict_data_internal_positive = {
                'p_x': list(pos_radius),
                'positive': {}
            }
            dict_data_internal_negative = {
                'n_x': list(neg_radius),
                'negative': {}
            }

            pos_internal_fig = go.Figure()
            # pos_internal_fig.add_trace(
            #     go.Scatter(x=pos_radius,
            #                y=pos_conc[0, :].T,
            #                mode='lines',
            #                name='Original Li Concentration',
            #                marker={'color': colorscale_pos[0]}))
            positive_electrode_thickness = p2d.initial_parameters['lp']
            for i, particle_number in enumerate({k: v for k, v in p2d.internal_structure['solid_lithium_concentration'].items() if 'positive' in k}):
                depth = round(positive_electrode_thickness * (i / (positive_particles - 2)) * 1e6, 1)
                indices = p2d.internal_structure['solid_lithium_concentration'][particle_number]
                pos_conc = internal_data[:, indices]
                pos_conc = linearly_interpolate_concentrations(data.time, raw_times, pos_conc)
                dict_data_internal_positive['positive'][i] = [list(time_slice) for time_slice in pos_conc]
                pos_internal_fig.add_trace(
                    go.Scatter(x=pos_radius,
                               y=pos_conc[initial_time, :].T,
                               mode='lines',
                               name=f'Li at {depth}um',
                               marker={'color': colorscale_pos[i+1]}))
            pos_internal_fig.update_layout(
                margin=dict(l=55, r=20, t=40, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=500,
                height=350,
                # legend=dict(
                #     x=0,
                #     y=.5,
                #     traceorder="normal",
                #     font=dict(
                #         family="sans-serif",
                #         size=12,
                #         color="black"
                #     ),
                # ),
                title='Positive Particle Li Concentration',
                xaxis_title="Distance From Center Of Particle (m)",
            )


            neg_internal_fig = go.Figure()
            # neg_internal_fig.add_trace(go.Scatter(x=neg_radius,
            #                                       y=neg_conc[0, :].T,
            #                                       mode='lines',
            #                                       name='Original Li Concentration',
            #                                       marker={'color': colorscale_neg[0]}))
            negative_electrode_thickness = p2d.initial_parameters['ln']
            for i, particle_number in enumerate({k: v for k, v in p2d.internal_structure['solid_lithium_concentration'].items() if 'negative' in k}):
                # for the negative particles, index 0 is closest to the separator.
                depth = round((negative_electrode_thickness - negative_electrode_thickness * (i / (negative_particles - 2))) * 1e6, 1)
                indices = p2d.internal_structure['solid_lithium_concentration'][particle_number]
                neg_conc = internal_data[:, indices]
                neg_conc = linearly_interpolate_concentrations(data.time, raw_times, neg_conc)
                dict_data_internal_negative['negative'][i] = [list(time_slice) for time_slice in neg_conc]
                neg_internal_fig.add_trace(
                    go.Scatter(x=neg_radius,
                               y=neg_conc[initial_time, :].T,
                               mode='lines',
                               name=f'Li at {depth}um',
                               marker={'color': colorscale_neg[i + 1]}))
            # neg_internal_fig.add_trace(go.Scatter(x=neg_radius,
            #                                       y=neg_conc[initial_time, :].T,
            #                                       mode='lines',
            #                                       name='Current Concentration',
            #                                       marker={'color': colorscale_neg[1]}))
            neg_internal_fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor="rgb(240, 240, 240)",
                plot_bgcolor='rgb(220, 220, 220)',
                width=500,
                height=350,
                # legend=dict(
                #     x=0,
                #     y=.3,
                #     traceorder="normal",
                #     font=dict(
                #         family="sans-serif",
                #         size=12,
                #         color="black"
                #     ),
                # ),
                title='Negative Particle Li Concentration',
                xaxis_title="Distance From Center Of Particle (m)",
            )


            l = html.Div([
                dbc.Row([
                    dcc.Graph(
                        id='p2d-voltage-graph',
                        figure=voltage_fig
                    ),
                    html.Div([], style={'height': '40px'}),
                    html.P(f'Above is the discharge of the simulated battery. By scrubbing through time, you can examine the internal states of the cell. Based on the design parameters, the capacity of this cell is {total_capacity} AH'),
                    html.P('As current increases, the capacity will decrease due to Li depletion at the surface of the particles relative to total Li concentration.')
                ]),
                # dbc.Row([
                #    dcc.Graph(
                #        id='p2d-liquid-graph',
                #        figure=liquid_pot_conc_fig
                #    ),
                #     html.P('Above is the Liquid-phase potential and liquid Li concentration across the cell')
                # ]),

                dcc.Slider(id='p2d-time', min=0, max=len(data.time), value=4, step=1, updatemode='drag',
                           marks={i: f'{int(data.time[i])}s' for i in range(0, len(data.time), 30)}),
                dbc.Row([
                    html.Div([], style={'height': '20px'}),
                    html.P('During discharge, the positive electrode concentration rises. During charge, it falls.  Color indicates particle distance from current collector.'),
                    html.P('In particular, notice the concentration disparity across electrode depth for the negative electrode, and how the surface concentrations come together again as the battery nears total discharge.  This is a great example of Li starvation at the surface of the particles closest to the separator, which passes the load to deeper particles.'),
                    dcc.Graph(
                        id='p2d-pos-graph',
                        figure=pos_internal_fig,
                        style={'width': '50%'}
                    ),
                    dcc.Graph(
                        id='p2d-neg-graph',
                        figure=neg_internal_fig,
                        style={'width': '50%'}
                    ),
                ]),
                dbc.Row([
                    html.Div([], style={'height': '40px'}),
                    html.P('The potentials of the positive and negative electrode are based on the Li concentration at the surface of the particles that make up the electrode. It is the changing of these potentials that causes the battery voltage to change with use.'),
                    html.P('When we visualize the positive / negative electrode potentials like this, it becomes clear why the lithium-ion battery voltage seems to fall off a cliff as the battery nears empty - the negative electrode potential skyrockets as the particles near Lithium saturation.'),
                    dcc.Graph(
                        id='p2d-potential-graph',
                        figure=internal_pot_fig
                    ),
                ]),
            ])

            return l, json.dumps(dict_data), json.dumps(dict_data_internal_positive), json.dumps(dict_data_internal_negative)
        return None, ''

    app.clientside_callback(
        """
        function(time, data) {
            // tuple is (dict of new data, target trace index, number of points to keep)
            const _data = JSON.parse(data)['voltage_data']['time'];
            return [{'x':[[_data[time], _data[time]]], 'y': [[2, 4.2]]}, [1], 2];
        }
        """, Output('p2d-voltage-graph', 'extendData'), [Input('p2d-time', 'value')], [State('p2d-data-div', 'children')]
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
        """, Output('p2d-potential-graph', 'extendData'), [Input('p2d-time', 'value')],
        [State('p2d-data-div', 'children')]
    )

    # app.clientside_callback(
    #     """
    #     function(time, data) {
    #         // tuple is (dict of new data, target trace index, number of points to keep)
    #         const _data = JSON.parse(data);
    #         const x = _data['internal_data']['total_nodes'];
    #         const pot = _data['internal_data']['liquid_pot'];
    #         const conc = _data['internal_data']['liquid_conc'];
    #         return [{'x': [x, x], 'y': [pot[time], conc[time]] }, [0, 1], x.length];
    #     }
    #     """, Output('p2d-liquid-graph', 'extendData'), [Input('p2d-time', 'value')],
    #     [State('p2d-data-div', 'children')]
    # )

    # @app.callback(Output('p2d-pos-graph', 'extendData'), [Input('p2d-time', 'value')],
    #     [State('p2d-data-div', 'children')])
    # def update_potential(time, data):
    #     data = json.loads(data)
    #     positive = data['internal_data']['positive']
    #     _px = data['internal_data']['p_x']
    #     count = 1
    #     xs = []
    #     ys = []
    #     inds = []
    #     for key, value in positive.items():
    #         inds.append(count)
    #         ys.append([value[time]])
    #         xs.append([_px])
    #     return ({'x': xs, 'y': ys}, inds, len(_px))

    app.clientside_callback(
        """
        function(time, data) {
            // tuple is (dict of new data, target trace index, number of points to keep)
            const _data = JSON.parse(data);
            const positive = _data['positive'];
            const _px = _data['p_x'];
            var xs = [];
            var ys = [];
            var indices = [];
            var count = 0;
            for (let [key, value] of Object.entries(positive)) {
                xs.push(_px);
                ys.push(value[time]);
                indices.push(count);
                count ++;
            };

            return [{'x': xs, 'y': ys}, indices, _px.length];
        }
        """, Output('p2d-pos-graph', 'extendData'), [Input('p2d-time', 'value')],[State('p2d-data-internal-pos-div', 'children')]
    )

    app.clientside_callback(
        """
        function(time, data) {
            // tuple is (dict of new data, target trace index, number of points to keep)
            const _data = JSON.parse(data);
            const negative = _data['negative'];
            const _nx = _data['n_x'];
            var xs = [];
            var ys = [];
            var indices = [];
            var count = 0;
            for (let [key, value] of Object.entries(negative)) {
                xs.push(_nx);
                ys.push(value[time]);
                indices.push(count);
                count ++;
            };

            return [{'x': xs, 'y': ys}, indices, _nx.length];
        }
        """, Output('p2d-neg-graph', 'extendData'), [Input('p2d-time', 'value')], [State('p2d-data-internal-neg-div', 'children')]
    )

    # app.clientside_callback(
    #     """
    #     function(time, data) {
    #         // tuple is (dict of new data, target trace index, number of points to keep)
    #         const _data = JSON.parse(data);
    #         const negative = _data['internal_data']['positive'];
    #         const _nx = _data['internal_data']['p_x'];
    #         return [{'x': [_nx, _nx], 'y': [negative[0][time], negative[1][time]]}, [1, 2], _nx.length];
    #     }
    #     """, Output('p2d-pos-graph', 'extendData'), [Input('p2d-time', 'value')], [State('p2d-data-div', 'children')]
    # )

    # app.clientside_callback(
    #     """
    #     function(time, data) {
    #         // tuple is (dict of new data, target trace index, number of points to keep)
    #         const _data = JSON.parse(data);
    #         const negative = _data['internal_data']['negative'];
    #         const _nx = _data['internal_data']['n_x'];
    #         return [{'x': [_nx], 'y': [negative[time]]}, [1], _nx.length];
    #     }
    #     """, Output('p2d-neg-graph', 'extendData'), [Input('p2d-time', 'value')], [State('p2d-data-div', 'children')]
    # )

    return layout


def linearly_interpolate_concentrations(time, raw_time, concentrations):
    return np.concatenate([interp1d(raw_time, concentrations[:, i], kind='cubic', bounds_error=False)(time)[:, np.newaxis] for i in range(concentrations.shape[1])], axis=1)