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

# Inicialización de la memoria (Session State)
if "pantalla_actual" not in st.session_state: st.session_state.pantalla_actual = "home"
if "historial_chat" not in st.session_state: st.session_state.historial_chat = []
if "df_bruto" not in st.session_state: st.session_state.df_bruto = pd.DataFrame()
if "costos_editados" not in st.session_state: st.session_state.costos_editados = pd.DataFrame()

# API Key Invisible
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    modelo_ia = genai.GenerativeModel('gemini-3.6-flash')
    ia_activa = True
except:
    ia_activa = False

def cambiar_pantalla(nombre): st.session_state.pantalla_actual = nombre

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
# 2. BARRA LATERAL (NAVEGACIÓN, DATOS Y CHATBOT GLOBAL)
# ==============================================================================
with st.sidebar:
    st.title("🧭 Navegación")
    if st.button("🏠 Inicio", use_container_width=True): cambiar_pantalla("home")
    if st.button("⚡ Diagnóstico Express", use_container_width=True): cambiar_pantalla("express")
    if st.button("🔍 Auditoría de Catálogo", use_container_width=True): cambiar_pantalla("diagnostico")
    if st.button("🎛️ Simulador y Pauta IA", use_container_width=True): cambiar_pantalla("simulador")
    if st.button("🎯 Planificador Metas", use_container_width=True): cambiar_pantalla("objetivos")
    
    st.markdown("---")
    st.header("📁 Ingesta de Datos")
    archivo = st.file_uploader("Sube tus ventas (CSV/Excel):", type=['csv', 'xlsx'])
    
    if archivo:
        # Guardamos en memoria para que no se borre al cambiar de pestaña
        if archivo.name.endswith('.xlsx'): st.session_state.df_bruto = pd.read_excel(archivo)
        else: st.session_state.df_bruto = pd.read_csv(archivo)
        st.success("¡Datos cargados y guardados en memoria!")

    # EL CHATBOT GLOBAL VIVE AQUÍ
    st.markdown("---")
    st.header("💬 Asesor IA (Copiloto)")
    if not ia_activa:
        st.error("⚠️ Falta API Key en Secrets")
    else:
        for msg in st.session_state.historial_chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        pregunta = st.chat_input("Escribe tu pregunta...")
        if pregunta:
            st.session_state.historial_chat.append({"role": "user", "content": pregunta})
            with st.chat_message("user"): st.write(pregunta)
            
            # Contexto Dinámico para la IA
            resumen_datos = st.session_state.df_bruto.head(10).to_string() if not st.session_state.df_bruto.empty else "Sin datos"
            prompt_experto = f"""
            Eres el Asesor IA de IntelRetail Pro. 
            El usuario está viendo la pantalla: {st.session_state.pantalla_actual}.
            Datos recientes de su negocio: {resumen_datos}
            Instrucción vital: Analiza el tipo de productos que maneja el usuario en la tabla. Si detectas un nicho específico (ej. productos para mascotas, peluquería, moda, etc.), recomiéndale estratégicamente qué plataforma de publicidad es mejor (ej. Instagram/TikTok para visuales, Google Ads para urgencias).
            Responde de forma profesional, concisa y comercial a la siguiente pregunta: {pregunta}
            """
            
            with st.chat_message("assistant"):
                with st.spinner("Analizando..."):
                    try:
                        respuesta = modelo_ia.generate_content(prompt_experto)
                        st.write(respuesta.text)
                        st.session_state.historial_chat.append({"role": "assistant", "content": respuesta.text})
                    except Exception as e: st.error("Error de conexión.")

# ==============================================================================
# 3. PROCESAMIENTO CON COSTOS INDIVIDUALES
# ==============================================================================
df_final = pd.DataFrame()

if not st.session_state.df_bruto.empty:
    df_temp = st.session_state.df_bruto.copy()
    
    # Mapeo corregido y exacto de columnas
    column_map = {}
    for col in df_temp.columns:
        c = str(col).strip().lower()
        if any(x in c for x in ['venta', 'sales', 'monto']): column_map[col] = 'Sales'
        elif any(x in c for x in ['producto', 'product', 'sku']): column_map[col] = 'Product Name'
        elif any(x in c for x in ['cantidad', 'quantity', 'cant']): column_map[col] = 'Quantity'
        elif any(x in c for x in ['cliente', 'customer']): column_map[col] = 'Customer Name'
        elif any(x in c for x in ['fecha', 'date']): column_map[col] = 'Order Date'
            
    df_temp = df_temp.rename(columns=column_map)
    df_temp = df_temp.loc[:, ~df_temp.columns.duplicated()] # Elimina duplicados
    
    # Valores por defecto si faltan columnas
    if 'Sales' in df_temp.columns:
        if 'Product Name' not in df_temp.columns: df_temp['Product Name'] = 'General'
        if 'Quantity' not in df_temp.columns: df_temp['Quantity'] = 1
        if 'Customer Name' not in df_temp.columns: df_temp['Customer Name'] = "Mostrador"
        
        # Limpieza de datos numéricos
        df_temp['Sales'] = pd.to_numeric(df_temp['Sales'], errors='coerce').fillna(0)
        df_temp['Quantity'] = pd.to_numeric(df_temp['Quantity'], errors='coerce').fillna(1)
        
        # Generar tabla de costos únicos si no existe o cambió el archivo
        productos_unicos = df_temp['Product Name'].unique()
        if st.session_state.costos_editados.empty or len(st.session_state.costos_editados) != len(productos_unicos):
            st.session_state.costos_editados = pd.DataFrame({'Product Name': productos_unicos, 'Costo (%)': [60.0]*len(productos_unicos)})
        
        # Cruzar ventas con la tabla de costos interactiva
        df_final = pd.merge(df_temp, st.session_state.costos_editados, on='Product Name', how='left')
        df_final['Costo_Valor'] = df_final['Sales'] * (df_final['Costo (%)'] / 100)
        df_final['Ganancia_Neta'] = df_final['Sales'] - df_final['Costo_Valor']

# ==============================================================================
# 4. PANTALLAS COMPLETAS (RESTAURADAS AL 100%)
# ==============================================================================

# -- PANTALLA: HOME --
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

# -- PANTALLA: EXPRESS --
elif st.session_state.pantalla_actual == "express":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("⚡ Diagnóstico Rápido (Sin Archivos)")
    
    c1, c2 = st.columns(2)
    with c1:
        venta = st.number_input("Venta mensual estimada ($):", value=5000000.0)
        margen = st.slider("Margen de ganancia general (%):", 5, 80, 30)
    with c2:
        gastos = st.number_input("Gastos fijos ($):", value=1200000.0)
        clientes = st.number_input("Clientes al mes:", value=350)
    
    utilidad = (venta * (margen / 100)) - gastos
    punto_eq = gastos / (margen / 100) if margen > 0 else 0
    ticket = venta / clientes if clientes > 0 else 0
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container {"metric-success" if utilidad > 0 else "metric-danger"}"><div class="metric-title">UTILIDAD NETA</div><div class="metric-value">${utilidad:,.2f}</div><div class="metric-caption">Ganancia real descontando gastos fijos.</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">PUNTO DE EQUILIBRIO</div><div class="metric-value">${punto_eq:,.2f}</div><div class="metric-caption">Venta mínima requerida para no perder dinero.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO</div><div class="metric-value">${ticket:,.2f}</div><div class="metric-caption">Lo que gasta cada cliente en promedio.</div></div>', unsafe_allow_html=True)

# -- PANTALLA: DIAGNÓSTICO Y COSTOS INDIVIDUALES --
elif st.session_state.pantalla_actual == "diagnostico":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("📊 Auditoría de Catálogo y Costos")
    if df_final.empty: 
        st.warning("👈 Sube tu archivo de ventas en el menú de la izquierda para comenzar.")
    else:
        st.subheader("⚙️ 1. Ajuste de Costos Individuales")
        st.markdown("Modifica la columna **Costo (%)** para cada producto. Todas las gráficas se actualizarán en tiempo real.")
        
        # Tabla interactiva
        st.session_state.costos_editados = st.data_editor(st.session_state.costos_editados, hide_index=True, use_container_width=True)
        
        # Recálculo de métricas Top
        df_g = df_final.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
        ticket_promedio = df_final['Sales'].sum() / len(df_final)
        
        st.markdown("---")
        st.subheader("🏆 2. Métricas Clave de Rentabilidad")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-container metric-success"><div class="metric-title">ESTRELLA (MÁXIMA UTILIDAD)</div><div class="metric-value">${df_g["Ganancia_Neta"].max():,.2f}</div><div class="metric-caption"><b>{df_g.loc[df_g["Ganancia_Neta"].idxmax()]["Product Name"]}</b><br>El producto que más dinero real deja en caja.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">LÍDER EN ROTACIÓN</div><div class="metric-value">{df_g["Quantity"].max()} Unds</div><div class="metric-caption"><b>{df_g.loc[df_g["Quantity"].idxmax()]["Product Name"]}</b></div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-container metric-danger"><div class="metric-title">DORMIDO (RIESGO INVENTARIO)</div><div class="metric-value">{df_g["Quantity"].min()} Unds</div><div class="metric-caption"><b>{df_g.loc[df_g["Quantity"].idxmin()]["Product Name"]}</b><br>Baja rotación de inventario.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO GLOBAL</div><div class="metric-value">${ticket_promedio:,.2f}</div><div class="metric-caption">Facturación media por registro.</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🎯 3. Matriz BCG: Posición Estratégica")
        st.plotly_chart(px.scatter(df_g, x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name', hover_name='Product Name', labels={'Quantity': 'Unidades Vendidas', 'Ganancia_Neta': 'Ganancia Neta Real'}, height=380).update_layout(showlegend=False), use_container_width=True)

        st.markdown("---")
        st.subheader("👥 4. Concentración: Top 5 Clientes")
        clientes_top = df_final.groupby('Customer Name')['Sales'].sum().reset_index().sort_values('Sales', ascending=False).head(5)
        st.plotly_chart(px.bar(clientes_top, x='Sales', y='Customer Name', orientation='h', color='Sales', color_continuous_scale='Blues').update_layout(height=300, showlegend=False, yaxis=dict(autorange="reversed")), use_container_width=True)

# -- PANTALLA: SIMULADOR --
elif st.session_state.pantalla_actual == "simulador":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎛️ Simulador Financiero")
    
    if df_final.empty: 
        st.warning("👈 Sube tu archivo de ventas en el menú de la izquierda.")
    else:
        st.markdown("### Ajusta tus palancas comerciales:")
        c1, c2 = st.columns(2)
        precio = c1.slider("1. Ajuste General de Precios (%)", -50, 100, 0)
        pauta = c2.slider("2. Presupuesto Publicidad Adicional ($)", 0, 1000000, 0, 50000)
        
        # Cálculos de simulación basados en los costos personalizados
        factor_precio = 1 + (precio / 100)
        factor_cantidad = 1 - (precio / 100 * 0.5) 
        cl_n = int(pauta / 5000) # Costo aprox de adquisición de cliente simulado
        
        precio_m = df_final['Sales'].mean() / df_final['Quantity'].mean()
        costo_promedio_porcentaje = st.session_state.costos_editados['Costo (%)'].mean() / 100
        
        v_sim = (df_final['Sales'] * factor_precio * factor_cantidad).sum() + ((cl_n * 1.5) * precio_m * factor_precio)
        c_sim = (df_final['Sales'] * costo_promedio_porcentaje * factor_cantidad).sum() + ((cl_n * 1.5) * precio_m * costo_promedio_porcentaje)
        g_sim = v_sim - c_sim - pauta
        
        fig = go.Figure(data=[
            go.Bar(name='Actual', x=['Ventas Totales', 'Ganancia Neta'], y=[df_final['Sales'].sum(), df_final['Ganancia_Neta'].sum()], marker_color='#636EFA', texttemplate='$%{y:,.0f}', textposition='outside'),
            go.Bar(name='Proyectado', x=['Ventas Totales', 'Ganancia Neta'], y=[v_sim, g_sim], marker_color='#00CC96', texttemplate='$%{y:,.0f}', textposition='outside')
        ])
        fig.update_layout(barmode='group', height=400, margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)

# -- PANTALLA: OBJETIVOS --
elif st.session_state.pantalla_actual == "objetivos":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎯 Planificador Estratégico Multi-Mes")
    
    c1, c2, c3 = st.columns(3)
    with c1: meta = st.number_input("Ganancia Neta Deseada ($):", value=10000000.0, step=500000.0)
    with c2: meses = st.slider("Horizonte (Meses):", 1, 12, 1)
    with c3: gastos = st.number_input("Gastos Fijos por Mes ($):", value=1500000.0, step=100000.0)
    
    # Cálculo basado en costo promedio actual o 70% por defecto
    costo_prom_actual = st.session_state.costos_editados['Costo (%)'].mean() if not st.session_state.costos_editados.empty else 70.0
    margen_comercial = (100 - costo_prom_actual) / 100
    
    gastos_totales = gastos * meses
    ventas_totales_req = (meta + gastos_totales) / margen_comercial if margen_comercial > 0 else 0
    ventas_diarias_req = ventas_totales_req / (30 * meses)
    
    t_prom = df_final['Sales'].sum() / len(df_final) if not df_final.empty else (ventas_totales_req / (300 * meses))
    clientes_diarios = int(np.ceil(ventas_diarias_req / t_prom)) if t_prom > 0 else 0
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container metric-success"><div class="metric-title">FACTURACIÓN TOTAL REQUERIDA</div><div class="metric-value">${ventas_totales_req:,.2f}</div><div class="metric-caption">Ventas necesarias en {meses} mes(es).</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container"><div class="metric-title">META DE VENTA DIARIA</div><div class="metric-value">${ventas_diarias_req:,.2f}</div><div class="metric-caption">Venta mínima promedio cada día.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">CLIENTES DIARIOS</div><div class="metric-value">{clientes_diarios} Compras/Día</div><div class="metric-caption">Basado en tu ticket promedio.</div></div>', unsafe_allow_html=True)
