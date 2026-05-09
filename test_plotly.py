import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=[1, 2, 3], y=[4000, 15000, 27000],
    mode='lines', name='Nasdaq',
    line=dict(color='blue'),
    yaxis='y'
))

fig.add_trace(go.Scatter(
    x=[1, 2, 3], y=[10, 40, 80],
    mode='lines', name='VIX',
    line=dict(color='red'),
    yaxis='y2'
))

fig.update_layout(
    yaxis=dict(
        title='Left',
        side='left',
        tickfont=dict(color='blue')
    ),
    yaxis2=dict(
        title='Right',
        side='right',
        overlaying='y',
        tickfont=dict(color='red')
    )
)

fig.write_html('test_chart.html')
