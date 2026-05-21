import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CARGAR Y PREPARAR DATOS
# ==========================================
print("Cargando datos de los 3 tipos de sensores...")

df_co2 = pd.read_csv('patios_co2.csv')
df_wifi = pd.read_csv('patios_wifi.csv')
df_puertas = pd.read_csv('patios_puertas.csv')

# Formatear fechas y agrupar por horas
for df in [df_co2, df_wifi, df_puertas]:
    if not df.empty:
        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
        df['hora'] = df['fecha_hora'].dt.floor('H')

# Mapeo de Sensores de CO2 (del Word)
mapa_co2 = {
    'atd-airsense007': 'San Basilio, 16',
    'atd-airsense008': 'Martín Roa, 9',
    'atd-airsense002': 'Duartas, 2',
    'atd-airsense003': 'Postrera, 51 (Pta. Sevilla)',
    'atd-airsense010': 'Zarco, 15',
    'atd-airsense004': 'Parras, 5',
    'atd-airsense009': 'Marroquíes, 6'
}

if not df_co2.empty:
    df_co2['Ubicacion'] = df_co2['entity_id'].map(mapa_co2).fillna(df_co2['entity_id'])

# Para puertas y wifi usamos el ID temporalmente (si el tutor te da los nombres de las calles para estos, los podemos mapear igual)
if not df_puertas.empty:
    df_puertas['Ubicacion'] = df_puertas['entity_id'] 

if not df_wifi.empty:
    df_wifi['Ubicacion'] = df_wifi['entity_id']

# ==========================================
# 2. INICIALIZAR LA APLICACIÓN
# ==========================================
app = dash.Dash(__name__)
server = app.server
app.title = "Córdoba Patios - Smart City"

# ==========================================
# 3. DISEÑO DE LA INTERFAZ
# ==========================================
app.layout = html.Div(children=[
    
    html.Div(className='header-container', children=[
        html.H2("Análisis IoT: Festival de los Patios 2021", className='header-title'),
        html.P("Monitorización completa: Ambiental, Aforo Físico y Conectividad", className='header-subtitle')
    ]),

    dcc.Tabs(id="tabs-patios", value='tab-co2', children=[
        
        # PESTAÑA 1: CO2
        dcc.Tab(label='💨 Calidad del Aire (CO2)', value='tab-co2', children=[
            html.Div(style={'marginTop': '20px'}, className='row-container', children=[
                html.Div(className='card col-filtros', children=[
                    html.Label("Seleccionar Patio:", className='control-label'),
                    dcc.Dropdown(id='filtro-co2', options=[{'label': loc, 'value': loc} for loc in df_co2['Ubicacion'].unique()], value=['San Basilio, 16'] if not df_co2.empty else [], multi=True)
                ]),
            ]),
            html.Div(className='card card-grafica', children=[dcc.Graph(id='grafica-co2', style={'height': '500px'})])
        ]),

        # PESTAÑA 2: PUERTAS (ENTRADAS Y SALIDAS)
        dcc.Tab(label='🚪 Aforo (Entradas y Salidas)', value='tab-puertas', children=[
            html.Div(style={'marginTop': '20px'}, className='row-container', children=[
                html.Div(className='card col-filtros', children=[
                    html.Label("Seleccionar Sensor de Puerta:", className='control-label'),
                    dcc.Dropdown(id='filtro-puertas', options=[{'label': loc, 'value': loc} for loc in df_puertas['Ubicacion'].unique()] if not df_puertas.empty else [], value=[df_puertas['Ubicacion'].iloc[0]] if not df_puertas.empty else [], multi=True)
                ]),
            ]),
            html.Div(className='card card-grafica', children=[dcc.Graph(id='grafica-puertas', style={'height': '500px'})])
        ]),

        # PESTAÑA 3: CONEXIONES WI-FI EXTERIORES
        dcc.Tab(label='📱 Afluencia Exterior (Wi-Fi)', value='tab-wifi', children=[
            html.Div(style={'marginTop': '20px'}, className='row-container', children=[
                html.Div(className='card col-filtros', children=[
                    html.Label("Seleccionar Sensor Exterior:", className='control-label'),
                    dcc.Dropdown(id='filtro-wifi', options=[{'label': loc, 'value': loc} for loc in df_wifi['Ubicacion'].unique()] if not df_wifi.empty else [], value=[df_wifi['Ubicacion'].iloc[0]] if not df_wifi.empty else [], multi=True)
                ]),
            ]),
            html.Div(className='card card-grafica', children=[dcc.Graph(id='grafica-wifi', style={'height': '500px'})])
        ])
    ])
])

# ==========================================
# 4. CALLBACKS
# ==========================================

# 1. CO2
@app.callback(Output('grafica-co2', 'figure'), [Input('filtro-co2', 'value')])
def update_co2(seleccion):
    if not seleccion or df_co2.empty: return px.line(title="Sin datos.")
    df_plot = df_co2[df_co2['Ubicacion'].isin(seleccion)].groupby(['hora', 'Ubicacion'])['co2'].mean().reset_index()
    fig = px.line(df_plot, x='hora', y='co2', color='Ubicacion', line_shape='spline', color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_traces(fill='tozeroy', mode='lines', line=dict(width=3))
    fig.add_hline(y=1000, line_dash="dash", line_color="#ef4444", annotation_text="Límite OMS (1000 ppm)", annotation_position="top left")
    fig.update_layout(title="Evolución de CO2", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified", margin=dict(l=40, r=40, t=60, b=40), xaxis=dict(showgrid=True, gridcolor='#e2e8f0', griddash='dash'), yaxis=dict(showgrid=True, gridcolor='#e2e8f0', griddash='dash'))
    return fig

# 2. PUERTAS (Aforo)
@app.callback(Output('grafica-puertas', 'figure'), [Input('filtro-puertas', 'value')])
def update_puertas(seleccion):
    if not seleccion or df_puertas.empty: return px.line(title="Sin datos.")
    df_plot = df_puertas[df_puertas['Ubicacion'].isin(seleccion)]
    if 'total_counter_a' in df_plot.columns:
        df_plot = df_plot.groupby(['hora', 'Ubicacion'])['total_counter_a'].max().reset_index()
    fig = px.line(df_plot, x='hora', y='total_counter_a', color='Ubicacion', line_shape='spline', color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_traces(fill='tozeroy', mode='lines', line=dict(width=3))
    fig.update_layout(title="Control de Accesos (Entradas Acumuladas)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified", margin=dict(l=40, r=40, t=60, b=40), xaxis=dict(showgrid=True, gridcolor='#e2e8f0', griddash='dash'), yaxis=dict(showgrid=True, gridcolor='#e2e8f0', griddash='dash', title="Personas Acumuladas"))
    return fig

# 3. WI-FI
@app.callback(Output('grafica-wifi', 'figure'), [Input('filtro-wifi', 'value')])
def update_wifi(seleccion):
    if not seleccion or df_wifi.empty: return px.line(title="Sin datos.")
    df_plot = df_wifi[df_wifi['Ubicacion'].isin(seleccion)].groupby(['hora', 'Ubicacion'])['wifi'].mean().reset_index()
    fig = px.line(df_plot, x='hora', y='wifi', color='Ubicacion', line_shape='spline', color_discrete_sequence=px.colors.qualitative.Prism)
    fig.update_traces(fill='tozeroy', mode='lines', line=dict(width=3))
    fig.update_layout(title="Afluencia Exterior (Detecciones Wi-Fi Promedio)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified", margin=dict(l=40, r=40, t=60, b=40), xaxis=dict(showgrid=True, gridcolor='#e2e8f0', griddash='dash'), yaxis=dict(showgrid=True, gridcolor='#e2e8f0', griddash='dash', title="Conexiones Promedio"))
    return fig

if __name__ == '__main__':
    app.run(debug=True)