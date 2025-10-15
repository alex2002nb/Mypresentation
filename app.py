# app.py
import pandas as pd
from dash import Dash, html, dcc, Output, Input
import plotly.express as px

# === 1. Cargar datos ===
df = pd.read_csv("Datos exposicion.csv")

# Asegurar formato de fecha
df["invoice_date"] = pd.to_datetime(df["invoice_date"], dayfirst=True)

# === 2. Inicializar aplicación ===
app = Dash(__name__)
server = app.server  # necesario para Render

# === 3. Layout ===
app.layout = html.Div([
    html.H1("📊 Dashboard de Ventas en Centros Comerciales", style={'textAlign': 'center'}),
    html.P("Analiza los patrones de compra por edad, género, categoría y método de pago."),

    # --- Filtros principales ---
    html.Div([
        html.Div([
            html.Label("Centro Comercial:"),
            dcc.Dropdown(
                options=[{'label': m, 'value': m} for m in df["shopping_mall"].unique()],
                id="mall-filter",
                value=df["shopping_mall"].unique()[0],
                clearable=False
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),

        html.Div([
            html.Label("Rango de Fechas:"),
            dcc.DatePickerRange(
                id='date-range',
                start_date=df["invoice_date"].min(),
                end_date=df["invoice_date"].max(),
                display_format='DD/MM/YYYY'
            )
        ], style={'width': '40%', 'display': 'inline-block'}),
    ], style={'marginBottom': '30px'}),

    # --- Botón para cambiar tipo de gráfico ---
    html.Div([
        html.Label("Cambiar tipo de gráfico (Categorías más vendidas):"),
        dcc.RadioItems(
            id="chart-type",
            options=[
                {"label": "Barras", "value": "bar"},
                {"label": "Pastel", "value": "pie"}
            ],
            value="bar",
            inline=True
        )
    ], style={'marginBottom': '20px'}),

    # === 4. Cuadrícula de gráficos 2x2 ===
    html.Div([
        html.Div([dcc.Graph(id='ventas-tiempo')], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='categorias')], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='genero-edad')], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='metodos-pago')], style={'width': '48%', 'display': 'inline-block'}),
    ])
])

# === 5. Callbacks ===

# Gráfico 1: Línea temporal con barra deslizante y selector de rango
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
    return fig

# Gráfico 2: Categorías más vendidas (tipo cambia con botón)
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
    return fig

# Gráfico 3: Dispersión edad vs gasto promedio
@app.callback(
    Output('genero-edad', 'figure'),
    Input('mall-filter', 'value')
)
def actualizar_dispersion(mall):
    dff = df[df["shopping_mall"] == mall]
    gasto_prom = dff.groupby(["age", "gender"])["price"].mean().reset_index()
    fig = px.scatter(gasto_prom, x="age", y="price", color="gender", title="Relación Edad - Gasto Promedio")
    return fig

# Gráfico 4: Métodos de pago
@app.callback(
    Output('metodos-pago', 'figure'),
    Input('mall-filter', 'value')
)
def actualizar_pago(mall):
    dff = df[df["shopping_mall"] == mall]
    resumen = dff["payment_method"].value_counts().reset_index()
    resumen.columns = ["Método de Pago", "Cantidad"]
    fig = px.bar(resumen, x="Método de Pago", y="Cantidad", title="Uso de Métodos de Pago")
    return fig


# === 6. Ejecutar ===
if __name__ == "__main__":
    app.run(debug=False)