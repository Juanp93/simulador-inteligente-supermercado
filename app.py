import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import google.generativeai as genai

# ==============================================================================
# CONFIGURACIÓN Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="IntelRetail Pro - Sistema de Decisiones", layout="wide", page_icon="📈")

st.markdown("""
<style>
    .metric-container { background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid #636EFA; margin-bottom: 15px; }
    .metric-success { border-left: 5px solid #00CC96; }
    .metric-warning { border-left: 5px solid #FFA15A; }
    .metric-danger { border-left: 5px solid #EF553B; }
    .metric-title { font-size: 13px; color: #A3A3A3; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 22px; color: #FFFFFF; font-weight: bold; margin-top: 5px; }
    .metric-caption { font-size: 12px; color: #858585; margin-top: 4px; }
    .home-card { background-color: #1a1c24; border: 1px solid #2d3139; border-radius: 12px; padding: 25px; margin-bottom: 20px; text-align: center; }
    .home-card h3 { color: #ffffff; margin-bottom: 10px; font-size: 18px; }
    .home-card p { color: #a0aec0; font-size: 14px; margin-bottom: 20px; min-height: 40px; }
    div[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

if "pantalla_actual" not in st.session_state: st.session_state.pantalla_actual = "home"
if "historial_chat" not in st.session_state: st.session_state.historial_chat = []

def cambiar_pantalla(nombre): st.session_state.pantalla_actual = nombre

# ==============================================================================
# NAVEGACIÓN Y MONEDA (BARRA LATERAL)
# ==============================================================================
st.sidebar.title("🧭 Navegación")
if st.sidebar.button("🏠 Inicio (Home)", use_container_width=True): cambiar_pantalla("home")
if st.sidebar.button("⚡ Diagnóstico Express", use_container_width=True): cambiar_pantalla("express")
if st.sidebar.button("🔍 Auditoría de Catálogo", use_container_width=True): cambiar_pantalla("diagnostico")
if st.sidebar.button("🎛️ Simulador y Pauta IA", use_container_width=True): cambiar_pantalla("simulador")
if st.sidebar.button("🎯 Planificador Metas", use_container_width=True): cambiar_pantalla("objetivos")

st.sidebar.markdown("---")
st.sidebar.header("💱 Moneda Global")
selector_moneda = st.sidebar.selectbox("Divisa:", ["COP (Pesos Colombianos)", "USD (Dólares)", "MXN (Pesos Mexicanos)"])

if selector_moneda == "COP (Pesos Colombianos)":
    m_factor = st.sidebar.number_input("Tasa de Cambio (1 USD = X COP):", min_value=100.0, value=4000.0, step=50.0)
    m_simbolo, m_sufijo = "$", " COP"
elif selector_moneda == "MXN (Pesos Mexicanos)":
    m_factor = st.sidebar.number_input("Tasa de Cambio (1 USD = X MXN):", min_value=1.0, value=18.5, step=0.5)
    m_simbolo, m_sufijo = "$", " MXN"
else:
    m_factor, m_simbolo, m_sufijo = 1.0, "$", " USD"

# ==============================================================================
# PROCESAMIENTO DE DATOS
# ==============================================================================
@st.cache_data
def generar_plantilla_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame({'Fecha': ['01/10/2026', '02/10/2026'], 'Producto': ['Producto A', 'Producto B'], 'Ventas': [100, 250], 'Cantidad': [2, 5], 'Cliente': ['Mostrador', 'Cliente VIP'], 'Costo Proveedor (%)': [60, 45]}).to_excel(writer, index=False)
    return output.getvalue()

@st.cache_data
def limpiar_y_preparar_datos(file_bytes, filename, costo_global, factor_divisa):
    buffer = io.BytesIO(file_bytes) if isinstance(file_bytes, bytes) else file_bytes
    try: df_temp = pd.read_excel(buffer) if filename.endswith('.xlsx') else pd.read_csv(buffer, encoding='utf-8')
    except: return pd.DataFrame()

    column_map = {}
    for col in df_temp.columns:
        c = str(col).strip().lower()
        if any(x in c for x in ['fecha', 'date']): column_map[col] = 'Order Date'
        elif any(x in c for x in ['venta', 'sales', 'monto']): column_map[col] = 'Sales'
        elif any(x in c for x in ['producto', 'product', 'sku']): column_map[col] = 'Product Name'
        elif any(x in c for x in ['cantidad', 'quantity', 'cant']): column_map[col] = 'Quantity'
        elif any(x in c for x in ['cliente', 'customer']): column_map[col] = 'Customer Name'
        elif any(x in c for x in ['costo', 'cost', 'margen']): column_map[col] = 'Costo_Porcentaje'
            
    df_temp = df_temp.rename(columns=column_map)
    if 'Sales' not in df_temp.columns: return pd.DataFrame()
    
    if 'Product Name' not in df_temp.columns: df_temp['Product Name'] = "Artículo General"
    if 'Customer Name' not in df_temp.columns: df_temp['Customer Name'] = "Mostrador"
    if 'Quantity' not in df_temp.columns: df_temp['Quantity'] = 1
    if 'Costo_Porcentaje' not in df_temp.columns: df_temp['Costo_Porcentaje'] = costo_global
        
    df_temp = df_temp.dropna(subset=['Sales'])
    df_temp['Sales'] = pd.to_numeric(df_temp['Sales'], errors='coerce') * factor_divisa
    df_temp['Quantity'] = pd.to_numeric(df_temp['Quantity'], errors='coerce').fillna(1)
    df_temp['Costo_Porcentaje'] = pd.to_numeric(df_temp['Costo_Porcentaje'], errors='coerce').fillna(costo_global)
    
    df_temp['Costo_Proveedor'] = df_temp['Sales'] * (df_temp['Costo_Porcentaje'] / 100)
    df_temp['Ganancia_Neta'] = df_temp['Sales'] - df_temp['Costo_Proveedor']
    
    if 'Order Date' in df_temp.columns: df_temp['Order Date'] = pd.to_datetime(df_temp['Order Date'], format='%d/%m/%Y', errors='coerce')
    else: df_temp['Order Date'] = pd.Timestamp.now()
    return df_temp

def analizar_datos(df):
    df_g = df.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
    df_g['Precio_Medio'] = df_g['Sales'] / df_g['Quantity']
    df['Dia'] = df['Order Date'].dt.day_name().map({'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}).fillna('N/A')
    
    df_p = df_g.sort_values('Sales', ascending=False)
    df_p['Pct'] = (df_p['Sales'].cumsum() / df_p['Sales'].sum()) * 100
    
    return {
        "estrella": df_g.loc[df_g['Ganancia_Neta'].idxmax()]['Product Name'], "ganancia_estrella": df_g['Ganancia_Neta'].max(),
        "lider": df_g.loc[df_g['Quantity'].idxmax()]['Product Name'], "cant_lider": df_g['Quantity'].max(),
        "dormido": df_g.loc[df_g['Quantity'].idxmin()]['Product Name'], "cant_dormido": df_g['Quantity'].min(),
        "dia_dorado": df.groupby('Dia')['Sales'].sum().idxmax(), "ticket": df['Sales'].sum() / len(df),
        "clientes": df.groupby('Customer Name')['Sales'].sum().reset_index().sort_values('Sales', ascending=False).head(5),
        "df_agrupado": df_g, "total_skus": len(df_p), "pareto": max(1, len(df_p[df_p['Pct'] <= 80]))
    }

# ==============================================================================
# CARGA DE DATOS EN PANTALLAS ESPECÍFICAS
# ==============================================================================
df_app = pd.DataFrame()
costo_base = 70

if st.session_state.pantalla_actual in ["diagnostico", "simulador", "objetivos"]:
    st.sidebar.markdown("---")
    st.sidebar.header("📁 Ingesta de Datos")
    st.sidebar.download_button("📥 Plantilla Avanzada (Costos)", generar_plantilla_excel(), "plantilla.xlsx")
    archivo = st.sidebar.file_uploader("Sube tu archivo de ventas:", type=['csv', 'xlsx'])
    costo_base = st.sidebar.slider("Costo Global por Defecto (%)", 10, 90, 70, 5, help="Se usará si tu archivo no trae la columna de costos.")

    if archivo: df_app = limpiar_y_preparar_datos(archivo.getvalue(), archivo.name, costo_base, m_factor)
    else:
        try:
            with open('train.csv', 'rb') as f: df_app = limpiar_y_preparar_datos(f.read(), 'train.csv', costo_base, m_factor)
        except: pass

if not df_app.empty: analisis = analizar_datos(df_app)

# ==============================================================================
# PANTALLAS PRINCIPALES
# ==============================================================================
if st.session_state.pantalla_actual == "home":
    st.title("🚀 Bienvenido a IntelRetail Pro")
    st.markdown("#### *Tu copiloto estratégico de inteligencia comercial.*")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="home-card"><h3>⚡ Diagnóstico Express</h3><p>Calcula tu punto de equilibrio sin necesidad de archivos.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Diagnóstico", use_container_width=True, type="primary"): cambiar_pantalla("express"); st.rerun()
        st.markdown('<div class="home-card"><h3>🎛️ Simulador e IA</h3><p>Proyecta escenarios y chatea con tus datos usando Gemini AI.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Simulador", use_container_width=True): cambiar_pantalla("simulador"); st.rerun()
    with c2:
        st.markdown('<div class="home-card"><h3>🔍 Auditoría de Catálogo</h3><p>Descubre tu producto estrella, Pareto y matriz BCG.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Auditoría", use_container_width=True): cambiar_pantalla("diagnostico"); st.rerun()
        st.markdown('<div class="home-card"><h3>🎯 Planificador Metas</h3><p>Calcula tus proyecciones a múltiples meses.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Planificador", use_container_width=True): cambiar_pantalla("objetivos"); st.rerun()

# ------------------------------------------------------------------------------
# 1. DIAGNÓSTICO EXPRESS (RESTAURADO)
# ------------------------------------------------------------------------------
elif st.session_state.pantalla_actual == "express":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("⚡ Diagnóstico Rápido para Micro-Comercios")
    st.markdown("Ingresa tus estimados para obtener una radiografía financiera instantánea sin cargar archivos.")
    
    c1, c2 = st.columns(2)
    with c1:
        venta = st.number_input(f"Venta mensual estimada ({m_sufijo}):", value=5000000.0)
        margen = st.slider("Margen de ganancia (%):", 5, 80, 30)
    with c2:
        gastos = st.number_input(f"Gastos fijos ({m_sufijo}):", value=1200000.0)
        clientes = st.number_input("Clientes al mes:", value=350)
    
    utilidad = (venta * (margen / 100)) - gastos
    punto_eq = gastos / (margen / 100) if margen > 0 else 0
    ticket = venta / clientes if clientes > 0 else 0
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container {"metric-success" if utilidad > 0 else "metric-danger"}"><div class="metric-title">UTILIDAD NETA</div><div class="metric-value">{m_simbolo}{utilidad:,.2f}</div><div class="metric-caption">Ganancia real descontando gastos fijos.</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">PUNTO DE EQUILIBRIO</div><div class="metric-value">{m_simbolo}{punto_eq:,.2f}</div><div class="metric-caption">Venta mínima requerida para no perder dinero.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO</div><div class="metric-value">{m_simbolo}{ticket:,.2f}</div><div class="metric-caption">Lo que gasta cada cliente en promedio.</div></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. AUDITORÍA Y BI (RESTAURADO TEXTOS Y GRÁFICOS)
# ------------------------------------------------------------------------------
elif st.session_state.pantalla_actual == "diagnostico":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("📊 Auditoría y BI de Catálogo")
    if df_app.empty: st.warning("Carga tus datos en el menú lateral.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-container"><div class="metric-title">🏆 ESTRELLA (MÁXIMA UTILIDAD)</div><div class="metric-value">{m_simbolo}{analisis["ganancia_estrella"]:,.2f}</div><div class="metric-caption"><b>{analisis["estrella"]}</b><br>El producto que más dinero real deja en caja.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">🥇 LÍDER EN ROTACIÓN</div><div class="metric-value">{analisis["cant_lider"]} Unds</div><div class="metric-caption"><b>{analisis["lider"]}</b><br>El producto que más cantidad de veces se vende.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">🛒 TICKET PROMEDIO</div><div class="metric-value">{m_simbolo}{analisis["ticket"]:,.2f}</div><div class="metric-caption">Monto medio facturado por cada orden de compra.</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-container metric-danger"><div class="metric-title">💤 DORMIDO (RIESGO DE INVENTARIO)</div><div class="metric-value">{analisis["cant_dormido"]} Unds</div><div class="metric-caption"><b>{analisis["dormido"]}</b><br>Baja rotación. Riesgo de dinero inmovilizado.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">🗓️ DÍA DORADO</div><div class="metric-value">Cada {analisis["dia_dorado"]}</div><div class="metric-caption">Día de la semana con mayor pico de ingresos.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">📐 LEY DE PARETO (80/20)</div><div class="metric-value">{analisis["pareto"]} de {analisis["total_skus"]} Productos</div><div class="metric-caption">Estos pocos SKUs generan el 80% de tus ventas totales.</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🎯 Matriz BCG: Posición Estratégica del Catálogo")
        st.plotly_chart(px.scatter(analisis['df_agrupado'], x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name', hover_name='Product Name', labels={'Quantity': 'Unidades Vendidas', 'Ganancia_Neta': 'Ganancia Neta'}, height=380).update_layout(showlegend=False), use_container_width=True)
        
        st.markdown("---")
        st.subheader("👥 Concentración de Ventas: Top 5 Clientes de Mayor Valor")
        st.plotly_chart(px.bar(analisis['clientes'], x='Sales', y='Customer Name', orientation='h', color='Sales', color_continuous_scale='Blues', labels={'Sales': 'Total Facturado', 'Customer Name': 'Cliente'}).update_layout(height=300, showlegend=False, yaxis=dict(autorange="reversed")), use_container_width=True)

# ------------------------------------------------------------------------------
# 3. SIMULADOR Y CHATBOT (MEJORADO CON ETIQUETAS Y SLIDERS AGRUPADOS)
# ------------------------------------------------------------------------------
elif st.session_state.pantalla_actual == "simulador":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎛️ Simulador Financiero y Asesor IA")
    
    if df_app.empty: st.warning("Carga tus datos en el menú lateral.")
    else:
        st.markdown("### Ajusta tus palancas comerciales:")
        c1, c2, c3 = st.columns(3)
        precio = c1.slider("1. Ajuste de Precios (%)", -50, 100, 0, help="Simula descuentos o incrementos masivos de precios.")
        pauta = c2.slider("2. Presupuesto Pauta", 0, int(5000 * m_factor), 0, int(100 * m_factor))
        costo_sim = c3.slider("3. Costo Operativo Simulado (%)", 10, 90, costo_base)
        
        factor_precio = 1 + (precio / 100)
        factor_cantidad = 1 - (precio / 100 * 0.5) 
        cl_n = int((pauta * 2.0) / (3 * m_factor)) if pauta < (20 * m_factor) else int(((pauta * 0.35 * 3.5) + (pauta * 0.30 * 3.0) + (pauta * 0.20 * 2.5) + (pauta * 0.15 * 2.0)) / (4 * m_factor))
        
        precio_m = df_app['Sales'].mean() / df_app['Quantity'].mean()
        v_sim = (df_app['Sales'] * factor_precio * factor_cantidad).sum() + ((cl_n * 1.5) * precio_m * factor_precio)
        c_sim = (df_app['Sales'] * (costo_sim/100) * factor_cantidad).sum() + ((cl_n * 1.5) * precio_m * (costo_sim/100))
        g_sim = v_sim - c_sim - pauta
        
        fig = go.Figure(data=[
            go.Bar(name='Histórico', x=['Ventas Totales', 'Ganancia Neta'], y=[df_app['Sales'].sum(), df_app['Ganancia_Neta'].sum()], marker_color='#636EFA', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside'),
            go.Bar(name='Proyectado', x=['Ventas Totales', 'Ganancia Neta'], y=[v_sim, g_sim], marker_color='#00CC96', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside')
        ])
        fig.update_layout(barmode='group', height=400, margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("🤖 Chatbot Analista: Pregúntale a tus Datos (Gemini IA)")
        st.markdown("La IA lee tu tabla de ventas. Pregúntale: *'¿Cuál es mi producto con mayor margen?'* o *'Escribe 2 copys para mi mejor producto'*.")
        
        api_key = None
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            api_key = st.text_input("Ingresa tu API Key de Gemini para chatear:", type="password")
        
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3.6-flash')
            
            for msg in st.session_state.historial_chat:
                with st.chat_message(msg["role"]): st.write(msg["content"])
            
            pregunta = st.chat_input("Escribe tu pregunta aquí...")
            if pregunta:
                st.session_state.historial_chat.append({"role": "user", "content": pregunta})
                with st.chat_message("user"): st.write(pregunta)
                
                contexto = f"Datos del negocio:\n{analisis['df_agrupado'][['Product Name', 'Quantity', 'Sales', 'Ganancia_Neta', 'Precio_Medio']].to_string(index=False)}\n\nResponde de forma concisa y como experto a: {pregunta}"
                
                with st.chat_message("assistant"):
                    with st.spinner("Analizando con Gemini 3.6 Flash..."):
                        try:
                            respuesta = model.generate_content(contexto)
                            st.write(respuesta.text)
                            st.session_state.historial_chat.append({"role": "assistant", "content": respuesta.text})
                        except Exception as e: 
                            st.error(f"Error de API: {e}")
        else: 
            st.info("⚠️ Configura la clave 'GEMINI_API_KEY' en los Secrets de Streamlit para activar el chat.")

# ------------------------------------------------------------------------------
# 4. PLANIFICADOR DE METAS (RESTAURADO Y MULTI-MES)
# ------------------------------------------------------------------------------
elif st.session_state.pantalla_actual == "objetivos":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎯 Planificador Estratégico por Objetivos")
    st.markdown("Define tu meta financiera y en cuánto tiempo quieres lograrla. El sistema calculará tu ruta diaria.")
    
    c1, c2, c3 = st.columns(3)
    with c1: meta = st.number_input(f"Ganancia Neta Deseada ({m_sufijo}):", value=10000000.0, step=500000.0)
    with c2: meses = st.slider("Horizonte de Tiempo (Meses):", 1, 12, 1)
    with c3: gastos = st.number_input(f"Gastos Fijos Mensuales ({m_sufijo}):", value=1500000.0, step=100000.0)
    
    gastos_totales = gastos * meses
    margen_comercial = (100 - costo_base) / 100
    ventas_totales_req = (meta + gastos_totales) / margen_comercial if margen_comercial > 0 else 0
    ventas_diarias_req = ventas_totales_req / (30 * meses)
    
    t_prom = analisis['ticket'] if not df_app.empty else (ventas_totales_req / (300 * meses))
    clientes_diarios = int(np.ceil(ventas_diarias_req / t_prom)) if t_prom > 0 else 0
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container metric-success"><div class="metric-title">FACTURACIÓN TOTAL REQUERIDA</div><div class="metric-value">{m_simbolo}{ventas_totales_req:,.2f}</div><div class="metric-caption">Ventas brutas necesarias en {meses} mes(es).</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container"><div class="metric-title">META DE VENTA DIARIA</div><div class="metric-value">{m_simbolo}{ventas_diarias_req:,.2f}</div><div class="metric-caption">Venta mínima promedio cada día.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">CLIENTES DIARIOS</div><div class="metric-value">{clientes_diarios} Compras/Día</div><div class="metric-caption">Basado en tu ticket promedio actual.</div></div>', unsafe_allow_html=True)
