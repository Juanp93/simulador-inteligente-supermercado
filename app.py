import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
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
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# GESTIÓN DE ESTADO (NAVEGACIÓN MULTIPANTALLA)
# ==============================================================================
if "pantalla_actual" not in st.session_state:
    st.session_state.pantalla_actual = "home"

def cambiar_pantalla(nombre):
    st.session_state.pantalla_actual = nombre

# ==============================================================================
# BARRA LATERAL: NAVEGACIÓN Y MONEDA (GLOBALES)
# ==============================================================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2800/2800118.png", width=60) # Ícono decorativo
st.sidebar.title("IntelRetail Pro")

st.sidebar.markdown("---")
st.sidebar.header("🧭 Navegación")
opciones_menu = {
    "🏠 Inicio (Home)": "home",
    "⚡ Diagnóstico Express (Sin CSV)": "express",
    "🔍 Auditoría y BI de Catálogo": "diagnostico",
    "🎛️ Simulador y Pauta Digital": "simulador",
    "🎯 Planificador por Objetivos": "objetivos"
}

# Encontrar el índice actual
indice_actual = list(opciones_menu.values()).index(st.session_state.pantalla_actual)
seleccion_nav = st.sidebar.radio("Ir a:", list(opciones_menu.keys()), index=indice_actual)
st.session_state.pantalla_actual = opciones_menu[seleccion_nav]

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
# FUNCIONES CORE CON CACHÉ
# ==============================================================================
@st.cache_data
def generar_plantilla_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_datos = pd.DataFrame({
            'Fecha': ['01/10/2026', '02/10/2026', '03/10/2026'],
            'Producto': ['Arroz Premium 1kg', 'Aceite Vegetal 900ml', 'Leche Entera 1L'],
            'Ventas': [1.25, 2.50, 1.10],
            'Cantidad': [10, 5, 12],
            'Cliente': ['Cliente Mostrador', 'Supermercado Central', 'Tienda Doña Rosa']
        })
        df_datos.to_excel(writer, sheet_name='Datos_Ventas', index=False)
    return output.getvalue()

@st.cache_data
def limpiar_y_preparar_datos(file_bytes, filename, porcentaje_costo_proveedor, factor_divisa):
    df_temp = None
    buffer = io.BytesIO(file_bytes) if isinstance(file_bytes, bytes) else file_bytes
    
    if filename.endswith('.xlsx'):
        df_temp = pd.read_excel(buffer)
    else:
        for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                buffer.seek(0)
                df_temp = pd.read_csv(buffer, encoding=enc)
                break
            except:
                continue
                
    if df_temp is None:
        return pd.DataFrame()

    column_map = {}
    for col in df_temp.columns:
        col_clean = str(col).strip().lower()
        if any(x in col_clean for x in ['fecha', 'order date', 'date', 'dia']): column_map[col] = 'Order Date'
        elif any(x in col_clean for x in ['venta', 'sales', 'ingreso', 'monto', 'total']): column_map[col] = 'Sales'
        elif any(x in col_clean for x in ['producto', 'product', 'item', 'articulo', 'sku']): column_map[col] = 'Product Name'
        elif any(x in col_clean for x in ['cantidad', 'quantity', 'unidades', 'cant']): column_map[col] = 'Quantity'
        elif any(x in col_clean for x in ['cliente', 'customer', 'comprador']): column_map[col] = 'Customer Name'
            
    df_temp = df_temp.rename(columns=column_map)
    
    if 'Sales' not in df_temp.columns: return pd.DataFrame()
    if 'Product Name' not in df_temp.columns: df_temp['Product Name'] = "Artículo General"
    if 'Customer Name' not in df_temp.columns: df_temp['Customer Name'] = "Mostrador"
        
    df_temp = df_temp.dropna(subset=['Sales'])
    df_temp['Sales'] = pd.to_numeric(df_temp['Sales'], errors='coerce')
    df_temp = df_temp[df_temp['Sales'] > 0]
    
    if 'Order Date' in df_temp.columns:
        df_temp['Order Date'] = pd.to_datetime(df_temp['Order Date'], format='%d/%m/%Y', errors='coerce')
    else:
        df_temp['Order Date'] = pd.Timestamp.now()
        
    df_temp['Sales'] = df_temp['Sales'] * factor_divisa
    
    if 'Quantity' not in df_temp.columns or df_temp['Quantity'].isnull().all():
        np.random.seed(42)
        df_temp['Quantity'] = np.random.randint(1, 6, size=len(df_temp))
    else:
        df_temp['Quantity'] = pd.to_numeric(df_temp['Quantity'], errors='coerce').fillna(1)
        
    factor_costo = porcentaje_costo_proveedor / 100
    df_temp['Costo_Proveedor'] = df_temp['Sales'] * factor_costo
    df_temp['Ganancia_Neta'] = df_temp['Sales'] - df_temp['Costo_Proveedor']
    return df_temp

def analizar_datos_avanzados(df_limpio):
    df_agrupado = df_limpio.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
    df_limpio['Precio_Unitario'] = df_limpio['Sales'] / df_limpio['Quantity']
    df_limpio['Dia_Semana'] = df_limpio['Order Date'].dt.day_name().map({'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}).fillna('Indeterminado')
    
    df_pareto = df_agrupado.sort_values(by='Sales', ascending=False).copy()
    df_pareto['Pct_Acum'] = (df_pareto['Sales'].cumsum() / df_pareto['Sales'].sum()) * 100
    skus_pareto = max(1, len(df_pareto[df_pareto['Pct_Acum'] <= 80]))

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
        "skus_pareto": skus_pareto
    }

def simular_escenario_negocio(df_original, cambio_precio_porcentaje, presupuesto_marketing, porcentaje_costo_proveedor):
    # Simplificación del simulador para el bloque principal
    factor_precio = 1 + (cambio_precio_porcentaje / 100)
    factor_cantidad = 1 - (cambio_precio_porcentaje / 100 * 0.5) 
    
    clientes_nuevos = int((presupuesto_marketing * 2.0) / (3 * m_factor)) if presupuesto_marketing < (20 * m_factor) else int(((presupuesto_marketing * 0.35 * 3.5) + (presupuesto_marketing * 0.30 * 3.0) + (presupuesto_marketing * 0.20 * 2.5) + (presupuesto_marketing * 0.15 * 2.0)) / (4 * m_factor))
    unidades_extra = clientes_nuevos * 1.5
    
    ventas_historicas = df_original['Sales'].sum()
    ganancia_historica = df_original['Ganancia_Neta'].sum()
    
    precio_medio = df_original['Sales'].mean() / df_original['Quantity'].mean()
    ventas_simuladas = (df_original['Sales'] * factor_precio * factor_cantidad).sum() + (unidades_extra * precio_medio * factor_precio)
    
    costo_prov_pct = porcentaje_costo_proveedor / 100
    costos_simulados = (df_original['Sales'] * costo_prov_pct * factor_cantidad).sum() + (unidades_extra * precio_medio * costo_prov_pct)
    
    ganancia_simulada = ventas_simuladas - costos_simulados - presupuesto_marketing
    return ventas_historicas, ganancia_historica, ventas_simuladas, ganancia_simulada, clientes_nuevos

# ==============================================================================
# BARRA LATERAL DINÁMICA: SOLO SE MUESTRA EN PANTALLAS DE DATOS
# ==============================================================================
df_app = pd.DataFrame()
slider_costo_prov = 70

if st.session_state.pantalla_actual in ["diagnostico", "simulador", "objetivos"]:
    st.sidebar.markdown("---")
    st.sidebar.header("📁 Ingesta de Datos (CSV o Excel)")
    st.sidebar.download_button("📥 Descargar Plantilla Oficial", generar_plantilla_excel(), "plantilla_intelretail.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    archivo_usuario = st.sidebar.file_uploader("Sube tu archivo de ventas:", type=['csv', 'xlsx'])
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Costos Operativos")
    slider_costo_prov = st.sidebar.slider("Costo de Adquisición (%)", 10, 90, 70, 5)

    if archivo_usuario:
        df_app = limpiar_y_preparar_datos(archivo_usuario.getvalue(), archivo_usuario.name, slider_costo_prov, m_factor)
        if not df_app.empty: st.sidebar.success("¡Datos cargados con éxito!")
    else:
        try:
            with open('train.csv', 'rb') as f: df_app = limpiar_y_preparar_datos(f.read(), 'train.csv', slider_costo_prov, m_factor)
            st.sidebar.info("Modo demostración activo.")
        except: pass

if not df_app.empty:
    analisis = analizar_datos_avanzados(df_app)

# ==============================================================================
# PANTALLA 1: HOME PAGE
# ==============================================================================
if st.session_state.pantalla_actual == "home":
    st.title("🚀 Bienvenido a IntelRetail Pro")
    st.markdown("#### *El copiloto estratégico de inteligencia de negocios para microempresarios.*")
    st.write("")
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown('<div class="home-card"><h3>⚡ Diagnóstico Express</h3><p>Ideal si no tienes archivo. Ingresa números estimados y obtén tu punto de equilibrio.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Diagnóstico Express ➡️", use_container_width=True, type="primary"): cambiar_pantalla("express"); st.rerun()
        st.write("")
        st.markdown('<div class="home-card"><h3>🎛️ Simulador y Pauta Digital</h3><p>Proyecta cómo afectará tus utilidades subir precios e invierte con IA.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Simulador Financiero ➡️", use_container_width=True): cambiar_pantalla("simulador"); st.rerun()
    with col_h2:
        st.markdown('<div class="home-card"><h3>🔍 Auditoría y BI de Catálogo</h3><p>Carga tus ventas para descubrir tu producto estrella, Pareto 80/20 y matriz BCG.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Auditoría de Catálogo ➡️", use_container_width=True): cambiar_pantalla("diagnostico"); st.rerun()
        st.write("")
        st.markdown('<div class="home-card"><h3>🎯 Planificador de Metas</h3><p>Define cuánto dinero quieres ganar y calcula cuántas ventas diarias necesitas.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Planificador de Metas ➡️", use_container_width=True): cambiar_pantalla("objetivos"); st.rerun()

# ==============================================================================
# PANTALLA 2: DIAGNÓSTICO EXPRESS
# ==============================================================================
elif st.session_state.pantalla_actual == "express":
    st.header("⚡ Diagnóstico Rápido para Micro-Comercios")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        venta = st.number_input(f"Venta mensual estimada ({m_sufijo}):", value=5000000.0)
        margen = st.slider("Margen de ganancia (%):", 5, 80, 30)
    with col_e2:
        gastos = st.number_input(f"Gastos fijos ({m_sufijo}):", value=1200000.0)
        clientes = st.number_input("Clientes al mes:", value=350)
    
    utilidad = (venta * (margen / 100)) - gastos
    punto_eq = gastos / (margen / 100) if margen > 0 else 0
    
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.markdown(f'<div class="metric-container {"metric-success" if utilidad > 0 else "metric-danger"}"><div class="metric-title">UTILIDAD NETA</div><div class="metric-value">{m_simbolo}{utilidad:,.2f}</div></div>', unsafe_allow_html=True)
    col_r2.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">PUNTO DE EQUILIBRIO</div><div class="metric-value">{m_simbolo}{punto_eq:,.2f}</div></div>', unsafe_allow_html=True)
    col_r3.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO</div><div class="metric-value">{m_simbolo}{venta/clientes:,.2f}</div></div>', unsafe_allow_html=True)

# ==============================================================================
# PANTALLA 3: AUDITORÍA Y BI
# ==============================================================================
elif st.session_state.pantalla_actual == "diagnostico":
    st.header("📊 Auditoría y BI de Catálogo")
    if df_app.empty: st.warning("Carga tus datos en el menú lateral.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-container"><div class="metric-title">🏆 ESTRELLA (UTILIDAD)</div><div class="metric-value">{m_simbolo}{analisis["ganancia_estrella"]:,.0f}</div><div class="metric-caption">{analisis["estrella"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-container"><div class="metric-title">🥇 MÁS VENDIDO</div><div class="metric-value">{analisis["cant_mas_vendido"]} Unds</div><div class="metric-caption">{analisis["mas_vendido"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-container metric-danger"><div class="metric-title">💤 DORMIDO (RIESGO)</div><div class="metric-value">{analisis["cant_menos_vendido"]} Unds</div><div class="metric-caption">{analisis["menos_vendido"]}</div></div>', unsafe_allow_html=True)
        
        st.subheader("🎯 Matriz de Inventario BCG (Rotación vs. Margen)")
        st.plotly_chart(px.scatter(analisis['df_agrupado'], x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name', hover_name='Product Name', height=350).update_layout(showlegend=False), use_container_width=True)

# ==============================================================================
# PANTALLA 4: SIMULADOR E INTEGRACIÓN IA
# ==============================================================================
elif st.session_state.pantalla_actual == "simulador":
    st.header("🎛️ Simulador Financiero y Estrategia Digital")
    if df_app.empty: st.warning("Carga tus datos en el menú lateral.")
    else:
        c1, c2 = st.columns(2)
        precio = c1.slider("Ajuste de Precios (%)", -20, 20, 0)
        pauta = c2.slider("Presupuesto de Pauta", 0, int(5000 * m_factor), 0, int(100 * m_factor))
        
        v_h, g_h, v_s, g_s, cl_n = simular_escenario_negocio(df_app, precio, pauta, slider_costo_prov)
        
        st.plotly_chart(go.Figure(data=[
            go.Bar(name='Histórico', x=['Ventas', 'Ganancia'], y=[v_h, g_h], marker_color='#636EFA'),
            go.Bar(name='Proyectado', x=['Ventas', 'Ganancia'], y=[v_s, g_s], marker_color='#00CC96')
        ]).update_layout(barmode='group', height=350), use_container_width=True)

        if pauta > 0:
            st.markdown("---")
            st.subheader("💡 Consultoría Estratégica de Contenido")
            # AQUÍ VOLVIERON LAS RECOMENDACIONES CLÁSICAS
            with st.expander("Ver recomendaciones de contenido multiplataforma", expanded=True):
                col_c1, col_c2 = st.columns(2)
                col_c1.markdown(f"""
                **📸 Para Instagram:**
                * **Idea:** Carruseles mostrando los productos que más se compran juntos.
                * **Gancho:** Usa tu producto estrella (**{analisis['estrella']}**) en promociones cruzadas.
                """)
                col_c2.markdown(f"""
                **🎵 Para TikTok:**
                * **Idea:** Graba el "detrás de escena" empacando pedidos.
                * **Audio/Ubicación:** Audios en tendencia etiquetando tu ciudad/barrio.
                """)
            
            st.markdown("---")
            # MÓDULO LISTO PARA CONECTAR LA IA EN EL PRÓXIMO PASO
            st.subheader("🧠 Asesor Creativo con Inteligencia Artificial (Gemini)")
            st.markdown("Deja que la IA lea tu catálogo y genere los copys exactos de tus campañas de hoy.")
            api_key = st.text_input("Ingresa tu API Key de Gemini (Opcional por ahora):", type="password")
            
            if st.button("✨ Generar Estrategia Única con IA"):
                if api_key:
                    st.success("¡Conexión exitosa! (Aquí programaremos el prompt para que la IA lea tu CSV y redacte los copys perfectos para tu nicho de mercado).")
                else:
                    st.warning("⚠️ Para utilizar el asesor automático, necesitas ingresar una API Key gratuita de Google AI Studio.")

# ==============================================================================
# PANTALLA 5: PLANIFICADOR DE METAS
# ==============================================================================
elif st.session_state.pantalla_actual == "objetivos":
    st.header("🎯 Planificador por Objetivos (Simulador Inverso)")
    meta = st.number_input(f"Meta de ganancia neta este mes ({m_sufijo}):", value=3000000.0)
    gastos = st.number_input(f"Gastos fijos del período ({m_sufijo}):", value=1500000.0)
    
    ventas_nec = (meta + gastos) / ((100 - slider_costo_prov)/100)
    st.markdown(f'<div class="metric-container metric-success"><div class="metric-title">FACTURACIÓN REQUERIDA</div><div class="metric-value">{m_simbolo}{ventas_nec:,.2f}</div></div>', unsafe_allow_html=True)
