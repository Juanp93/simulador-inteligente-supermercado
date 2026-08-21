import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import google.generativeai as genai

# ==============================================================================
# CONFIGURACIÓN, MEMORIA Y ESTILOS (Puntos 1 y 3)
# ==============================================================================
st.set_page_config(page_title="IntelRetail Pro", layout="wide", page_icon="📈")

# Inicialización de la memoria (Session State)
if "pantalla_actual" not in st.session_state: st.session_state.pantalla_actual = "home"
if "historial_chat" not in st.session_state: st.session_state.historial_chat = []
if "df_bruto" not in st.session_state: st.session_state.df_bruto = pd.DataFrame()
if "costos_editados" not in st.session_state: st.session_state.costos_editados = pd.DataFrame()

# API Key Invisible (Punto 3)
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
    .metric-title { font-size: 13px; color: #A3A3A3; font-weight: bold; }
    .metric-value { font-size: 22px; color: #FFFFFF; font-weight: bold; margin-top: 5px; }
    div[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# NAVEGACIÓN, DATOS Y CHATBOT GLOBAL (BARRA LATERAL) (Puntos 1, 2 y 4)
# ==============================================================================
with st.sidebar:
    st.title("🧭 Navegación")
    if st.button("🏠 Inicio", use_container_width=True): cambiar_pantalla("home")
    if st.button("🔍 Auditoría de Catálogo", use_container_width=True): cambiar_pantalla("diagnostico")
    if st.button("🎛️ Simulador", use_container_width=True): cambiar_pantalla("simulador")
    if st.button("🎯 Planificador Metas", use_container_width=True): cambiar_pantalla("objetivos")
    
    st.markdown("---")
    st.header("📁 Datos")
    archivo = st.file_uploader("Sube tus ventas:", type=['csv', 'xlsx'])
    
    if archivo:
        # Guardamos en memoria para que no se borre al cambiar de pestaña
        if archivo.name.endswith('.xlsx'): st.session_state.df_bruto = pd.read_excel(archivo)
        else: st.session_state.df_bruto = pd.read_csv(archivo)
        st.success("¡Datos cargados en memoria!")

    # EL CHATBOT GLOBAL VIVE AQUÍ
    st.markdown("---")
    st.header("💬 Asesor IA")
    if not ia_activa:
        st.error("Falta API Key en Secrets")
    else:
        for msg in st.session_state.historial_chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        pregunta = st.chat_input("Pregúntale a tus datos...")
        if pregunta:
            st.session_state.historial_chat.append({"role": "user", "content": pregunta})
            with st.chat_message("user"): st.write(pregunta)
            
            # Contexto Dinámico (Puntos 4 y 6)
            resumen_datos = st.session_state.df_bruto.head().to_string() if not st.session_state.df_bruto.empty else "Sin datos"
            prompt_experto = f"""
            Eres el Asesor IA de IntelRetail Pro. 
            El usuario está en la pantalla: {st.session_state.pantalla_actual}.
            Datos recientes: {resumen_datos}
            Instrucción vital: Analiza el nicho. Si detectas productos de mascotas o servicios de peluquería, sugiere invertir en pauta visual (Instagram/TikTok).
            Responde breve y profesional a: {pregunta}
            """
            
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    try:
                        respuesta = modelo_ia.generate_content(prompt_experto)
                        st.write(respuesta.text)
                        st.session_state.historial_chat.append({"role": "assistant", "content": respuesta.text})
                    except Exception as e: st.error("Error de conexión.")

# ==============================================================================
# PROCESAMIENTO CON COSTOS INDIVIDUALES (Punto 5)
# ==============================================================================
# ==============================================================================
# PROCESAMIENTO CON COSTOS INDIVIDUALES (Punto 5)
# ==============================================================================
df_app = pd.DataFrame()
if not st.session_state.df_bruto.empty:
    df_temp = st.session_state.df_bruto.copy()
    
    # Mapeo corregido y exacto de columnas
    column_map = {}
    for col in df_temp.columns:
        c = str(col).strip().lower()
        if any(x in c for x in ['venta', 'sales', 'monto']): column_map[col] = 'Sales'
        elif any(x in c for x in ['producto', 'product', 'sku']): column_map[col] = 'Product Name'
        elif any(x in c for x in ['cantidad', 'quantity', 'cant']): column_map[col] = 'Quantity'
            
    df_temp = df_temp.rename(columns=column_map)
    
    # Limpieza
    if 'Sales' in df_temp.columns:
        if 'Product Name' not in df_temp.columns: df_temp['Product Name'] = 'General'
        if 'Quantity' not in df_temp.columns: df_temp['Quantity'] = 1
        
        # Eliminar columnas duplicadas por precaución
        df_temp = df_temp.loc[:, ~df_temp.columns.duplicated()]
        
        # Generar tabla de costos únicos
        productos_unicos = df_temp['Product Name'].unique()
        if st.session_state.costos_editados.empty or len(st.session_state.costos_editados) != len(productos_unicos):
            st.session_state.costos_editados = pd.DataFrame({'Product Name': productos_unicos, 'Costo (%)': [60.0]*len(productos_unicos)})
        
        df_app = df_temp    
# ==============================================================================
# PANTALLAS
# ==============================================================================
if st.session_state.pantalla_actual == "home":
    st.title("🚀 Bienvenido a IntelRetail Pro")
    st.markdown("Carga tus datos en la barra lateral y explora las herramientas.")

elif st.session_state.pantalla_actual == "diagnostico":
    st.header("📊 Auditoría de Catálogo y Costos")
    if df_app.empty: st.warning("Carga tus datos primero.")
    else:
        st.subheader("⚙️ 1. Ajuste de Costos Individuales")
        st.markdown("Modifica el % de costo para cada producto. Los márgenes se recalcularán automáticamente.")
        
        # Editor Interactivo (Punto 5)
        st.session_state.costos_editados = st.data_editor(st.session_state.costos_editados, hide_index=True, use_container_width=True)
        
        # Cruce de datos para calcular ganancia real
        df_final = pd.merge(df_app, st.session_state.costos_editados, on='Product Name', how='left')
        df_final['Costo_Valor'] = df_final['Sales'] * (df_final['Costo (%)'] / 100)
        df_final['Ganancia_Neta'] = df_final['Sales'] - df_final['Costo_Valor']
        
        st.markdown("---")
        st.subheader("🎯 2. Matriz BCG y Rentabilidad")
        df_g = df_final.groupby('Product Name').agg({'Quantity': 'sum', 'Ganancia_Neta': 'sum', 'Sales': 'sum'}).reset_index()
        st.plotly_chart(px.scatter(df_g, x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name'), use_container_width=True)

elif st.session_state.pantalla_actual == "simulador":
    st.header("🎛️ Simulador Financiero")
    st.info("Utiliza el Asesor IA en la barra lateral para planificar tus campañas.")
    if not df_app.empty: st.success("Datos listos para simular. (Aquí irán tus gráficas)")

elif st.session_state.pantalla_actual == "objetivos":
    st.header("🎯 Planificador de Metas")
    st.info("Pregúntale a la IA en la barra lateral: '¿Es realista mi meta?'")
