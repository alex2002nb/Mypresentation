# app.py
import pandas as pd
from dash import Dash, html, dcc, Output, Input
import plotly.express as px

# === 1. Cargar datos ===
df = pd.read_csv("Datos exposicion.csv")
df["invoice_date"] = pd.to_datetime(df["invoice_date"], dayfirst=True)

# === 2. Inicializar aplicación ===
app = Dash(__name__)
server = app.server  # necesario para Render

# === 3. Layout ===
app.layout = html.Div([
    # --- Encabezado principal ---
    html.Div([
        html.H1("📊 Dashboard de Ventas en Centros Comerciales",
                style={'textAlign': 'center',
                       'color': '#1E3A8A',
                       'fontWeight': 'bold',
                       'marginBottom': '5px'}),
        html.P("Analiza los patrones de compra por edad, género, categoría y método de pago.",
               style={'textAlign': 'center', 'color': '#374151', 'fontSize': '16px'})
    ], style={'marginBottom': '25px'}),

    # --- Sección de filtros y controles ---
    html.Div([
        # Dropdown y fecha alineados lado a lado
        html.Div([
            html.Label("🏬 Centro Comercial:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                options=[{'label': m, 'value': m} for m in df["shopping_mall"].unique()],
                id="mall-filter",
                value=df["shopping_mall"].unique()[0],
                clearable=False,
                style={'backgroundColor': 'white'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '30px'}),

        html.Div([
            html.Label("📅 Rango de Fechas:", style={'fontWeight': 'bold'}),
            dcc.DatePickerRange(
                id='date-range',
                start_date=df["invoice_date"].min(),
                end_date=df["invoice_date"].max(),
                display_format='DD/MM/YYYY',
                style={'marginTop': '4px'}
            )
        ], style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    # --- Selector tipo de gráfico ---
    html.Div([
        html.Label("🧭 Cambiar tipo de gráfico (Categorías más vendidas):",
                   style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.RadioItems(
            id="chart-type",
            options=[
                {"label": "Barras", "value": "bar"},
                {"label": "Pastel", "value": "pie"}
            ],
            value="bar",
            inline=True
        )
    ], style={'textAlign': 'center', 'marginBottom': '30px'}),

    # === 4. Cuadrícula de gráficos 2x2 ===
    html.Div([
        html.Div([dcc.Graph(id='ventas-tiempo')],
                 style={'width': '48%', 'display': 'inline-block', 'margin': '1%', 'backgroundColor': 'white',
                        'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'}),

        html.Div([dcc.Graph(id='categorias')],
                 style={'width': '48%', 'display': 'inline-block', 'margin': '1%', 'backgroundColor': 'white',
                        'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'}),

        html.Div([dcc.Graph(id='genero-edad')],
                 style={'width': '48%', 'display': 'inline-block', 'margin': '1%', 'backgroundColor': 'white',
                        'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'}),

        html.Div([dcc.Graph(id='metodos-pago')],
                 style={'width': '48%', 'display': 'inline-block', 'margin': '1%', 'backgroundColor': 'white',
                        'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'}),
    ], style={'backgroundColor': '#F9FAFB', 'padding': '20px', 'borderRadius': '12px'})
])

# === 5. Callbacks ===
@app.callback(
    Output('ventas-tiempo', 'figure'),
    Input('mall-filter', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def actualizar_linea(mall, start, end):
    dff = df[(df["shopping_mall"] == mall) &
             (df["invoice_date"] >= start) &
             (df["invoice_date"] <= end)]
    ventas_mensuales = dff.groupby(pd.Grouper(key="invoice_date", freq="M"))["price"].sum().reset_index()
    fig = px.line(ventas_mensuales, x="invoice_date", y="price", title="Ventas Mensuales", markers=True)
    fig.update_xaxes(rangeslider_visible=True, rangeselector=dict(
        buttons=[
            dict(count=3, label="3M", step="month", stepmode="backward"),
            dict(count=6, label="6M", step="month", stepmode="backward"),
            dict(count=12, label="1Y", step="month", stepmode="backward"),
            dict(step="all")
        ]
    ))
    fig.update_layout(template="plotly_white", title_x=0.5)
    return fig


@app.callback(
    Output('categorias', 'figure'),
    Input('chart-type', 'value'),
    Input('mall-filter', 'value')
)
def actualizar_categorias(chart_type, mall):
    dff = df[df["shopping_mall"] == mall]
    resumen = dff.groupby("category")["quantity"].sum().reset_index()
    if chart_type == "bar":
        fig = px.bar(resumen, x="category", y="quantity", title="Categorías más vendidas")
    else:
        fig = px.pie(resumen, names="category", values="quantity", title="Participación por categoría")
    fig.update_layout(template="plotly_white", title_x=0.5)
    return fig


@app.callback(
    Output('genero-edad', 'figure'),
    Input('mall-filter', 'value')
)
def actualizar_dispersion(mall):
    dff = df[df["shopping_mall"] == mall]
    gasto_prom = dff.groupby(["age", "gender"])["price"].mean().reset_index()
    fig = px.scatter(gasto_prom, x="age", y="price", color="gender", title="Relación Edad - Gasto Promedio")
    fig.update_layout(template="plotly_white", title_x=0.5)
    return fig


@app.callback(
    Output('metodos-pago', 'figure'),
    Input('mall-filter', 'value')
)
def actualizar_pago(mall):
    dff = df[df["shopping_mall"] == mall]
    resumen = dff["payment_method"].value_counts().reset_index()
    resumen.columns = ["Método de Pago", "Cantidad"]
    fig = px.bar(resumen, x="Método de Pago", y="Cantidad", title="Uso de Métodos de Pago")
    fig.update_layout(template="plotly_white", title_x=0.5)
    return fig


# === 6. Ejecutar ===
if __name__ == "__main__":
    app.run(debug=False)