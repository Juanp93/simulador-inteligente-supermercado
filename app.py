import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import google.generativeai as genai
from streamlit_option_menu import option_menu

# ==============================================================================
# 1. CONFIGURACIÓN, MEMORIA Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="IntelRetail Pro", layout="wide", page_icon="🚀")

if "pantalla_actual" not in st.session_state: st.session_state.pantalla_actual = "home"
if "historial_chat" not in st.session_state: st.session_state.historial_chat = []
if "df_bruto" not in st.session_state: st.session_state.df_bruto = pd.DataFrame()
if "costos_editados" not in st.session_state: st.session_state.costos_editados = pd.DataFrame()
if "escenario_a" not in st.session_state: st.session_state.escenario_a = None
if "apuntes_ia" not in st.session_state: st.session_state.apuntes_ia = ""

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
        pd.DataFrame({'Fecha': ['01/10/2026', '02/10/2026'], 'Producto': ['Producto A', 'Producto B'], 'Ventas': [100000, 250000], 'Cantidad': [2, 5], 'Cliente': ['Mostrador', 'VIP']}).to_excel(writer, index=False)
    return output.getvalue()

@st.cache_data
def df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte Ejecutivo')
    return output.getvalue()

def generar_informe_texto(ventas_tot, ganancia_tot, simbolo, notas_ia):
    contenido = f"""====================================================
INFORME EJECUTIVO - INTELRETAIL PRO
====================================================

💰 RESUMEN FINANCIERO GLOBAL:
- Ventas Totales Registradas: {simbolo}{ventas_tot:,.2f}
- Ganancia Neta Libre Estimada: {simbolo}{ganancia_tot:,.2f}

----------------------------------------------------
🧠 APUNTES Y ESTRATEGIAS DE INTELIGENCIA ARTIFICIAL:
----------------------------------------------------
{notas_ia if notas_ia != "" else "Aún no has generado estrategias con la IA en esta sesión."}

====================================================
Generado automáticamente por tu copiloto IntelRetail Pro.
"""
    return contenido.encode('utf-8')

# INYECCIÓN CSS PREMIUM CON TU FONDO ANIMADO
st.markdown("""
<style>
    /* Ocultar botones de Streamlit en la esquina superior */
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* FONDO ANIMADO MAESTRO (GIF DE GITHUB) */
    [data-testid="stAppViewContainer"] {
        background-color: #0C1519;
        background-image: url('https://github.com/Juanp93/simulador-inteligente-supermercado/raw/main/gif4.webm');
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    
    /* EFECTO GLASSMORPHISM EN TARJETAS */
    .metric-container, .home-card { 
        background: linear-gradient(135deg, rgba(22, 33, 39, 0.75) 0%, rgba(12, 21, 25, 0.90) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(114, 75, 57, 0.35);
        border-radius: 16px;
        color: #F3F4F6;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    }
    .metric-container { 
        padding: 22px; 
        margin-bottom: 15px;
        border-left: 4px solid #CF9D7B; 
    }
    .metric-success { border-left: 4px solid #00CC96; }
    .metric-warning { border-left: 4px solid #FFA15A; }
    .metric-danger { border-left: 4px solid #EF553B; }
    
    .metric-title { font-size: 12px; color: #CF9D7B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 26px; color: #FFFFFF; font-weight: 700; margin-top: 8px; margin-bottom: 4px; }
    .metric-caption { font-size: 12px; color: #8F95A3; line-height: 1.4; }
    
    .home-card { 
        padding: 30px; 
        margin-bottom: 20px; 
        text-align: center;
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .home-card:hover { transform: translateY(-4px); border: 1px solid #CF9D7B; box-shadow: 0 12px 40px rgba(207, 157, 123, 0.2); }
    .home-card h3 { color: #FFFFFF; margin-bottom: 12px; font-size: 19px; font-weight: 600; }
    .home-card p { color: #8F95A3; font-size: 14px; margin-bottom: 25px; min-height: 45px; line-height: 1.5; }
    
    div[data-testid="stSidebarNav"] {display: none;}
    .sidebar-chat { margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(114, 75, 57, 0.2); }
</style>
""", unsafe_allow_html=True)

def stream_gemini(respuesta):
    for chunk in respuesta:
        if chunk.text: yield chunk.text

# ==============================================================================
# 2. BARRA LATERAL (NUEVO MENÚ PREMIUM) Y CHATBOT
# ==============================================================================
with st.sidebar:
    st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 5px;'>🚀 IntelRetail Pro<br><span style='font-size: 14px; color: #CF9D7B; font-weight: 500;'>Strategic Console</span></h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu_opciones = ["Inicio", "Diagnóstico Express", "Auditoría Catálogo", "Simulador & Pauta IA", "Planificador de Metas"]
    menu_iconos = ["house", "lightning", "search", "sliders", "bullseye"]
    menu_ids = ["home", "express", "diagnostico", "simulador", "objetivos"]
    
    try:
        indice_actual = menu_ids.index(st.session_state.pantalla_actual)
    except:
        indice_actual = 0

    seleccion = option_menu(
        menu_title=None,
        options=menu_opciones,
        icons=menu_iconos,
        menu_icon="cast",
        default_index=indice_actual,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#CF9D7B", "font-size": "16px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"2px 0px", "border-radius": "10px", "--hover-color": "rgba(255,255,255,0.05)", "color": "#8F95A3"},
            "nav-link-selected": {"background-color": "rgba(207, 157, 123, 0.15)", "color": "#CF9D7B", "font-weight": "bold", "border": "1px solid rgba(207, 157, 123, 0.5)"},
        }
    )
    
    id_seleccionado = menu_ids[menu_opciones.index(seleccion)]
    if st.session_state.pantalla_actual != id_seleccionado:
        st.session_state.pantalla_actual = id_seleccionado
        st.rerun()

    st.markdown("---")
    
    st.markdown("<p style='font-size: 12px; color: #CF9D7B; font-weight: bold; margin-bottom: 0px;'>DIVISA ACTIVA</p>", unsafe_allow_html=True)
    selector_moneda = st.selectbox("Divisa a mostrar:", ["COP (Pesos Colombianos)", "USD (Dólares)", "MXN (Pesos Mexicanos)"], label_visibility="collapsed")
    if selector_moneda == "COP (Pesos Colombianos)": m_factor, m_simbolo, m_sufijo = st.number_input("Tasa (1 USD = X COP):", 100.0, value=4000.0, step=50.0), "$", " COP"
    elif selector_moneda == "MXN (Pesos Mexicanos)": m_factor, m_simbolo, m_sufijo = st.number_input("Tasa (1 USD = X MXN):", 1.0, value=18.5, step=0.5), "$", " MXN"
    else: m_factor, m_simbolo, m_sufijo = 1.0, "$", " USD"

    aplicar_conversion = st.checkbox("🔄 Convertir datos del archivo", help="Marca esta casilla SOLO si tu archivo Excel está en una moneda diferente.", value=False)

    st.markdown("---")
    
    st.markdown("<p style='font-size: 12px; color: #CF9D7B; font-weight: bold; margin-bottom: 0px;'>INGESTA DE DATOS</p>", unsafe_allow_html=True)
    st.download_button("📥 Descargar Plantilla", generar_plantilla_excel(), "plantilla.xlsx", use_container_width=True)
    
    with st.expander("⚠️ Requisitos del archivo", expanded=False):
        st.markdown("""
        1. **Números puros:** No escribas letras ni signos de moneda.
        2. **Títulos claros:** Usa nombres lógicos en la fila 1 (Ej: *Ventas*, *Producto*).
        3. **Sin Totales:** Sube la base de datos cruda.
        """)

    archivo = st.file_uploader("Sube tus ventas aquí (.csv o .xlsx):", type=['csv', 'xlsx'])
    
    if archivo:
        if archivo.name.endswith('.xlsx'): st.session_state.df_bruto = pd.read_excel(archivo)
        else: st.session_state.df_bruto = pd.read_csv(archivo)
        st.success("¡Datos en memoria listos!")

    st.markdown('<div class="sidebar-chat"></div>', unsafe_allow_html=True)
    st.subheader("💬 Asistente IA")
    
    chat_container = st.container(height=300)
    
    if not ia_activa:
        chat_container.error("⚠️ Falta API Key")
    else:
        for msg in st.session_state.historial_chat:
            with chat_container.chat_message(msg["role"]): st.write(msg["content"])
            
    pregunta = st.chat_input("Consulta a tu IA aquí...")
    if pregunta and ia_activa:
        st.session_state.historial_chat.append({"role": "user", "content": pregunta})
        with chat_container.chat_message("user"): st.write(pregunta)
        
        resumen_datos = st.session_state.df_bruto.head(10).to_string() if not st.session_state.df_bruto.empty else "Sin datos"
        prompt_experto = f"""
        Eres el Asesor IA de IntelRetail Pro. 
        Pantalla actual: {st.session_state.pantalla_actual}. Divisa: {selector_moneda}.
        Datos: {resumen_datos}
        Actúa como consultor experto. Identifica el nicho del negocio y adapta tus recomendaciones.
        Responde breve y muy práctico a: {pregunta}
        """
        with chat_container.chat_message("assistant"):
            try:
                respuesta = modelo_ia.generate_content(prompt_experto, stream=True)
                texto_completo = st.write_stream(stream_gemini(respuesta))
                st.session_state.historial_chat.append({"role": "assistant", "content": texto_completo})
                st.session_state.apuntes_ia += f"\n\n[Consulta Libre - Chat IA]:\n{texto_completo}"
            except Exception as e: 
                st.error("Error de conexión.")

# ==============================================================================
# 3. PROCESAMIENTO MATEMÁTICO INTELIGENTE (GLOBAL) - INTACTO
# ==============================================================================
df_final = pd.DataFrame()

if not st.session_state.df_bruto.empty:
    df_temp = st.session_state.df_bruto.copy()
    df_temp = df_temp.dropna(how='all')
    col_map = {}
    for col in df_temp.columns:
        c = str(col).strip().lower()
        if any(x in c for x in ['venta', 'sales', 'monto']): col_map[col] = 'Sales'
        elif any(x in c for x in ['producto', 'product', 'sku']): col_map[col] = 'Product Name'
        elif any(x in c for x in ['cantidad', 'quantity', 'cant']): col_map[col] = 'Quantity'
        elif any(x in c for x in ['cliente', 'customer']): col_map[col] = 'Customer Name'
            
    df_temp = df_temp.rename(columns=col_map)
    df_temp = df_temp.loc[:, ~df_temp.columns.duplicated()] 
    
    if 'Product Name' in df_temp.columns:
        df_temp['Product Name'] = df_temp['Product Name'].replace(r'^\s*$', np.nan, regex=True)
        df_temp = df_temp.dropna(subset=['Product Name'])
        filtro_totales = df_temp['Product Name'].astype(str).str.lower().str.contains('total', na=False)
        df_temp = df_temp[~filtro_totales]
    
    if 'Sales' in df_temp.columns:
        if 'Product Name' not in df_temp.columns: df_temp['Product Name'] = 'General'
        if 'Quantity' not in df_temp.columns: df_temp['Quantity'] = 1
        if 'Customer Name' not in df_temp.columns: df_temp['Customer Name'] = "Mostrador"
        factor_multiplicador = m_factor if aplicar_conversion else 1.0
        df_temp['Sales'] = pd.to_numeric(df_temp['Sales'], errors='coerce').fillna(0) * factor_multiplicador
        df_temp['Quantity'] = pd.to_numeric(df_temp['Quantity'], errors='coerce').fillna(1)
        
        productos_unicos = df_temp['Product Name'].unique()
        if st.session_state.costos_editados.empty or len(st.session_state.costos_editados) != len(productos_unicos):
            st.session_state.costos_editados = pd.DataFrame({'Product Name': productos_unicos, 'Costo (%)': [70.0]*len(productos_unicos)})
        
        df_final = pd.merge(df_temp, st.session_state.costos_editados, on='Product Name', how='left')
        df_final['Costo_Valor'] = df_final['Sales'] * (df_final['Costo (%)'] / 100)
        df_final['Ganancia_Neta'] = df_final['Sales'] - df_final['Costo_Valor']

# ==============================================================================
# 4. PANTALLAS
# ==============================================================================

if st.session_state.pantalla_actual == "home":
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px; color: #FFFFFF;'>🚀 Bienvenido a IntelRetail Pro</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #8F95A3; margin-bottom: 40px;'><em>Tu copiloto estratégico de inteligencia comercial.</em></h4>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="home-card"><h3>⚡ Diagnóstico Express</h3><p>Calcula tu rentabilidad separando servicios, productos y gastos a 8 semanas.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Diagnóstico", use_container_width=True, type="primary"): cambiar_pantalla("express"); st.rerun()
        st.write("")
        st.markdown('<div class="home-card"><h3>🎛️ Simulador y Marketing IA</h3><p>Proyecta pauta realista y genera campañas automáticas con IA.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Simulador", use_container_width=True): cambiar_pantalla("simulador"); st.rerun()
    with c2:
        st.markdown('<div class="home-card"><h3>🔍 Auditoría de Catálogo</h3><p>Métricas claras sobre la salud de tus productos con ajuste de costos global.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Auditoría", use_container_width=True): cambiar_pantalla("diagnostico"); st.rerun()
        st.write("")
        st.markdown('<div class="home-card"><h3>🎯 Planificador Estratégico</h3><p>Proyecta tarifas, meses pico y tu capacidad operativa tope.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Planificador", use_container_width=True): cambiar_pantalla("objetivos"); st.rerun()

elif st.session_state.pantalla_actual == "express":
    st.header("⚡ Diagnóstico Financiero Avanzado")
    st.markdown("Ingresa los datos fraccionados de los últimos **2 meses** para un cálculo preciso de tu realidad comercial.")
    
    st.subheader("🗓️ 1. Ingresos Semanales (8 Semanas)")
    sw1, sw2, sw3, sw4 = st.columns(4)
    v_s1 = sw1.number_input("Semana 1", value=0.0, step=100000.0)
    v_s2 = sw2.number_input("Semana 2", value=0.0, step=100000.0)
    v_s3 = sw3.number_input("Semana 3", value=0.0, step=100000.0)
    v_s4 = sw4.number_input("Semana 4", value=0.0, step=100000.0)
    
    sw5, sw6, sw7, sw8 = st.columns(4)
    v_s5 = sw5.number_input("Semana 5", value=0.0, step=100000.0)
    v_s6 = sw6.number_input("Semana 6", value=0.0, step=100000.0)
    v_s7 = sw7.number_input("Semana 7", value=0.0, step=100000.0)
    v_s8 = sw8.number_input("Semana 8", value=0.0, step=100000.0)
    
    ventas_totales = v_s1 + v_s2 + v_s3 + v_s4 + v_s5 + v_s6 + v_s7 + v_s8
    
    st.subheader("💼 2. Estructura de Negocio y Egresos (Bimestral)")
    c1, c2, c3 = st.columns(3)
    with c1:
        mix_servicios = st.slider("% Ingresos por Servicios (vs. Productos físicos)", 0, 100, 0)
        margen_promedio = st.slider("Margen Neto Promedio (%)", 0, 90, 0)
    with c2:
        gastos_fijos = st.number_input("Gastos Fijos Acumulados (2 Meses)", value=0.0)
        gastos_variables = st.number_input("Costos Variables Estimados (2 Meses)", value=0.0)
    with c3:
        clientes_mes = st.number_input("Atenciones/Clientes Totales (8 Semanas):", value=0)
    
    utilidad = (ventas_totales * (margen_promedio / 100)) - gastos_fijos - gastos_variables
    punto_eq = (gastos_fijos + gastos_variables) / (margen_promedio / 100) if margen_promedio > 0 else 0
    ticket = ventas_totales / clientes_mes if clientes_mes > 0 else 0
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container {"metric-success" if utilidad >= 0 else "metric-danger"}"><div class="metric-title">UTILIDAD NETA (8 SEMANAS)</div><div class="metric-value">{m_simbolo}{utilidad:,.2f}</div><div class="metric-caption">Ganancia 100% real y libre del periodo.</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">PUNTO DE EQUILIBRIO BIMESTRAL</div><div class="metric-value">{m_simbolo}{punto_eq:,.2f}</div><div class="metric-caption">Venta mínima en 2 meses para no tener pérdidas.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO</div><div class="metric-value">{m_simbolo}{ticket:,.2f}</div><div class="metric-caption">Dinero promedio por cada cliente atendido.</div></div>', unsafe_allow_html=True)

elif st.session_state.pantalla_actual == "diagnostico":
    st.header("📊 Auditoría de Catálogo y Costos")
    if df_final.empty: 
        st.warning("👈 Sube tu archivo de ventas en el menú de la izquierda para comenzar.")
    else:
        st.subheader("⚙️ 1. Ajuste de Costos (Proveedores o Producción)")
        st.markdown("💡 **¿Qué significa esto?** Es el porcentaje del precio de venta que te cuesta adquirir o fabricar el producto.")
        
        c_sl, c_btn = st.columns([3, 1])
        with c_sl: nuevo_costo_global = st.slider("Asignar un costo global a todo el catálogo (%)", 0.0, 100.0, 70.0, 1.0)
        with c_btn:
            st.write("") 
            st.write("")
            if st.button("Aplicar a todos", use_container_width=True, type="primary"):
                st.session_state.costos_editados['Costo (%)'] = float(nuevo_costo_global)
                st.rerun()

        st.markdown("Edita individualmente usando las celdas de la tabla:")
        costos_actualizados = st.data_editor(
            st.session_state.costos_editados, hide_index=True, use_container_width=True,
            column_config={"Costo (%)": st.column_config.NumberColumn("Costo (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f %%")}
        )
        
        if not costos_actualizados.equals(st.session_state.costos_editados):
            st.session_state.costos_editados = costos_actualizados
            df_final = pd.merge(df_temp, st.session_state.costos_editados, on='Product Name', how='left')
            df_final['Costo_Valor'] = df_final['Sales'] * (df_final['Costo (%)'] / 100)
            df_final['Ganancia_Neta'] = df_final['Sales'] - df_final['Costo_Valor']
        
        st.markdown("💾 **Guarda o Recupera tu configuración de costos:**")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            csv_costos = st.session_state.costos_editados.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Descargar Costos (.csv)", data=csv_costos, file_name='mis_costos_guardados.csv', mime='text/csv', use_container_width=True)
        with col_m2:
            archivo_costos = st.file_uploader("Cargar tabla previa de Costos (.csv)", type=['csv'], label_visibility="collapsed")
            if archivo_costos:
                if st.button("♻️ Aplicar Costos de este Archivo", use_container_width=True):
                    try:
                        df_cargado = pd.read_csv(archivo_costos)
                        if 'Product Name' in df_cargado.columns and 'Costo (%)' in df_cargado.columns:
                            st.session_state.costos_editados = df_cargado
                            st.success("✅ ¡Costos restaurados exitosamente!")
                            st.rerun() 
                        else:
                            st.error("❌ El archivo no tiene las columnas correctas.")
                    except Exception as e:
                        st.error("❌ Archivo no válido o corrupto.")
        
        df_g = df_final.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
        ticket_promedio = df_final['Sales'].sum() / len(df_final) if len(df_final) > 0 else 0
        ventas_totales_global = df_final['Sales'].sum()
        ganancia_neta_global = df_final['Ganancia_Neta'].sum()
        
        st.markdown("---")
        st.subheader("🏆 2. Métricas Clave (Análisis Humano)")
        
        c_top1, c_top2 = st.columns(2)
        with c_top1:
            st.markdown(f'<div class="metric-container"><div class="metric-title">VENTAS TOTALES REGISTRADAS</div><div class="metric-value">{m_simbolo}{ventas_totales_global:,.2f}</div><div class="metric-caption">Suma total de todos los ingresos en tu base de datos.</div></div>', unsafe_allow_html=True)
        with c_top2:
            st.markdown(f'<div class="metric-container {"metric-success" if ganancia_neta_global >= 0 else "metric-danger"}"><div class="metric-title">GANANCIA NETA TOTAL</div><div class="metric-value">{m_simbolo}{ganancia_neta_global:,.2f}</div><div class="metric-caption">Dinero libre después de descontar el costo de proveedores/producción.</div></div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            prod_estrella = df_g.loc[df_g["Ganancia_Neta"].idxmax()]["Product Name"] if not df_g.empty else "N/A"
            ganancia_estrella = df_g["Ganancia_Neta"].max() if not df_g.empty else 0
            st.markdown(f'<div class="metric-container metric-success"><div class="metric-title">ESTRELLA (MAYOR GANANCIA NETA)</div><div class="metric-value">{m_simbolo}{ganancia_estrella:,.2f}</div><div class="metric-caption"><b>{prod_estrella}</b><br>El campeón indiscutible. Es el artículo o servicio que más dinero libre y real deja en tu caja.</div></div>', unsafe_allow_html=True)
            prod_lider = df_g.loc[df_g["Quantity"].idxmax()]["Product Name"] if not df_g.empty else "N/A"
            cant_lider = df_g["Quantity"].max() if not df_g.empty else 0
            st.markdown(f'<div class="metric-container"><div class="metric-title">LÍDER EN ROTACIÓN</div><div class="metric-value">{cant_lider} Unds</div><div class="metric-caption"><b>{prod_lider}</b><br>El favorito del público. Es el que más unidades vende y atrae el tráfico recurrente a tu local.</div></div>', unsafe_allow_html=True)
        with c2:
            prod_dormido = df_g.loc[df_g["Quantity"].idxmin()]["Product Name"] if not df_g.empty else "N/A"
            cant_dormido = df_g["Quantity"].min() if not df_g.empty else 0
            st.markdown(f'<div class="metric-container metric-danger"><div class="metric-title">DORMIDO (MENOR ROTACIÓN)</div><div class="metric-value">{cant_dormido} Unds</div><div class="metric-caption"><b>{prod_dormido}</b><br>¡Alerta roja! Este producto está estancado y tienes dinero congelado. Necesita promoción urgente.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO GLOBAL</div><div class="metric-value">{m_simbolo}{ticket_promedio:,.2f}</div><div class="metric-caption">Esta es la facturación media histórica extraída directamente de tu base de datos.</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        col_export, col_ia = st.columns(2)
        
        with col_export:
            st.subheader("💾 Exportar Datos")
            st.markdown("Descarga tu base de datos y un resumen ejecutivo en texto con todas las estrategias de la IA de esta sesión.")
            st.download_button(label="📥 Descargar Auditoría (.xlsx)", data=df_to_excel(df_final), file_name='auditoria_intelretail.xlsx', mime='application/vnd.ms-excel', use_container_width=True)
            
            txt_reporte = generar_informe_texto(ventas_totales_global, ganancia_neta_global, m_simbolo, st.session_state.apuntes_ia)
            st.download_button(label="📥 Descargar Informe Ejecutivo (.txt)", data=txt_reporte, file_name='informe_narrativo.txt', mime='text/plain', use_container_width=True)
            
        with col_ia:
            st.subheader("🧠 Consultor IA Ejecutivo")
            st.markdown("Un solo clic para leer tus métricas actuales y obtener estrategias gerenciales de alto impacto.")
            if st.button("✨ Generar Análisis Automático", use_container_width=True, type="primary"):
                if not ia_activa: st.error("⚠️ IA desactivada (Falta API Key).")
                else:
                    prompt_analisis = f"Eres un consultor de negocios retail experto. Leyendo los datos de este usuario, su producto estrella (el que más ganancia neta deja) es '{prod_estrella}'. Su producto dormido (el de menor rotación) es '{prod_dormido}'. Su ticket promedio es {ticket_promedio}. Dame 3 viñetas cortas, muy directas y accionables con estrategias precisas para mejorar sus ventas conjuntas y rotar el inventario estancado. Usa lenguaje corporativo, sin saludos iniciales."
                    try:
                        res_analisis = modelo_ia.generate_content(prompt_analisis, stream=True)
                        st.markdown("#### 💡 Nueva Estrategia Sugerida:")
                        texto_estrategia = st.write_stream(stream_gemini(res_analisis))
                        st.session_state.apuntes_ia += f"\n\n[Análisis de Auditoría]:\n{texto_estrategia}"
                        st.rerun() 
                    except Exception as e: 
                        st.error("Error contactando a la IA.")
            
            if st.session_state.apuntes_ia != "":
                st.write("")
                with st.expander("📝 Mis Apuntes de esta Sesión (Historial)", expanded=True):
                    st.markdown(st.session_state.apuntes_ia)
        
        st.markdown("---")
        st.subheader("🎯 3. Matriz BCG: Rentabilidad vs. Rotación")
        fig_bcg = px.scatter(df_g, x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name', hover_name='Product Name', labels={'Quantity': 'Unidades Vendidas', 'Ganancia_Neta': 'Ganancia Neta Libre'})
        fig_bcg.update_layout(showlegend=True, height=500, margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#8F95A3'))
        st.plotly_chart(fig_bcg, use_container_width=True)

        st.markdown("---")
        st.subheader("📊 4. Análisis Profundo del Negocio")
        tipo_analisis = st.radio("Selecciona la métrica:", ["📦 Top 10 Productos (Por Unidades Vendidas)", "💰 Top 10 Productos (Por Ingreso Bruto)", "👥 Top 10 Clientes (Por Facturación)"], horizontal=True)

        if "Clientes" in tipo_analisis:
            data_plot = df_final.groupby('Customer Name')['Sales'].sum().reset_index().sort_values('Sales', ascending=False).head(10)
            fig_extra = px.bar(data_plot, x='Sales', y='Customer Name', orientation='h', color='Sales', color_continuous_scale='Blues', labels={'Sales': 'Facturación Total', 'Customer Name': 'Nombre del Cliente'})
        elif "Ingreso" in tipo_analisis:
            data_plot = df_final.groupby('Product Name')['Sales'].sum().reset_index().sort_values('Sales', ascending=False).head(10)
            fig_extra = px.bar(data_plot, x='Sales', y='Product Name', orientation='h', color='Sales', color_continuous_scale='Greens', labels={'Sales': 'Ingresos Brutos Generados', 'Product Name': 'Producto'})
        else:
            data_plot = df_final.groupby('Product Name')['Quantity'].sum().reset_index().sort_values('Quantity', ascending=False).head(10)
            fig_extra = px.bar(data_plot, x='Quantity', y='Product Name', orientation='h', color='Quantity', color_continuous_scale='Oranges', labels={'Quantity': 'Unidades Totales Vendidas', 'Product Name': 'Producto'})

        fig_extra.update_layout(height=450, showlegend=False, yaxis=dict(autorange="reversed"), margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#8F95A3'))
        st.plotly_chart(fig_extra, use_container_width=True)

elif st.session_state.pantalla_actual == "simulador":
    st.header("🎛️ Simulador Financiero y Marketing IA")
    
    if df_final.empty: 
        st.warning("👈 Sube tu archivo de ventas en el menú de la izquierda.")
    else:
        st.markdown("### 1. Palancas Comerciales:")
        c1, c2, c3, c4 = st.columns(4)
        
        precio = c1.slider("Ajuste de Precios (%)", -50, 50, 0)
        
        step_val = int(5 * m_factor)     
        pauta = c2.number_input(f"Presupuesto Pauta ({m_sufijo})", min_value=0, value=0, step=step_val)
        
        costo_lead = c3.number_input(f"Costo por Mensaje/Contacto ({m_sufijo})", min_value=0.1, value=2000.0 if m_sufijo == " COP" else 0.5, help="¿Cuánto estimas que te cuesta hacer que un cliente nuevo te escriba al WhatsApp o pregunte por un producto?")
        
        tasa_conversion = c4.slider("% de Cierre de Ventas", 1.0, 100.0, 5.0, 0.5, help="De cada 100 personas que te preguntan, ¿cuántas terminan comprando realmente?")
        
        factor_precio = 1 + (precio / 100)
        factor_cantidad = 1 - (precio / 100 * 0.5) 
        
        leads_generados = int(pauta / costo_lead) if costo_lead > 0 else 0
        clientes_reales = int(leads_generados * (tasa_conversion / 100))
        
        st.info(f"💡 **Proyección de Campaña:** Con este presupuesto, es **posible** que atraigas aproximadamente **{leads_generados} mensajes o contactos potenciales**. Si mantienes un nivel de cierre de ventas del {tasa_conversion}%, **podrías** conseguir **{clientes_reales} clientes nuevos**.")
        
        if st.session_state.costos_editados.empty:
            costo_promedio_porcentaje = 0.70
        else:
            costo_promedio_porcentaje = st.session_state.costos_editados['Costo (%)'].mean() / 100
            if pd.isna(costo_promedio_porcentaje): 
                costo_promedio_porcentaje = 0.70

        ventas_actuales_tot = df_final['Sales'].sum()
        costo_actual_tot = (df_final['Sales'] * costo_promedio_porcentaje).sum()
        ganancia_actual_tot = df_final['Ganancia_Neta'].sum()

        v_sim = (df_final['Sales'] * factor_precio * factor_cantidad).sum() + (clientes_reales * (ventas_actuales_tot / df_final['Quantity'].sum() if df_final['Quantity'].sum() > 0 else 0) * factor_precio)
        c_sim = (df_final['Sales'] * costo_promedio_porcentaje * factor_cantidad).sum() + (clientes_reales * (ventas_actuales_tot / df_final['Quantity'].sum() if df_final['Quantity'].sum() > 0 else 0) * costo_promedio_porcentaje)
        g_sim = v_sim - c_sim - pauta
        
        st.markdown("### ⚖️ Comparador de Escenarios Estratégicos")
        col_esc1, col_esc2 = st.columns(2)
        with col_esc1:
            if st.button("💾 Guardar como Escenario A", use_container_width=True):
                st.session_state.escenario_a = {
                    'Ajuste_Precios': precio,
                    'Pauta': pauta,
                    'Costo_Lead': costo_lead,
                    'Conversion': tasa_conversion,
                    'Clientes_Nuevos': clientes_reales,
                    'Ventas': v_sim,
                    'Costo_Inv': c_sim,
                    'Ganancia': g_sim
                }
                st.success("✅ ¡Escenario A guardado! Ahora mueve las palancas para armar tu Plan B y compáralos en la gráfica y en el Excel.")
        with col_esc2:
            if st.session_state.escenario_a is not None:
                if st.button("🗑️ Borrar Escenario A", use_container_width=True):
                    st.session_state.escenario_a = None
                    st.rerun()

        barras_grafica = [
            go.Bar(name='Actual (Realidad)', x=['Ventas Totales', 'Ganancia Neta'], y=[ventas_actuales_tot, ganancia_actual_tot], marker_color='#CF9D7B', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside'),
            go.Bar(name='Escenario Vivo (Proyección)', x=['Ventas Totales', 'Ganancia Neta'], y=[v_sim, g_sim], marker_color='#00CC96', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside')
        ]
        
        if st.session_state.escenario_a is not None:
            barras_grafica.insert(1, go.Bar(name='Escenario A (Guardado)', x=['Ventas Totales', 'Ganancia Neta'], y=[st.session_state.escenario_a['Ventas'], st.session_state.escenario_a['Ganancia']], marker_color='#FFA15A', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside'))
        
        fig = go.Figure(data=barras_grafica)
        fig.update_layout(barmode='group', height=400, margin=dict(t=50), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#8F95A3'))
        st.plotly_chart(fig, use_container_width=True)

        export_data = {
            "Métrica / Parámetro": [
                "[ PARÁMETROS ESTRATÉGICOS ]",
                "Ajuste de Precios (%)",
                f"Presupuesto Pauta ({m_sufijo.strip()})",
                f"Costo por Mensaje/Contacto ({m_sufijo.strip()})",
                "% de Cierre de Ventas",
                "Nuevos Clientes Estimados",
                "",
                "[ RESULTADOS FINANCIEROS ]",
                "Ventas Totales Brutas",
                "Costo de Inventario (Estimado)",
                "Inversión en Publicidad",
                "Ganancia Neta Libre"
            ],
            "Escenario Actual (Realidad)": [
                "", "0%", 0, "N/A", "N/A", "N/A", "", "",
                ventas_actuales_tot,
                costo_actual_tot,
                0,
                ganancia_actual_tot
            ]
        }

        if st.session_state.escenario_a is not None:
            export_data["Escenario A (Guardado)"] = [
                "",
                f"{st.session_state.escenario_a['Ajuste_Precios']}%",
                st.session_state.escenario_a['Pauta'],
                st.session_state.escenario_a['Costo_Lead'],
                f"{st.session_state.escenario_a['Conversion']}%",
                st.session_state.escenario_a['Clientes_Nuevos'],
                "", "",
                st.session_state.escenario_a['Ventas'],
                st.session_state.escenario_a['Costo_Inv'],
                st.session_state.escenario_a['Pauta'],
                st.session_state.escenario_a['Ganancia']
            ]

        export_data["Escenario Vivo (Proyección)"] = [
            "",
            f"{precio}%", pauta, costo_lead, f"{tasa_conversion}%", clientes_reales,
            "", "",
            v_sim, c_sim, pauta, g_sim
        ]

        df_sim_export = pd.DataFrame(export_data)
        st.download_button(label="📥 Descargar Comparativo de Simulación (Excel)", data=df_to_excel(df_sim_export), file_name='proyeccion_simulador_completa.xlsx', mime='application/vnd.ms-excel')
        
        st.markdown("---")
        st.subheader("📱 2. Distribución Estratégica de Pauta")
        if pauta > 0:
            pauta_usd = pauta / m_factor
            if pauta_usd < 40:
                plataformas, valores, colores = ['Meta (Instagram/Facebook)'], [pauta], ['#E1306C']
                st.info("💡 **Micro-Presupuesto:** 100% a **Meta Ads (Instagram/FB)**. Evitamos diluir tu dinero.")
            elif pauta_usd < 150:
                plataformas, valores, colores = ['Meta (Instagram/Facebook)', 'Google Ads (Búsqueda)'], [pauta * 0.70, pauta * 0.30], ['#E1306C', '#4285F4']
                st.info("💡 **Multicanal Moderada:** 70% visual en **Meta** + 30% en **Google Ads**.")
            else:
                plataformas, valores, colores = ['Meta (Instagram/Facebook)', 'Google Ads (Búsqueda)', 'TikTok Ads'], [pauta * 0.50, pauta * 0.30, pauta * 0.20], ['#E1306C', '#4285F4', '#00F2FE'] 
                st.info("💡 **Integral Omnicanal:** Tu presupuesto alcanza para **TikTok Ads** (20%), **Meta** (50%) y **Google** (30%).")
                
            dist_data = pd.DataFrame({'Plataforma': plataformas, 'Asignación': valores})
            fig_pauta = px.pie(dist_data, names='Plataforma', values='Asignación', hole=0.4, color_discrete_sequence=colores)
            fig_pauta.update_traces(textinfo='percent+label')
            fig_pauta.update_layout(showlegend=False, margin=dict(t=30, b=10, l=10, r=10), height=350, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#8F95A3'))
            st.plotly_chart(fig_pauta, use_container_width=True)
        else:
            st.info("💡 Asigna un presupuesto en la parte superior para ver la distribución recomendada.")

        st.markdown("---")
        st.subheader("🤖 3. Suite IA de Creación de Campañas")
        col_m1, col_m2 = st.columns(2)
        with col_m1: prod_promo = st.text_input("¿Qué vas a promocionar?")
        with col_m2: tono_marca = st.selectbox("Tono de comunicación:", ["Comercial y Directo", "Divertido y Cercano", "Urgente (Oferta)", "Elegante y Premium"])
            
        if st.button("✨ Generar Campaña", type="primary"):
            if not ia_activa: st.error("⚠️ IA desactivada (Falta API Key).")
            elif not prod_promo: st.warning("⚠️ Escribe el producto a promocionar.")
            else:
                prompt_marketing = f"Eres un Copywriter experto. Crea una campaña para '{prod_promo}' con tono '{tono_marca}'. Entrega: 1) Copy para Meta con emojis y CTA. 2) 3 Títulos cortos para Google Ads. 3) 1 Idea de diseño visual/arte."
                try:
                    res_mkt = modelo_ia.generate_content(prompt_marketing, stream=True)
                    st.markdown("#### 💡 Nueva Campaña Generada:")
                    texto_campana = st.write_stream(stream_gemini(res_mkt))
                    st.session_state.apuntes_ia += f"\n\n[Campaña de Marketing para '{prod_promo}']: \n{texto_campana}"
                    st.rerun()
                except Exception as e: 
                    st.error("Error contactando a la IA.")
        
        if st.session_state.apuntes_ia != "":
            st.write("")
            with st.expander("📝 Mis Apuntes de esta Sesión (Historial)", expanded=True):
                st.markdown(st.session_state.apuntes_ia)

elif st.session_state.pantalla_actual == "objetivos":
    st.header("🎯 Planificador Estratégico (Modo Dios)")
    
    st.markdown("### Configura el entorno operativo de tu negocio:")
    c1, c2, c3, c4 = st.columns(4)
    with c1: meta = st.number_input(f"Ganancia Deseada ({m_sufijo}):", value=0.0, step=500000.0)
    with c2: meses = st.slider("Horizonte (Meses):", 1, 12, 1)
    with c3: gastos = st.number_input(f"Gastos Fijos/Mes ({m_sufijo}):", value=0.0, step=100000.0)
    with c4: capacidad_max = st.number_input("Tope Operativo Diario:", value=0)
        
    st.markdown("### Palancas Estratégicas Avanzadas:")
    p1, p2 = st.columns(2)
    with p1: estacionalidad = st.slider("🔥 Multiplicador de Temporada Alta (%)", 0, 50, 0)
    with p2: ajuste_tarifas = st.slider("📈 Simulador de Actualización de Tarifas (%)", 0, 30, 0)
    
    costo_prom_actual = st.session_state.costos_editados['Costo (%)'].mean() if not st.session_state.costos_editados.empty else 70.0
    margen_comercial = (100 - costo_prom_actual) / 100
    
    gastos_totales = gastos * meses
    meta_ajustada_temporada = meta * (1 - (estacionalidad/100))
    ventas_totales_req = (meta_ajustada_temporada + gastos_totales) / margen_comercial if margen_comercial > 0 else 0
    ventas_diarias_req = ventas_totales_req / (30 * meses)
    
    t_prom_base = df_final['Sales'].sum() / len(df_final) if not df_final.empty else (ventas_totales_req / (300 * meses))
    t_prom_simulado = t_prom_base * (1 + (ajuste_tarifas/100))
    
    clientes_diarios = int(np.ceil(ventas_diarias_req / t_prom_simulado)) if t_prom_simulado > 0 else 0
    alerta_capacidad = "metric-danger" if clientes_diarios > capacidad_max and capacidad_max > 0 else "metric-warning"
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container metric-success"><div class="metric-title">FACTURACIÓN TOTAL REQUERIDA</div><div class="metric-value">{m_simbolo}{ventas_totales_req:,.2f}</div><div class="metric-caption">Ventas necesarias estimadas en {meses} mes(es).</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container"><div class="metric-title">META DE VENTA DIARIA</div><div class="metric-value">{m_simbolo}{ventas_diarias_req:,.2f}</div><div class="metric-caption">Venta mínima promedio cada día para llegar al objetivo.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container {alerta_capacidad}"><div class="metric-title">CLIENTES DIARIOS REQUERIDOS</div><div class="metric-value">{clientes_diarios} Compras/Día</div><div class="metric-caption">Límite Operativo configurado: {capacidad_max} atenciones al día.</div></div>', unsafe_allow_html=True)
    
    if clientes_diarios > capacidad_max and capacidad_max > 0:
        st.error(f"🚨 ¡ALERTA OPERATIVA! Tu meta requiere {clientes_diarios} clientes diarios, pero tu negocio solo soporta {capacidad_max}. Debes subir tus tarifas, reducir tus costos operativos o extender el plazo de la meta.")
