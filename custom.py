import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go


# Example data:
# Let's say we have several keys: subproblem_idx, thread_idx, size
# We'll simulate some data here:
np.random.seed(42)
subproblems = np.arange(1, 6)    # smaller range for demo
threads = np.arange(1, 5)
sizes = np.arange(50, 101, 10)   # [50,60,70,80,90,100]

data = []
for sp in subproblems:
    for th in threads:
        for sz in sizes:
            latency = np.random.rand() * (sp * 0.1 + th * 0.05 + sz * 0.001)
            data.append({
                "subproblem_idx": sp,
                "thread_idx": th,
                "size": sz,
                "latency": latency
            })
df = pd.DataFrame(data)

# Available dimension keys (excluding latency which is always the dependent variable):
dimension_keys = ["subproblem_idx", "thread_idx", "size"]

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H1("Interactive Latency Visualization"),
    
    html.Div([
        html.Label("Plot Type:"),
        dcc.Dropdown(
            id='plot-type',
            options=[
                {"label": "1D (Line Plot)", "value": "1d"},
                {"label": "2D (Heatmap)", "value": "2d"},
                {"label": "3D (Surface)", "value": "3d"}
            ],
            value="1d"
        )
    ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top"}),

    html.Div(id='dimension-selectors', style={"display": "inline-block", "marginLeft": "20px"}),

    html.Div([
        dcc.Graph(id='main-graph')
    ], style={"marginTop": "20px"})
])


@app.callback(
    Output('dimension-selectors', 'children'),
    Input('plot-type', 'value')
)
def update_dimension_selectors(plot_type):
    # Depending on the plot type, we need different numbers of dimension selectors:
    if plot_type == "1d" and len(dimension_keys) >= 1:
        # One dimension for the x-axis
        return html.Div([
            html.Label("X-axis:"),
            dcc.Dropdown(
                id='dim1',
                options=[{"label": k, "value": k} for k in dimension_keys],
                value=dimension_keys[0],
                style={"width": "100%"}
            )
        ])
    elif plot_type == "2d" and len(dimension_keys) >= 2:
        # Two dimensions: x and y
        return html.Div([
            html.Label("X-axis:"),
            dcc.Dropdown(
                id='dim1',
                options=[{"label": k, "value": k} for k in dimension_keys],
                value=dimension_keys[0],
                style={"width": "100%"}
            ),
            html.Br(),
            html.Label("Y-axis:"),
            dcc.Dropdown(
                id='dim2',
                options=[{"label": k, "value": k} for k in dimension_keys],
                value=dimension_keys[1],
                style={"width": "100%"}
            )
        ])
    elif plot_type == "3d" and len(dimension_keys) >= 3:
        # Three dimensions: x, y, and z
        return html.Div([
            html.Label("X-axis:"),
            dcc.Dropdown(
                id='dim1',
                options=[{"label": k, "value": k} for k in dimension_keys],
                value=dimension_keys[0]
            ),
            html.Br(),
            html.Label("Y-axis:"),
            dcc.Dropdown(
                id='dim2',
                options=[{"label": k, "value": k} for k in dimension_keys if k != dimension_keys[0]],
                value=dimension_keys[1]
            ),
            html.Br(),
            html.Label("Z-axis:"),
            dcc.Dropdown(
                id='dim3',
                options=[{"label": k, "value": k} for k in dimension_keys if k not in [dimension_keys[0], dimension_keys[1]]],
                value=dimension_keys[2]
            )
        ])
    else:
        return html.Div(children=[html.H1("This plot type is not supported for this number of dimensions")])


@app.callback(
    Output('main-graph', 'figure'),
    Input('plot-type', 'value'),
    Input('dim1', 'value'),
    Input('dim2', 'value'),
    Input('dim3', 'value')
)
def update_figure(plot_type, dim1, dim2, dim3):
    if plot_type == "1d" and dim1:
        # 1D: We plot latency vs dim1
        # We might need to aggregate if there are multiple latency values for the same dim1.
        # Let's just average latency by dim1:
        grouped = df.groupby(dim1, as_index=False).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=grouped[dim1], y=grouped["latency"], mode='lines+markers'))
        fig.update_layout(
            title=f"Average Latency vs {dim1}",
            xaxis_title=dim1,
            yaxis_title="Latency"
        )
        return fig

    elif plot_type == "2d" and dim1 and dim2:
        # 2D heatmap: dim1 on x-axis, dim2 on y-axis, latency as color
        # We pivot the table:
        pivoted = df.pivot_table(index=dim2, columns=dim1, values='latency', aggfunc='mean')
        fig = go.Figure(data=go.Heatmap(
            z=pivoted.values,
            x=pivoted.columns,
            y=pivoted.index,
            colorscale='Viridis'
        ))
        fig.update_layout(
            title=f"Average Latency Heatmap ({dim1} vs {dim2})",
            xaxis_title=dim1,
            yaxis_title=dim2
        )
        return fig

    elif plot_type == "3d" and dim1 and dim2 and dim3:
        # 3D surface: dim1 = x, dim2 = y, dim3 = z (latency)
        # Pivot the table:
        pivoted = df.pivot_table(index=dim2, columns=dim1, values='latency', aggfunc='mean')
        X = pivoted.columns
        Y = pivoted.index
        Z = pivoted.values

        fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z, colorscale='Viridis')])
        fig.update_layout(
            title=f"Average Latency Surface ({dim1}, {dim2}, {dim3})",
            scene = dict(
                xaxis_title=dim1,
                yaxis_title=dim2,
                zaxis_title='Latency'
            )
        )
        return fig

    else:
        # Return an empty figure or a message indicating missing parameters
        fig = go.Figure()
        fig.update_layout(
            title="Please select the necessary dimensions for the selected plot type."
        )
        return fig


if __name__ == '__main__':
    app.run_server(debug=True)