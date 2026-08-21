import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import google.generativeai as genai

# ==============================================================================
# 1. CONFIGURACIÓN, MEMORIA Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="IntelRetail Pro", layout="wide", page_icon="📈")

if "pantalla_actual" not in st.session_state: st.session_state.pantalla_actual = "home"
if "historial_chat" not in st.session_state: st.session_state.historial_chat = []
if "df_bruto" not in st.session_state: st.session_state.df_bruto = pd.DataFrame()
if "costos_editados" not in st.session_state: st.session_state.costos_editados = pd.DataFrame()

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    modelo_ia = genai.GenerativeModel('gemini-3.6-flash')
    ia_activa = True
except:
    ia_activa = False

def cambiar_pantalla(nombre): st.session_state.pantalla_actual = nombre

@st.cache_data
def generar_plantilla_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame({'Fecha': ['01/10/2026', '02/10/2026'], 'Producto': ['Producto A', 'Producto B'], 'Ventas': [100, 250], 'Cantidad': [2, 5], 'Cliente': ['Mostrador', 'VIP']}).to_excel(writer, index=False)
    return output.getvalue()

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

# ==============================================================================
# 2. BARRA LATERAL (NAVEGACIÓN, DIVISAS, DATOS Y CHATBOT GLOBAL)
# ==============================================================================
with st.sidebar:
    st.title("🧭 Navegación")
    if st.button("🏠 Inicio", use_container_width=True): cambiar_pantalla("home")
    if st.button("⚡ Diagnóstico Express", use_container_width=True): cambiar_pantalla("express")
    if st.button("🔍 Auditoría de Catálogo", use_container_width=True): cambiar_pantalla("diagnostico")
    if st.button("🎛️ Simulador y Pauta IA", use_container_width=True): cambiar_pantalla("simulador")
    if st.button("🎯 Planificador Metas", use_container_width=True): cambiar_pantalla("objetivos")
    
    st.markdown("---")
    st.header("💱 Moneda Global")
    selector_moneda = st.selectbox("Divisa:", ["COP (Pesos Colombianos)", "USD (Dólares)", "MXN (Pesos Mexicanos)"])
    if selector_moneda == "COP (Pesos Colombianos)": m_factor, m_simbolo, m_sufijo = st.number_input("Tasa (1 USD = X COP):", 100.0, value=4000.0, step=50.0), "$", " COP"
    elif selector_moneda == "MXN (Pesos Mexicanos)": m_factor, m_simbolo, m_sufijo = st.number_input("Tasa (1 USD = X MXN):", 1.0, value=18.5, step=0.5), "$", " MXN"
    else: m_factor, m_simbolo, m_sufijo = 1.0, "$", " USD"

    st.markdown("---")
    st.header("📁 Ingesta de Datos")
    st.download_button("📥 Plantilla Avanzada", generar_plantilla_excel(), "plantilla.xlsx")
    costo_base = st.slider("Costo Global por Defecto (%)", 10, 90, 70, 5, help="Se usará como base para todos los productos.")
    archivo = st.file_uploader("Sube tus ventas:", type=['csv', 'xlsx'])
    
    if archivo:
        if archivo.name.endswith('.xlsx'): st.session_state.df_bruto = pd.read_excel(archivo)
        else: st.session_state.df_bruto = pd.read_csv(archivo)
        st.success("¡Datos en memoria!")

    st.markdown("---")
    st.header("💬 Asesor IA (Copiloto)")
    if not ia_activa:
        st.error("⚠️ Falta API Key en Secrets")
    else:
        for msg in st.session_state.historial_chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        pregunta = st.chat_input("Pregunta algo...")
        if pregunta:
            st.session_state.historial_chat.append({"role": "user", "content": pregunta})
            with st.chat_message("user"): st.write(pregunta)
            
            resumen_datos = st.session_state.df_bruto.head(10).to_string() if not st.session_state.df_bruto.empty else "Sin datos"
            prompt_experto = f"""
            Eres el Asesor IA de IntelRetail Pro. 
            Pantalla actual: {st.session_state.pantalla_actual}. Divisa: {selector_moneda}.
            Datos recientes: {resumen_datos}
            Instrucción vital: Analiza el nicho de los productos. Si detectas servicios de cuidado de animales, estética canina o accesorios para mascotas, enfatiza estrategias de marketing altamente visuales para redes sociales.
            Responde de forma comercial y experta a: {pregunta}
            """
            
            with st.chat_message("assistant"):
                with st.spinner("Analizando..."):
                    try:
                        respuesta = modelo_ia.generate_content(prompt_experto)
                        st.write(respuesta.text)
                        st.session_state.historial_chat.append({"role": "assistant", "content": respuesta.text})
                    except Exception as e: st.error("Error de conexión.")

# ==============================================================================
# 3. PROCESAMIENTO (CRUZANDO COSTO GLOBAL Y COSTOS INDIVIDUALES)
# ==============================================================================
df_final = pd.DataFrame()

if not st.session_state.df_bruto.empty:
    df_temp = st.session_state.df_bruto.copy()
    
    col_map = {}
    for col in df_temp.columns:
        c = str(col).strip().lower()
        if any(x in c for x in ['venta', 'sales', 'monto']): col_map[col] = 'Sales'
        elif any(x in c for x in ['producto', 'product', 'sku']): col_map[col] = 'Product Name'
        elif any(x in c for x in ['cantidad', 'quantity', 'cant']): col_map[col] = 'Quantity'
        elif any(x in c for x in ['cliente', 'customer']): col_map[col] = 'Customer Name'
            
    df_temp = df_temp.rename(columns=col_map)
    df_temp = df_temp.loc[:, ~df_temp.columns.duplicated()] 
    
    if 'Sales' in df_temp.columns:
        if 'Product Name' not in df_temp.columns: df_temp['Product Name'] = 'General'
        if 'Quantity' not in df_temp.columns: df_temp['Quantity'] = 1
        if 'Customer Name' not in df_temp.columns: df_temp['Customer Name'] = "Mostrador"
        
        df_temp['Sales'] = pd.to_numeric(df_temp['Sales'], errors='coerce').fillna(0) * m_factor
        df_temp['Quantity'] = pd.to_numeric(df_temp['Quantity'], errors='coerce').fillna(1)
        
        productos_unicos = df_temp['Product Name'].unique()
        # Si la tabla de costos está vacía, la llenamos usando el COSTO GLOBAL DEFINIDO EN LA BARRA LATERAL
        if st.session_state.costos_editados.empty or len(st.session_state.costos_editados) != len(productos_unicos):
            st.session_state.costos_editados = pd.DataFrame({'Product Name': productos_unicos, 'Costo (%)': [float(costo_base)]*len(productos_unicos)})
        
        df_final = pd.merge(df_temp, st.session_state.costos_editados, on='Product Name', how='left')
        df_final['Costo_Valor'] = df_final['Sales'] * (df_final['Costo (%)'] / 100)
        df_final['Ganancia_Neta'] = df_final['Sales'] - df_final['Costo_Valor']

# ==============================================================================
# 4. PANTALLAS
# ==============================================================================

if st.session_state.pantalla_actual == "home":
    st.title("🚀 Bienvenido a IntelRetail Pro")
    st.markdown("#### *Tu copiloto estratégico de inteligencia comercial.*")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="home-card"><h3>⚡ Diagnóstico Express</h3><p>Calcula tu punto de equilibrio sin necesidad de archivos.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Diagnóstico", use_container_width=True, type="primary"): cambiar_pantalla("express"); st.rerun()
        st.markdown('<div class="home-card"><h3>🎛️ Simulador e IA</h3><p>Proyecta escenarios y chatea con tus datos en la barra lateral.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Simulador", use_container_width=True): cambiar_pantalla("simulador"); st.rerun()
    with c2:
        st.markdown('<div class="home-card"><h3>🔍 Auditoría de Catálogo</h3><p>Define costos individuales, descubre tu estrella y Pareto.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Auditoría", use_container_width=True): cambiar_pantalla("diagnostico"); st.rerun()
        st.markdown('<div class="home-card"><h3>🎯 Planificador Metas</h3><p>Calcula tus proyecciones a múltiples meses.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Planificador", use_container_width=True): cambiar_pantalla("objetivos"); st.rerun()

elif st.session_state.pantalla_actual == "express":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("⚡ Diagnóstico Rápido (Sin Archivos)")
    
    c1, c2 = st.columns(2)
    with c1:
        venta = st.number_input(f"Venta mensual estimada ({m_sufijo}):", value=5000000.0)
        margen = st.slider("Margen de ganancia general (%):", 5, 80, 30)
    with c2:
        gastos = st.number_input(f"Gastos fijos ({m_sufijo}):", value=1200000.0)
        clientes = st.number_input("Clientes al mes:", value=350)
    
    utilidad = (venta * (margen / 100)) - gastos
    punto_eq = gastos / (margen / 100) if margen > 0 else 0
    ticket = venta / clientes if clientes > 0 else 0
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container {"metric-success" if utilidad > 0 else "metric-danger"}"><div class="metric-title">UTILIDAD NETA</div><div class="metric-value">{m_simbolo}{utilidad:,.2f}</div><div class="metric-caption">Ganancia descontando gastos fijos.</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">PUNTO DE EQUILIBRIO</div><div class="metric-value">{m_simbolo}{punto_eq:,.2f}</div><div class="metric-caption">Venta mínima requerida.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO</div><div class="metric-value">{m_simbolo}{ticket:,.2f}</div><div class="metric-caption">Gasto medio por cliente.</div></div>', unsafe_allow_html=True)

elif st.session_state.pantalla_actual == "diagnostico":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("📊 Auditoría de Catálogo y Costos")
    if df_final.empty: 
        st.warning("👈 Sube tu archivo de ventas en el menú de la izquierda para comenzar.")
    else:
        st.subheader("⚙️ 1. Ajuste de Costos Individuales")
        st.markdown("Tu catálogo inició con el costo global de la barra lateral. Aquí puedes afinar el **Costo (%)** de productos específicos.")
        st.session_state.costos_editados = st.data_editor(st.session_state.costos_editados, hide_index=True, use_container_width=True)
        
        df_g = df_final.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
        ticket_promedio = df_final['Sales'].sum() / len(df_final)
        
        st.markdown("---")
        st.subheader("🏆 2. Métricas Clave de Rentabilidad")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-container metric-success"><div class="metric-title">ESTRELLA (MÁXIMA UTILIDAD)</div><div class="metric-value">{m_simbolo}{df_g["Ganancia_Neta"].max():,.2f}</div><div class="metric-caption"><b>{df_g.loc[df_g["Ganancia_Neta"].idxmax()]["Product Name"]}</b></div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">LÍDER EN ROTACIÓN</div><div class="metric-value">{df_g["Quantity"].max()} Unds</div><div class="metric-caption"><b>{df_g.loc[df_g["Quantity"].idxmax()]["Product Name"]}</b></div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-container metric-danger"><div class="metric-title">DORMIDO (RIESGO INVENTARIO)</div><div class="metric-value">{df_g["Quantity"].min()} Unds</div><div class="metric-caption"><b>{df_g.loc[df_g["Quantity"].idxmin()]["Product Name"]}</b></div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO GLOBAL</div><div class="metric-value">{m_simbolo}{ticket_promedio:,.2f}</div><div class="metric-caption">Facturación media por registro.</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🎯 3. Matriz BCG y Concentración de Clientes")
        c_graf1, c_graf2 = st.columns(2)
        with c_graf1:
            st.plotly_chart(px.scatter(df_g, x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name', hover_name='Product Name', labels={'Quantity': 'Unds. Vendidas', 'Ganancia_Neta': 'Ganancia Neta'}, height=350).update_layout(showlegend=False, margin=dict(t=10, l=10, r=10, b=10)), use_container_width=True)
        with c_graf2:
            clientes_top = df_final.groupby('Customer Name')['Sales'].sum().reset_index().sort_values('Sales', ascending=False).head(5)
            st.plotly_chart(px.bar(clientes_top, x='Sales', y='Customer Name', orientation='h', color='Sales', color_continuous_scale='Blues').update_layout(height=350, showlegend=False, yaxis=dict(autorange="reversed"), margin=dict(t=10, l=10, r=10, b=10)), use_container_width=True)

elif st.session_state.pantalla_actual == "simulador":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎛️ Simulador Financiero")
    
    if df_final.empty: 
        st.warning("👈 Sube tu archivo de ventas en el menú de la izquierda.")
    else:
        st.markdown("### Ajusta tus palancas comerciales:")
        c1, c2 = st.columns(2)
        precio = c1.slider("1. Ajuste General de Precios (%)", -50, 100, 0)
        pauta = c2.slider(f"2. Pauta Publicitaria Adicional ({m_sufijo})", 0, int(1000000 * m_factor), 0, int(50000 * m_factor))
        
        factor_precio = 1 + (precio / 100)
        factor_cantidad = 1 - (precio / 100 * 0.5) 
        cl_n = int(pauta / (5000 * m_factor)) 
        
        precio_m = df_final['Sales'].mean() / df_final['Quantity'].mean()
        costo_promedio_porcentaje = st.session_state.costos_editados['Costo (%)'].mean() / 100
        
        v_sim = (df_final['Sales'] * factor_precio * factor_cantidad).sum() + ((cl_n * 1.5) * precio_m * factor_precio)
        c_sim = (df_final['Sales'] * costo_promedio_porcentaje * factor_cantidad).sum() + ((cl_n * 1.5) * precio_m * costo_promedio_porcentaje)
        g_sim = v_sim - c_sim - pauta
        
        fig = go.Figure(data=[
            go.Bar(name='Actual', x=['Ventas Totales', 'Ganancia Neta'], y=[df_final['Sales'].sum(), df_final['Ganancia_Neta'].sum()], marker_color='#636EFA', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside'),
            go.Bar(name='Proyectado', x=['Ventas Totales', 'Ganancia Neta'], y=[v_sim, g_sim], marker_color='#00CC96', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside')
        ])
        fig.update_layout(barmode='group', height=400, margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)

elif st.session_state.pantalla_actual == "objetivos":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎯 Planificador Estratégico Multi-Mes")
    
    c1, c2, c3 = st.columns(3)
    with c1: meta = st.number_input(f"Ganancia Neta Deseada ({m_sufijo}):", value=10000000.0, step=500000.0)
    with c2: meses = st.slider("Horizonte (Meses):", 1, 12, 1)
    with c3: gastos = st.number_input(f"Gastos Fijos Mensuales ({m_sufijo}):", value=1500000.0, step=100000.0)
    
    costo_prom_actual = st.session_state.costos_editados['Costo (%)'].mean() if not st.session_state.costos_editados.empty else float(costo_base)
    margen_comercial = (100 - costo_prom_actual) / 100
    
    gastos_totales = gastos * meses
    ventas_totales_req = (meta + gastos_totales) / margen_comercial if margen_comercial > 0 else 0
    ventas_diarias_req = ventas_totales_req / (30 * meses)
    
    t_prom = df_final['Sales'].sum() / len(df_final) if not df_final.empty else (ventas_totales_req / (300 * meses))
    clientes_diarios = int(np.ceil(ventas_diarias_req / t_prom)) if t_prom > 0 else 0
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container metric-success"><div class="metric-title">FACTURACIÓN TOTAL REQUERIDA</div><div class="metric-value">{m_simbolo}{ventas_totales_req:,.2f}</div><div class="metric-caption">Ventas necesarias en {meses} mes(es).</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container"><div class="metric-title">META DE VENTA DIARIA</div><div class="metric-value">{m_simbolo}{ventas_diarias_req:,.2f}</div><div class="metric-caption">Venta mínima promedio cada día.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">CLIENTES DIARIOS</div><div class="metric-value">{clientes_diarios} Compras/Día</div><div class="metric-caption">Basado en tu ticket promedio actual.</div></div>', unsafe_allow_html=True)
