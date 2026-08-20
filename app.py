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
# GESTIÓN DE ESTADO (NAVEGACIÓN MULTIPANTALLA TIPO APP MÓVIL)
# ==============================================================================
if "pantalla_actual" not in st.session_state:
    st.session_state.pantalla_actual = "home"

def cambiar_pantalla(nombre):
    st.session_state.pantalla_actual = nombre

# ==============================================================================
# LOCALIZACIÓN Y GESTIÓN DE DIVISAS DINÁMICA
# ==============================================================================
st.sidebar.header("💱 Configuración de Moneda")
selector_moneda = st.sidebar.selectbox("Divisa de Visualización:", ["COP (Pesos Colombianos)", "USD (Dólares)", "MXN (Pesos Mexicanos)"])

if selector_moneda == "COP (Pesos Colombianos)":
    m_factor = st.sidebar.number_input("Tasa de Cambio (1 USD = X COP):", min_value=100.0, value=4000.0, step=50.0)
    m_simbolo = "$"
    m_sufijo = " COP"
elif selector_moneda == "MXN (Pesos Mexicanos)":
    m_factor = st.sidebar.number_input("Tasa de Cambio (1 USD = X MXN):", min_value=1.0, value=18.5, step=0.5)
    m_simbolo = "$"
    m_sufijo = " MXN"
else:
    m_factor = 1.0
    m_simbolo = "$"
    m_sufijo = " USD"

# ==============================================================================
# GENERADOR DE PLANTILLA EXCEL (.XLSX) PROFESIONAL
# ==============================================================================
@st.cache_data
def generar_plantilla_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_datos = pd.DataFrame({
            'Fecha': ['01/10/2026', '02/10/2026', '03/10/2026', '04/10/2026', '05/10/2026'],
            'Producto': ['Arroz Premium 1kg', 'Aceite Vegetal 900ml', 'Leche Entera 1L', 'Jabón Multiusos', 'Café Tostado 500g'],
            'Ventas': [1.25, 2.50, 1.10, 0.85, 3.20],
            'Cantidad': [10, 5, 12, 8, 15],
            'Cliente': ['Cliente Mostrador', 'Supermercado Central', 'Tienda Doña Rosa', 'Panadería San José', 'Cliente Mostrador']
        })
        df_datos.to_excel(writer, sheet_name='Datos_Ventas', index=False)
        
        df_instrucciones = pd.DataFrame({
            'Columna': ['Fecha', 'Producto', 'Ventas', 'Cantidad', 'Cliente'],
            'Formato': ['DD/MM/AAAA (ej. 15/08/2026)', 'Texto libre con nombre del SKU', 'Monto numérico en divisa base (sin símbolos)', 'Número entero de piezas/unidades', 'Nombre del comprador o "Mostrador"'],
            'Obligatorio': ['Sí', 'Sí', 'Sí', 'Opcional (se autogenera)', 'Opcional']
        })
        df_instrucciones.to_excel(writer, sheet_name='Instrucciones', index=False)
    return output.getvalue()

st.sidebar.markdown("---")
st.sidebar.header("📁 Ingesta de Datos")
st.sidebar.download_button(
    label="📥 Descargar Plantilla Excel Oficial",
    data=generar_plantilla_excel(),
    file_name="plantilla_ventas_intelretail.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    help="Descarga este archivo de Excel formateado con instrucciones para cargar tus ventas."
)

archivo_usuario = st.sidebar.file_uploader("Sube tu archivo de ventas (.csv o .xlsx):", type=['csv', 'xlsx'])

# ==============================================================================
# MOTOR CORE CON MAPEO TOLERANTE Y CACHÉ
# ==============================================================================
@st.cache_data
def limpiar_y_preparar_datos(file_bytes, filename, porcentaje_costo_proveedor, factor_divisa):
    df_temp = None
    buffer = io.BytesIO(file_bytes) if isinstance(file_bytes, bytes) else file_bytes
    
    if filename.endswith('.xlsx'):
        try:
            df_temp = pd.read_excel(buffer)
        except Exception as e:
            st.error(f"Error al leer archivo Excel: {e}")
            st.stop()
    else:
        for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                buffer.seek(0)
                df_temp = pd.read_csv(buffer, encoding=enc)
                break
            except:
                continue
                
    if df_temp is None:
        st.error("No fue posible leer el archivo suministrado.")
        st.stop()

    # Mapeo inteligente tolerante a sinónimos en español e inglés
    column_map = {}
    for col in df_temp.columns:
        col_clean = str(col).strip().lower()
        if any(x in col_clean for x in ['fecha', 'order date', 'date', 'dia']):
            column_map[col] = 'Order Date'
        elif any(x in col_clean for x in ['venta', 'sales', 'ingreso', 'monto', 'total']):
            column_map[col] = 'Sales'
        elif any(x in col_clean for x in ['producto', 'product', 'item', 'articulo', 'sku', 'nombre']):
            column_map[col] = 'Product Name'
        elif any(x in col_clean for x in ['cantidad', 'quantity', 'unidades', 'cant']):
            column_map[col] = 'Quantity'
        elif any(x in col_clean for x in ['cliente', 'customer', 'comprador']):
            column_map[col] = 'Customer Name'
            
    df_temp = df_temp.rename(columns=column_map)
    
    if 'Sales' not in df_temp.columns:
        st.error("⚠️ No se identificó una columna de ventas. Asegúrate de incluir 'Ventas' o 'Sales'.")
        st.stop()
        
    if 'Product Name' not in df_temp.columns:
        df_temp['Product Name'] = "Articulo General"
    if 'Customer Name' not in df_temp.columns:
        df_temp['Customer Name'] = "Cliente Mostrador"
        
    df_temp = df_temp.dropna(subset=['Sales'])
    df_temp['Sales'] = pd.to_numeric(df_temp['Sales'], errors='coerce')
    df_temp = df_temp[df_temp['Sales'] > 0]
    
    if 'Order Date' in df_temp.columns:
        df_temp['Order Date'] = pd.to_datetime(df_temp['Order Date'], format='%d/%m/%Y', errors='coerce')
    else:
        df_temp['Order Date'] = pd.Timestamp.now()
        
    df_temp['Sales_Original'] = df_temp['Sales']
    df_temp['Sales'] = df_temp['Sales_Original'] * factor_divisa
    
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
    
    df_limpio['Dia_Semana'] = df_limpio['Order Date'].dt.day_name()
    mapeo_dias = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
    df_limpio['Dia_Semana'] = df_limpio['Dia_Semana'].map(mapeo_dias).fillna('Indeterminado')
    dia_dorado = df_limpio.groupby('Dia_Semana')['Sales'].sum().idxmax()
    
    ticket_promedio = df_limpio['Sales'].sum() / len(df_limpio)
    df_clientes = df_limpio.groupby('Customer Name')['Sales'].sum().reset_index().sort_values(by='Sales', ascending=False).head(5)
    
    # Análisis de Pareto 80/20
    df_pareto = df_agrupado.sort_values(by='Sales', ascending=False).copy()
    df_pareto['Sales_Acum'] = df_pareto['Sales'].cumsum()
    df_pareto['Pct_Acum'] = (df_pareto['Sales_Acum'] / df_pareto['Sales'].sum()) * 100
    total_skus = len(df_pareto)
    skus_pareto = len(df_pareto[df_pareto['Pct_Acum'] <= 80])
    skus_pareto = max(1, skus_pareto)
    
    return {
        "mas_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmax()]['Product Name'],
        "cant_mas_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmax()]['Quantity'],
        "estrella": df_agrupado.loc[df_agrupado['Ganancia_Neta'].idxmax()]['Product Name'],
        "ganancia_estrella": df_agrupado.loc[df_agrupado['Ganancia_Neta'].idxmax()]['Ganancia_Neta'],
        "menos_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmin()]['Product Name'],
        "cant_menos_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmin()]['Quantity'],
        "precio_mas_caro": df_limpio['Precio_Unitario'].max(),
        "precio_mas_barato": df_limpio['Precio_Unitario'].min(),
        "dia_dorado": dia_dorado,
        "ticket_promedio": ticket_promedio,
        "top_clientes": df_clientes,
        "df_agrupado": df_agrupado,
        "total_skus": total_skus,
        "skus_pareto": skus_pareto
    }

def optimizar_marketing_avanzado(presupuesto_total):
    limite_minimo = 20 * m_factor
    if presupuesto_total < limite_minimo:
        return presupuesto_total, 0, 0, 0, int((presupuesto_total * 2.0) / (3 * m_factor)), "FACEBOOK_ONLY"
    
    if presupuesto_total < (200 * m_factor):
        p_ig, p_fb, p_tk, p_gg = 0.40, 0.40, 0.20, 0.0
    else:
        p_ig, p_fb, p_tk, p_gg = 0.35, 0.30, 0.20, 0.15
        
    inv_ig = presupuesto_total * p_ig
    inv_fb = presupuesto_total * p_fb
    inv_tk = presupuesto_total * p_tk
    inv_gg = presupuesto_total * p_gg
    
    cac = 4 * m_factor
    cl_ig = (inv_ig * 3.5) / cac
    cl_fb = (inv_fb * 3.0) / cac
    cl_tk = (inv_tk * 2.5) / cac
    cl_gg = (inv_gg * 2.0) / cac
    
    total_clientes = int(cl_ig + cl_fb + cl_tk + cl_gg)
    return inv_ig, inv_fb, inv_tk, inv_gg, total_clientes, "DIVERSIFICADO"

def simular_escenario_negocio(df_original, cambio_precio_porcentaje, presupuesto_marketing, porcentaje_costo_proveedor):
    df_simulado = df_original.copy()
    
    factor_precio = 1 + (cambio_precio_porcentaje / 100)
    factor_cantidad = 1 - (cambio_precio_porcentaje / 100 * 0.5) 
    
    _, _, _, _, clientes_nuevos, _ = optimizar_marketing_avanzado(presupuesto_marketing)
    unidades_extra = clientes_nuevos * 1.5
    
    ventas_totales_historicas = df_simulado['Sales'].sum()
    ganancia_total_historica = df_simulado['Ganancia_Neta'].sum()
    
    ventas_unidades_existentes = (df_simulado['Sales'] * factor_precio * factor_cantidad).sum()
    precio_medio = df_simulado['Sales'].mean() / df_simulado['Quantity'].mean()
    ventas_impulso_marketing = unidades_extra * precio_medio * factor_precio
    ventas_totales_simuladas = ventas_unidades_existentes + ventas_impulso_marketing
    
    factor_costo = porcentaje_costo_proveedor / 100
    costo_unidades_existentes = (df_simulado['Sales'] * factor_costo * factor_cantidad).sum()
    costo_impulso_marketing = (unidades_extra * precio_medio * factor_costo)
    nuevos_costos_proveedor = costo_unidades_existentes + costo_impulso_marketing
    
    ganancia_total_simulada = ventas_totales_simuladas - nuevos_costos_proveedor - presupuesto_marketing
    return ventas_totales_historicas, ganancia_total_historica, ventas_totales_simuladas, ganancia_total_simulada

# ==============================================================================
# CARGA DE DATOS CENTRALIZADA
# ==============================================================================
with st.sidebar.expander("⚙️ Parámetros de Costo de Compra", expanded=True):
    slider_costo_prov = st.slider("Costo de Adquisición / Proveedor (%)", min_value=10, max_value=90, value=70, step=5)

if archivo_usuario is not None:
    df_app = limpiar_y_preparar_datos(archivo_usuario.getvalue(), archivo_usuario.name, slider_costo_prov, m_factor)
    st.sidebar.success("¡Datos empresariales cargados con éxito!")
else:
    try:
        with open('train.csv', 'rb') as f:
            df_app = limpiar_y_preparar_datos(f.read(), 'train.csv', slider_costo_prov, m_factor)
        st.sidebar.info("Modo demostración con datos base.")
    except:
        df_app = pd.DataFrame()

if not df_app.empty:
    analisis = analizar_datos_avanzados(df_app)

# Menú lateral de navegación rápida
st.sidebar.markdown("---")
st.sidebar.header("🧭 Navegación")
opcion_nav = st.sidebar.radio(
    "Ir a:", 
    ["🏠 Inicio (Home)", "⚡ Diagnóstico Express (Sin CSV)", "🔍 Auditoría y BI de Catálogo", "🎛️ Simulador y Proyecciones", "🎯 Planificador por Objetivos"],
    index=0 if st.session_state.pantalla_actual == "home" else 
          1 if st.session_state.pantalla_actual == "express" else
          2 if st.session_state.pantalla_actual == "diagnostico" else
          3 if st.session_state.pantalla_actual == "simulador" else 4
)

if opcion_nav == "🏠 Inicio (Home)":
    st.session_state.pantalla_actual = "home"
elif opcion_nav == "⚡ Diagnóstico Express (Sin CSV)":
    st.session_state.pantalla_actual = "express"
elif opcion_nav == "🔍 Auditoría y BI de Catálogo":
    st.session_state.pantalla_actual = "diagnostico"
elif opcion_nav == "🎛️ Simulador y Proyecciones":
    st.session_state.pantalla_actual = "simulador"
elif opcion_nav == "🎯 Planificador por Objetivos":
    st.session_state.pantalla_actual = "objetivos"

# ==============================================================================
# PANTALLA 1: HOME PAGE (ESTILO APP MÓVIL)
# ==============================================================================
if st.session_state.pantalla_actual == "home":
    st.title("🚀 Bienvenido a IntelRetail Pro")
    st.markdown("#### *El copiloto estratégico de inteligencia de negocios y finanzas para microempresarios y retail.*")
    st.markdown("Selecciona el módulo con el que deseas trabajar hoy:")
    st.write("")

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("""
        <div class="home-card">
            <h3>⚡ Diagnóstico Express</h3>
            <p>Ideal si no tienes un archivo de ventas. Ingresa tus números estimados y obtén tu punto de equilibrio y salud de márgenes al instante.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Abrir Diagnóstico Express ➡️", use_container_width=True, type="primary"):
            cambiar_pantalla("express")
            st.rerun()

        st.write("")
        st.markdown("""
        <div class="home-card">
            <h3>🎛️ Simulador de Escenarios</h3>
            <p>Proyecta cómo afectará tus utilidades subir o bajar precios y simula la inversión publicitaria en redes sociales.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Abrir Simulador Financiero ➡️", use_container_width=True):
            cambiar_pantalla("simulador")
            st.rerun()

    with col_h2:
        st.markdown("""
        <div class="home-card">
            <h3>🔍 Auditoría y BI de Catálogo</h3>
            <p>Carga tu historial de ventas para descubrir tus productos estrella, dormidos, regla de Pareto 80/20 y matriz BCG.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Abrir Auditoría de Catálogo ➡️", use_container_width=True):
            cambiar_pantalla("diagnostico")
            st.rerun()

        st.write("")
        st.markdown("""
        <div class="home-card">
            <h3>🎯 Planificador de Metas (Simulador Inverso)</h3>
            <p>Define cuánto dinero neto quieres ganar este mes y calcula exactamente cuántas ventas diarias necesitas alcanzar.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Abrir Planificador de Metas ➡️", use_container_width=True):
            cambiar_pantalla("objetivos")
            st.rerun()

# ==============================================================================
# PANTALLA 2: DIAGNÓSTICO EXPRESS (PARA MICRO-NEGOCIOS)
# ==============================================================================
elif st.session_state.pantalla_actual == "express":
    if st.button("⬅️ Volver al Inicio"):
        cambiar_pantalla("home")
        st.rerun()
        
    st.header("⚡ Diagnóstico Rápido para Micro-Comercios")
    st.markdown("Diseñado para comerciantes sin data histórica masiva. Completa los 4 datos básicos:")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        venta_mensual_est = st.number_input(f"Venta estimada promedio al mes ({m_sufijo}):", min_value=100.0, value=5000000.0 if selector_moneda == "COP (Pesos Colombianos)" else 2000.0, step=50000.0 if selector_moneda == "COP (Pesos Colombianos)" else 100.0)
        margen_bruto_pct = st.slider("Margen bruto sobre productos (% de ganancia sobre costo):", min_value=5, max_value=80, value=30, step=1)
    
    with col_e2:
        gastos_fijos_est = st.number_input(f"Gastos fijos mensuales (Arriendo, nómina, servicios en {m_sufijo}):", min_value=0.0, value=1200000.0 if selector_moneda == "COP (Pesos Colombianos)" else 500.0, step=50000.0 if selector_moneda == "COP (Pesos Colombianos)" else 50.0)
        clientes_mes_est = st.number_input("Número estimado de clientes/compras al mes:", min_value=1, value=350, step=10)

    utilidad_bruta_est = venta_mensual_est * (margen_bruto_pct / 100)
    utilidad_neta_est = utilidad_bruta_est - gastos_fijos_est
    ticket_prom_express = venta_mensual_est / clientes_mes_est
    
    punto_equilibrio_ventas = gastos_fijos_est / (margen_bruto_pct / 100) if margen_bruto_pct > 0 else 0
    clientes_punto_equilibrio = int(punto_equilibrio_ventas / ticket_prom_express) if ticket_prom_express > 0 else 0
    
    st.markdown("---")
    st.subheader("📌 Diagnóstico Financiero Instantáneo")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.markdown(f"""
        <div class="metric-container {'metric-success' if utilidad_neta_est > 0 else 'metric-danger'}">
            <div class="metric-title">💼 UTILIDAD NETA MENSUAL ESTIMADA</div>
            <div class="metric-value">{m_simbolo}{utilidad_neta_est:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Ganancia real descontando gastos operativos y costo de compra.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_r2:
        st.markdown(f"""
        <div class="metric-container metric-warning">
            <div class="metric-title">⚖️ PUNTO DE EQUILIBRIO MENSUAL</div>
            <div class="metric-value">{m_simbolo}{punto_equilibrio_ventas:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Venta mínima para cubrir gastos sin entrar a pérdidas.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_r3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">🛒 TICKET PROMEDIO REQUERIDO</div>
            <div class="metric-value">{m_simbolo}{ticket_prom_express:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Necesitas atender al menos <b>{clientes_punto_equilibrio} clientes/mes</b>.</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("💡 Recomendaciones Prácticas para Mejorar tu Margen Hoy", expanded=True):
        st.markdown("""
        * **Estrategia de Anclaje:** Sitúa los artículos de compra por impulso cerca de la zona de cobro.
        * **Ofertas Empaquetadas (Bundles):** Combina el producto más vendido con uno de baja rotación pero alto margen.
        * **Revisión de Fugas de Caja:** Revisa periódicamente si las mermas o gastos hormiga superan el 3% de las ventas.
        """)

# ==============================================================================
# PANTALLA 3: AUDITORÍA Y BI DE CATÁLOGO (PARETO + BCG + CLIENTES TOP)
# ==============================================================================
elif st.session_state.pantalla_actual == "diagnostico":
    if st.button("⬅️ Volver al Inicio"):
        cambiar_pantalla("home")
        st.rerun()
        
    st.header("📊 Diagnóstico Avanzado de Catálogo y BI")
    
    if df_app.empty:
        st.warning("Carga un archivo de ventas en la barra lateral para ver este reporte.")
        st.stop()
        
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">🏆 PRODUCTO ESTRELLA (MÁXIMA UTILIDAD)</div>
            <div class="metric-value">{m_simbolo}{analisis['ganancia_estrella']:,.2f}{m_sufijo}</div>
            <div class="metric-caption"><b>SKU / Nombre:</b> {analisis['estrella']}</div>
        </div>
        <div class="metric-container">
            <div class="metric-title">🥇 LÍDER EN ROTACIÓN (MÁS VENDIDO)</div>
            <div class="metric-value">{analisis['cant_mas_vendido']:,} {'Unidad' if analisis['cant_mas_vendido'] == 1 else 'Unidades'}</div>
            <div class="metric-caption"><b>SKU / Nombre:</b> {analisis['mas_vendido']}</div>
        </div>
        <div class="metric-container">
            <div class="metric-title">🛒 TICKET PROMEDIO POR ORDEN</div>
            <div class="metric-value">{m_simbolo}{analisis['ticket_promedio']:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Facturación promedio por transacción en base de datos.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown(f"""
        <div class="metric-container metric-danger">
            <div class="metric-title">💤 PRODUCTO DORMIDO (BAJA ROTACIÓN)</div>
            <div class="metric-value">{analisis['cant_menos_vendido']} {'Unidad' if analisis['cant_menos_vendido'] == 1 else 'Unidades'}</div>
            <div class="metric-caption"><b>SKU / Nombre:</b> {analisis['menos_vendido']} (Riesgo de inventario estancado).</div>
        </div>
        <div class="metric-container">
            <div class="metric-title">🗓️ DÍA DORADO DE FACTURACIÓN</div>
            <div class="metric-value">Cada {analisis['dia_dorado']}</div>
            <div class="metric-caption">Día con mayor concentración de ingresos semanales.</div>
        </div>
        <div class="metric-container">
            <div class="metric-title">📐 ANÁLISIS DE PARETO (80/20)</div>
            <div class="metric-value">{analisis['skus_pareto']} de {analisis['total_skus']} Productos</div>
            <div class="metric-caption">Solo el {(analisis['skus_pareto']/analisis['total_skus'])*100:.1f}% de tus SKUs genera el 80% de tus ventas.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🎯 Matriz de Inventario BCG (Rotación vs. Margen)")
    fig_bcg = px.scatter(
        analisis['df_agrupado'], x='Quantity', y='Ganancia_Neta',
        size='Sales', color='Product Name', hover_name='Product Name',
        labels={'Quantity': 'Unidades Vendidas (Rotación)', 'Ganancia_Neta': f'Ganancia Acumulada ({m_sufijo})'},
        title="Posición Estratégica de Productos en Catálogo"
    )
    fig_bcg.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_bcg, use_container_width=True)

    st.markdown("---")
    st.subheader("👥 Concentración de Ventas: Top 5 Clientes de Mayor Valor")
    fig_cl = px.bar(
        analisis['top_clientes'], x='Sales', y='Customer Name', orientation='h',
        labels={'Sales': f'Total Facturado ({m_sufijo})', 'Customer Name': 'Cliente'},
        color='Sales', color_continuous_scale='Blues'
    )
    fig_cl.update_layout(height=300, showlegend=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_cl, use_container_width=True)

# ==============================================================================
# PANTALLA 4: SIMULADOR DE ESCENARIOS Y ASIGNACIÓN DE MARKETING
# ==============================================================================
elif st.session_state.pantalla_actual == "simulador":
    if st.button("⬅️ Volver al Inicio"):
        cambiar_pantalla("home")
        st.rerun()
        
    st.header("🎛️ Modelado Financiero Predictivo y Pauta Digital")
    
    if df_app.empty:
        st.warning("Carga un archivo de ventas en la barra lateral para simular escenarios.")
        st.stop()
        
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        slider_precio = st.slider("Ajuste Estratégico de Precios (%)", min_value=-20, max_value=20, value=0, step=1)
    with col_s2:
        max_p_mkt = 5000000 if selector_moneda == "COP (Pesos Colombianos)" else 2000
        step_p_mkt = 100000 if selector_moneda == "COP (Pesos Colombianos)" else 50
        slider_mkt = st.slider("Presupuesto Publicitario Mensual", min_value=0, max_value=max_p_mkt, value=0, step=step_p_mkt)

    v_h, g_h, v_s, g_s = simular_escenario_negocio(df_app, slider_precio, slider_mkt, slider_costo_prov)
    ig_i, fb_i, tk_i, gg_i, cl_n, modo_mkt = optimizar_marketing_avanzado(slider_mkt)
    
    if g_s > g_h:
        st.success(f"🟢 **Escenario Favorable:** Las proyecciones estiman un incremento en ganancias del **{((g_s - g_h)/g_h)*100:.2f}%**.")
    elif g_s < 0:
        st.error("🔴 **Alerta de Pérdidas:** La estrategia destruye el margen comercial; operarás por debajo del punto de equilibrio.")
    else:
        st.warning(f"🟡 **Riesgo Moderado:** Las utilidades proyectadas disminuyen un **{abs(((g_s - g_h)/g_h)*100):.2f}%**.")
        
    fig_fin = go.Figure(data=[
        go.Bar(name='Histórico (Pasado)', x=['Ventas Totales', 'Ganancia Neta'], y=[v_h, g_h], marker_color='#636EFA'),
        go.Bar(name='Simulado (Futuro Proyectado)', x=['Ventas Totales', 'Ganancia Neta'], y=[v_s, g_s], marker_color='#00CC96')
    ])
    fig_fin.update_layout(barmode='group', height=400, yaxis_title=f"Monto ({m_sufijo})")
    fig_fin.update_traces(texttemplate=m_simbolo + '%{y:,.2f}' + m_sufijo, textposition='outside')
    st.plotly_chart(fig_fin, use_container_width=True)
    
    if slider_mkt > 0:
        st.markdown("---")
        st.subheader("📢 Distribución de Presupuesto en Canales Digitales")
        if modo_mkt == "FACEBOOK_ONLY":
            st.info(f"🎯 Captación estimada de **{cl_n} clientes nuevos** concentrando el 100% en Facebook Ads local.")
        else:
            datos_mkt = {'Red Social': ['Instagram', 'Facebook', 'TikTok', 'Google Ads'], 'Inversión': [ig_i, fb_i, tk_i, gg_i]}
            fig_mkt = px.bar(
                datos_mkt, x='Red Social', y='Inversión', text='Inversión', color='Red Social',
                color_discrete_map={'Instagram': '#E1306C', 'Facebook': '#1877F2', 'TikTok': '#25F4EE', 'Google Ads': '#4285F4'}
            )
            fig_mkt.update_traces(texttemplate=m_simbolo + '%{text:,.2f}' + m_sufijo, textposition='outside')
            fig_mkt.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_mkt, use_container_width=True)

# ==============================================================================
# PANTALLA 5: PLANIFICADOR DE METAS (SIMULADOR INVERSO)
# ==============================================================================
elif st.session_state.pantalla_actual == "objetivos":
    if st.button("⬅️ Volver al Inicio"):
        cambiar_pantalla("home")
        st.rerun()
        
    st.header("🎯 Planificador por Objetivos (Simulador Inverso)")
    st.markdown("Define tu meta financiera mensual y descubre qué esfuerzo operativo requiere tu comercio:")
    
    meta_ganancia = st.number_input(f"¿Cuánto dinero neto deseas ganar este mes? ({m_sufijo}):", min_value=1000.0, value=3000000.0 if selector_moneda == "COP (Pesos Colombianos)" else 1500.0, step=100000.0 if selector_moneda == "COP (Pesos Colombianos)" else 50.0)
    gastos_fijos_plan = st.number_input(f"Gastos fijos a cubrir en el período ({m_sufijo}):", min_value=0.0, value=1500000.0 if selector_moneda == "COP (Pesos Colombianos)" else 600.0, step=50000.0 if selector_moneda == "COP (Pesos Colombianos)" else 50.0)
    
    margen_comercial = (100 - slider_costo_prov) / 100
    ventas_necesarias = (meta_ganancia + gastos_fijos_plan) / margen_comercial if margen_comercial > 0 else 0
    ventas_diarias_req = ventas_necesarias / 30
    
    t_prom = analisis['ticket_promedio'] if not df_app.empty else (ventas_necesarias / 300)
    transacciones_diarias_req = int(np.ceil(ventas_diarias_req / t_prom)) if t_prom > 0 else 0
    
    st.markdown("---")
    st.subheader("📋 Hoja de Ruta para Alcanzar tu Meta")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown(f"""
        <div class="metric-container metric-success">
            <div class="metric-title">🎯 FACTURACIÓN TOTAL REQUERIDA</div>
            <div class="metric-value">{m_simbolo}{ventas_necesarias:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Ventas brutas mensuales necesarias.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">📅 META DE VENTA DIARIA</div>
            <div class="metric-value">{m_simbolo}{ventas_diarias_req:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Objetivo diario promedio (30 días).</div>
        </div>
        """, unsafe_allow_html=True)
    with col_p3:
        st.markdown(f"""
        <div class="metric-container metric-warning">
            <div class="metric-title">👥 CLIENTES / TICKETS DIARIOS</div>
            <div class="metric-value">{transacciones_diarias_req} Compras/Día</div>
            <div class="metric-caption">Basado en tu ticket promedio actual.</div>
        </div>
        """, unsafe_allow_html=True)
