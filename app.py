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

if "pantalla_actual" not in st.session_state:
    st.session_state.pantalla_actual = "home"
if "historial_chat" not in st.session_state:
    st.session_state.historial_chat = []

def cambiar_pantalla(nombre):
    st.session_state.pantalla_actual = nombre

# ==============================================================================
# NAVEGACIÓN RÁPIDA Y MONEDA
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
# FUNCIONES CORE Y PREPARACIÓN DE DATOS (CON COSTOS DINÁMICOS)
# ==============================================================================
@st.cache_data
def generar_plantilla_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame({
            'Fecha': ['01/10/2026', '02/10/2026'], 
            'Producto': ['Producto A', 'Producto B'], 
            'Ventas': [100, 250], 
            'Cantidad': [2, 5], 
            'Cliente': ['Mostrador', 'Cliente VIP'],
            'Costo Proveedor (%)': [60, 45] # NUEVA COLUMNA DE COSTOS INDIVIDUALES
        }).to_excel(writer, index=False)
    return output.getvalue()

@st.cache_data
def limpiar_y_preparar_datos(file_bytes, filename, porcentaje_costo_proveedor, factor_divisa):
    buffer = io.BytesIO(file_bytes) if isinstance(file_bytes, bytes) else file_bytes
    try:
        df_temp = pd.read_excel(buffer) if filename.endswith('.xlsx') else pd.read_csv(buffer, encoding='utf-8')
    except:
        return pd.DataFrame()

    column_map = {}
    for col in df_temp.columns:
        col_clean = str(col).strip().lower()
        if any(x in col_clean for x in ['fecha', 'order date', 'date']): column_map[col] = 'Order Date'
        elif any(x in col_clean for x in ['venta', 'sales', 'monto']): column_map[col] = 'Sales'
        elif any(x in col_clean for x in ['producto', 'product', 'sku']): column_map[col] = 'Product Name'
        elif any(x in col_clean for x in ['cantidad', 'quantity', 'cant']): column_map[col] = 'Quantity'
        elif any(x in col_clean for x in ['cliente', 'customer']): column_map[col] = 'Customer Name'
        # MAPEO DE COSTOS DINÁMICOS
        elif any(x in col_clean for x in ['costo', 'cost', 'margen']): column_map[col] = 'Costo_Porcentaje'
            
    df_temp = df_temp.rename(columns=column_map)
    if 'Sales' not in df_temp.columns: return pd.DataFrame()
    
    if 'Product Name' not in df_temp.columns: df_temp['Product Name'] = "Artículo General"
    if 'Customer Name' not in df_temp.columns: df_temp['Customer Name'] = "Mostrador"
    if 'Quantity' not in df_temp.columns: df_temp['Quantity'] = 1
    
    # LÓGICA DE COSTO HÍBRIDO (Individual vs Global)
    if 'Costo_Porcentaje' not in df_temp.columns: 
        df_temp['Costo_Porcentaje'] = porcentaje_costo_proveedor
    else:
        df_temp['Costo_Porcentaje'] = pd.to_numeric(df_temp['Costo_Porcentaje'], errors='coerce').fillna(porcentaje_costo_proveedor)
        
    df_temp = df_temp.dropna(subset=['Sales'])
    df_temp['Sales'] = pd.to_numeric(df_temp['Sales'], errors='coerce') * factor_divisa
    df_temp['Quantity'] = pd.to_numeric(df_temp['Quantity'], errors='coerce').fillna(1)
    
    if 'Order Date' in df_temp.columns: df_temp['Order Date'] = pd.to_datetime(df_temp['Order Date'], format='%d/%m/%Y', errors='coerce')
    else: df_temp['Order Date'] = pd.Timestamp.now()
        
    df_temp['Costo_Proveedor'] = df_temp['Sales'] * (df_temp['Costo_Porcentaje'] / 100)
    df_temp['Ganancia_Neta'] = df_temp['Sales'] - df_temp['Costo_Proveedor']
    return df_temp

def analizar_datos_avanzados(df_limpio):
    df_agrupado = df_limpio.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
    df_limpio['Precio_Unitario'] = df_limpio['Sales'] / df_limpio['Quantity']
    df_agrupado['Precio_Unitario_Promedio'] = df_agrupado['Sales'] / df_agrupado['Quantity']
    df_limpio['Dia_Semana'] = df_limpio['Order Date'].dt.day_name().map({'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}).fillna('Indeterminado')
    
    df_pareto = df_agrupado.sort_values(by='Sales', ascending=False)
    df_pareto['Pct_Acum'] = (df_pareto['Sales'].cumsum() / df_pareto['Sales'].sum()) * 100
    
    return {
        "mas_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmax()]['Product Name'],
        "cant_mas_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmax()]['Quantity'],
        "estrella": df_agrupado.loc[df_agrupado['Ganancia_Neta'].idxmax()]['Product Name'],
        "ganancia_estrella": df_agrupado.loc[df_agrupado['Ganancia_Neta'].idxmax()]['Ganancia_Neta'],
        "menos_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmin()]['Product Name'],
        "cant_menos_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmin()]['Quantity'],
        "dia_dorado": df_limpio.groupby('Dia_Semana')['Sales'].sum().idxmax(),
        "ticket_promedio": df_limpio['Sales'].sum() / len(df_limpio),
        "top_clientes": df_limpio.groupby('Customer Name')['Sales'].sum().reset_index().sort_values(by='Sales', ascending=False).head(5),
        "df_agrupado": df_agrupado,
        "total_skus": len(df_pareto),
        "skus_pareto": max(1, len(df_pareto[df_pareto['Pct_Acum'] <= 80]))
    }

def simular_escenario_negocio(df_original, cambio_precio, presupuesto):
    factor_precio = 1 + (cambio_precio / 100)
    factor_cantidad = 1 - (cambio_precio / 100 * 0.5) 
    
    cl_n = int((presupuesto * 2.0) / (3 * m_factor)) if presupuesto < (20 * m_factor) else int(((presupuesto * 0.35 * 3.5) + (presupuesto * 0.30 * 3.0) + (presupuesto * 0.20 * 2.5) + (presupuesto * 0.15 * 2.0)) / (4 * m_factor))
    
    precio_medio = df_original['Sales'].mean() / df_original['Quantity'].mean()
    costo_medio_pct = (df_original['Costo_Porcentaje'] / 100).mean()
    
    v_sim = (df_original['Sales'] * factor_precio * factor_cantidad).sum() + ((cl_n * 1.5) * precio_medio * factor_precio)
    c_sim = (df_original['Sales'] * (df_original['Costo_Porcentaje']/100) * factor_cantidad).sum() + ((cl_n * 1.5) * precio_medio * costo_medio_pct)
    
    return df_original['Sales'].sum(), df_original['Ganancia_Neta'].sum(), v_sim, v_sim - c_sim - presupuesto, cl_n

# ==============================================================================
# BARRA LATERAL (INGESTA)
# ==============================================================================
df_app = pd.DataFrame()
slider_costo_prov = 70

if st.session_state.pantalla_actual in ["diagnostico", "simulador", "objetivos"]:
    st.sidebar.markdown("---")
    st.sidebar.header("📁 Cargar Datos")
    st.sidebar.download_button("📥 Descargar Plantilla Avanzada (Con Costos)", generar_plantilla_excel(), "plantilla_avanzada.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    archivo_usuario = st.sidebar.file_uploader("Sube tu archivo de ventas:", type=['csv', 'xlsx'])
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Costo Global (Si el archivo no lo tiene)")
    slider_costo_prov = st.sidebar.slider("Costo de Proveedor por defecto (%)", 10, 90, 70, 5)

    if archivo_usuario:
        df_app = limpiar_y_preparar_datos(archivo_usuario.getvalue(), archivo_usuario.name, slider_costo_prov, m_factor)
    else:
        try:
            with open('train.csv', 'rb') as f: df_app = limpiar_y_preparar_datos(f.read(), 'train.csv', slider_costo_prov, m_factor)
        except: pass

if not df_app.empty:
    analisis = analizar_datos_avanzados(df_app)

# ==============================================================================
# PANTALLAS
# ==============================================================================
if st.session_state.pantalla_actual == "home":
    st.title("🚀 Bienvenido a IntelRetail Pro")
    st.markdown("#### *El copiloto estratégico de inteligencia de negocios.*")
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown('<div class="home-card"><h3>⚡ Diagnóstico Express</h3><p>Ingresa números estimados y obtén tu punto de equilibrio.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Diagnóstico Express", use_container_width=True, type="primary"): cambiar_pantalla("express"); st.rerun()
        st.markdown('<div class="home-card"><h3>🎛️ Simulador e IA</h3><p>Proyecta utilidades y chatea con tus datos usando Gemini AI.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Simulador Financiero", use_container_width=True): cambiar_pantalla("simulador"); st.rerun()
    with col_h2:
        st.markdown('<div class="home-card"><h3>🔍 Auditoría de Catálogo</h3><p>Descubre tu producto estrella, Pareto 80/20 y matriz BCG.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Auditoría de Catálogo", use_container_width=True): cambiar_pantalla("diagnostico"); st.rerun()
        st.markdown('<div class="home-card"><h3>🎯 Planificador de Metas</h3><p>Calcula cuántas ventas diarias necesitas para tu meta.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Planificador de Metas", use_container_width=True): cambiar_pantalla("objetivos"); st.rerun()

elif st.session_state.pantalla_actual == "diagnostico":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("📊 Auditoría y BI de Catálogo")
    if df_app.empty: st.warning("Carga tus datos en el menú lateral.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-container"><div class="metric-title">🏆 ESTRELLA (MÁXIMA UTILIDAD)</div><div class="metric-value">{m_simbolo}{analisis["ganancia_estrella"]:,.2f}</div><div class="metric-caption">{analisis["estrella"]}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">🥇 LÍDER EN ROTACIÓN</div><div class="metric-value">{analisis["cant_mas_vendido"]} Unds</div><div class="metric-caption">{analisis["mas_vendido"]}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">🛒 TICKET PROMEDIO</div><div class="metric-value">{m_simbolo}{analisis["ticket_promedio"]:,.2f}</div><div class="metric-caption">Por transacción en base de datos.</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-container metric-danger"><div class="metric-title">💤 DORMIDO (RIESGO)</div><div class="metric-value">{analisis["cant_menos_vendido"]} Unds</div><div class="metric-caption">{analisis["menos_vendido"]}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">🗓️ DÍA DORADO</div><div class="metric-value">Cada {analisis["dia_dorado"]}</div><div class="metric-caption">Mayor concentración de ingresos.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">📐 PARETO (80/20)</div><div class="metric-value">{analisis["skus_pareto"]} de {analisis["total_skus"]} Productos</div><div class="metric-caption">Generan el 80% de tus ventas.</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🎯 Matriz de Inventario BCG (Rotación vs. Margen)")
        st.plotly_chart(px.scatter(analisis['df_agrupado'], x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name', hover_name='Product Name', height=380).update_layout(showlegend=False), use_container_width=True)

elif st.session_state.pantalla_actual == "simulador":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎛️ Simulador Financiero y Asesor IA")
    
    if df_app.empty: st.warning("Carga tus datos en el menú lateral.")
    else:
        c1, c2 = st.columns(2)
        precio = c1.slider("Ajuste de Precios (%)", -20, 20, 0)
        pauta = c2.slider("Presupuesto de Pauta Mensual", 0, int(5000 * m_factor), 0, int(100 * m_factor))
        
        v_h, g_h, v_s, g_s, cl_n = simular_escenario_negocio(df_app, precio, pauta)
        st.plotly_chart(go.Figure(data=[
            go.Bar(name='Histórico', x=['Ventas', 'Ganancia'], y=[v_h, g_h], marker_color='#636EFA'),
            go.Bar(name='Proyectado', x=['Ventas', 'Ganancia'], y=[v_s, g_s], marker_color='#00CC96')
        ]).update_layout(barmode='group', height=350), use_container_width=True)

        st.markdown("---")
        st.subheader("🤖 Chatbot Analista: Pregúntale a tus Datos (Gemini IA)")
        st.markdown("Escribe cualquier pregunta sobre tus productos, precios o estrategias. La IA responderá analizando tu tabla de ventas.")
        
        api_key = st.text_input("Ingresa tu API Key de Gemini para chatear:", type="password")
        
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Mostrar historial de chat
            for mensaje in st.session_state.historial_chat:
                with st.chat_message(mensaje["role"]):
                    st.write(mensaje["content"])
            
            # Caja de texto para que el usuario escriba su pregunta
            pregunta = st.chat_input("Ej: ¿Cuál es mi producto más barato? o Escribe copys para mi producto estrella.")
            
            if pregunta:
                # Agregar pregunta del usuario al historial y mostrarla
                st.session_state.historial_chat.append({"role": "user", "content": pregunta})
                with st.chat_message("user"):
                    st.write(pregunta)
                
                # Preparar el contexto oculto (Los datos que la IA leerá)
                df_resumen = analisis['df_agrupado'][['Product Name', 'Quantity', 'Sales', 'Ganancia_Neta', 'Precio_Unitario_Promedio']].to_string(index=False)
                contexto_oculto = f"""
                Eres un analista de datos y experto en marketing retail. 
                Aquí está el catálogo de productos de mi negocio con sus datos de ventas:
                {df_resumen}
                
                Responde a la siguiente solicitud del usuario utilizando SOLO los datos de arriba. 
                Pregunta del usuario: {pregunta}
                """
                
                # Obtener respuesta de Gemini y mostrarla
                with st.chat_message("assistant"):
                    with st.spinner("Analizando tu catálogo..."):
                        try:
                            respuesta = model.generate_content(contexto_oculto)
                            st.write(respuesta.text)
                            st.session_state.historial_chat.append({"role": "assistant", "content": respuesta.text})
                        except Exception as e:
                            st.error(f"Error de conexión con la API: {e}")
        else:
            st.info("⚠️ Ingresa una clave API válida para activar el chat de datos.")

elif st.session_state.pantalla_actual == "express":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("⚡ Diagnóstico Rápido")
    st.info("Módulo Express activo.") # (Aquí pega tu código de Diagnóstico Express)

elif st.session_state.pantalla_actual == "objetivos":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎯 Planificador por Objetivos")
    st.info("Planificador activo.") # (Aquí pega tu código de Objetivos)
