import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página web
st.set_page_config(page_title="Simulador Inteligente Retail", layout="wide", page_icon="📊")

# Título Principal
st.title("📊 Sistema Inteligente de Decisiones y Diagnóstico para Supermercados")
st.markdown("---")

# ==============================================================================
# FUNCIONES ANALÍTICAS (EL CEREBRO DEL PROYECTO)
# ==============================================================================

def limpiar_y_preparar_datos(file, porcentaje_costo_proveedor):
    """Limpia el archivo cargado y genera las columnas financieras usando el porcentaje del usuario."""
    df_temp = pd.read_csv(file)
    df_temp = df_temp.dropna(subset=['Order Date', 'Sales'])
    df_temp['Order Date'] = pd.to_datetime(df_temp['Order Date'], format='%d/%m/%Y', errors='coerce')
    df_temp = df_temp[df_temp['Sales'] > 0]
    
    # Simulación de cantidad (Semilla fija para consistencia)
    np.random.seed(42)
    df_temp['Quantity'] = np.random.randint(1, 6, size=len(df_temp))
    
    # Reglas de negocio financieras dinámicas [finance]
    factor_costo = porcentaje_costo_proveedor / 100
    df_temp['Costo_Proveedor'] = df_temp['Sales'] * factor_costo
    df_temp['Ganancia_Neta'] = df_temp['Sales'] - df_temp['Costo_Proveedor']
    return df_temp

def analizar_productos_estrella(df_limpio):
    """Encuentra métricas críticas del catálogo de productos."""
    df_agrupado = df_limpio.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
    df_limpio['Precio_Unitario'] = df_limpio['Sales'] / df_limpio['Quantity']
    
    return {
        "mas_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmax()]['Product Name'],
        "cant_mas_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmax()]['Quantity'],
        "estrella": df_agrupado.loc[df_agrupado['Ganancia_Neta'].idxmax()]['Product Name'],
        "ganancia_estrella": df_agrupado.loc[df_agrupado['Ganancia_Neta'].idxmax()]['Ganancia_Neta'],
        "menos_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmin()]['Product Name'],
        "cant_menos_vendido": df_agrupado.loc[df_agrupado['Quantity'].idxmin()]['Quantity'],
        "mas_caro": df_limpio.loc[df_limpio['Precio_Unitario'].idxmax()]['Product Name'],
        "precio_mas_caro": df_limpio.loc[df_limpio['Precio_Unitario'].idxmax()]['Precio_Unitario'],
        "mas_barato": df_limpio.loc[df_limpio['Precio_Unitario'].idxmin()]['Product Name'],
        "precio_mas_barato": df_limpio.loc[df_limpio['Precio_Unitario'].idxmin()]['Precio_Unitario']
    }

def optimizar_marketing(presupuesto_total):
    """Distribuye eficientemente los recursos publicitarios en redes sociales [finance]."""
    if presupuesto_total <= 0:
        return 0, 0, 0, 0, 0
    inversion_instagram = presupuesto_total * 0.40
    inversion_facebook = presupuesto_total * 0.30
    inversion_tiktok = presupuesto_total * 0.20
    inversion_google = presupuesto_total * 0.10
    
    clientes_ig = (inversion_instagram * 3.5) / 4
    clientes_fb = (inversion_facebook * 3.0) / 4
    clientes_tk = (inversion_tiktok * 2.5) / 4
    clientes_gg = (inversion_google * 2.0) / 4
    
    return inversion_instagram, inversion_facebook, inversion_tiktok, inversion_google, int(clientes_ig + clientes_fb + clientes_tk + clientes_gg)

def simular_escenario_negocio(df_original, cambio_precio_porcentaje, presupuesto_marketing, porcentaje_costo_proveedor):
    """Calcula el impacto global de variaciones de precio y marketing [finance]."""
    df_simulado = df_original.copy()
    factor_precio = 1 + (cambio_precio_porcentaje / 100)
    df_simulado['Nuevas_Ventas'] = df_simulado['Sales'] * factor_precio
    
    factor_cantidad = 1 - (cambio_precio_porcentaje / 100 * 0.5) # Elasticidad
    df_simulado['Nueva_Cantidad'] = df_simulado['Quantity'] * factor_cantidad
    
    _, _, _, _, clientes_nuevos = optimizar_marketing(presupuesto_marketing)
    unidades_extra_marketing = clientes_nuevos * 1.5
    
    ventas_totales_historicas = df_simulado['Sales'].sum()
    ganancia_total_historica = df_simulado['Ganancia_Neta'].sum()
    
    precio_promedio_unidad = df_simulado['Sales'].mean() / df_simulado['Quantity'].mean()
    ventas_totales_simuladas = (df_simulado['Nuevas_Ventas'] * factor_cantidad).sum() + (unidades_extra_marketing * precio_promedio_unidad)
    
    # El costo del proveedor se calcula con la nueva cantidad de piezas usando el porcentaje dinámico [finance]
    factor_costo = porcentaje_costo_proveedor / 100
    nuevos_costos_proveedor = ((df_simulado['Sales'] * factor_costo) * factor_cantidad).sum()
    ganancia_total_simulada = ventas_totales_simuladas - nuevos_costos_proveedor - presupuesto_marketing
    
    return ventas_totales_historicas, ganancia_total_historica, ventas_totales_simuladas, ganancia_total_simulada

# ==============================================================================
# ESTRUCTURA VISUAL (INTERFAZ DE USUARIO)
# ==============================================================================

# Panel Lateral de Configuración de Datos
st.sidebar.header("📁 Carga de Información Financiera")
archivo_usuario = st.sidebar.file_uploader("Sube el archivo CSV de ventas de tu negocio:", type=['csv'])

# NUEVA FUNCIÓN: Control para definir el costo del proveedor de forma interactiva
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Parámetros Financieros")
slider_costo_prov = st.sidebar.slider("Costo Promedio del Proveedor (% de la venta)", min_value=10, max_value=90, value=70, step=5)
st.sidebar.caption("Define qué porcentaje del precio de venta corresponde al pago de proveedores [finance]. Por defecto es 70%.")

# Carga condicionada de la base de datos aplicando el porcentaje dinámico
if archivo_usuario is not None:
    df_app = limpiar_y_preparar_datos(archivo_usuario, slider_costo_prov)
    st.sidebar.success("¡Datos reales cargados correctamente!")
else:
    try:
        df_app = limpiar_y_preparar_datos('train.csv', slider_costo_prov)
        st.sidebar.info("Mostrando datos de demostración (9,800 registros de prueba).")
    except:
        st.error("Por favor, asegúrate de que el archivo 'train.csv' esté en la misma carpeta.")
        st.stop()

# Menú de pestañas
pestana_diagnostico, pestana_simulador = st.tabs(["🔍 Diagnóstico de Productos Estrella", "🎛️ Simulador de Ventas e Inversión"])

# ---- PESTAÑA 1: DIAGNÓSTICO ----
with pestana_diagnostico:
    st.header("⭐ Diagnóstico Automático de Productos")
    st.markdown("Este panel analiza el catálogo del archivo para identificar tus artículos clave [finance].")
    
    res = analizar_productos_estrella(df_app)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🏆 PRODUCTO ESTRELLA (Mayor Utilidad)", value=f"${res['ganancia_estrella']:,.2f} USD")
        st.caption(f"**Nombre:** {res['estrella']}")
        
        st.metric(label="🥇 PRODUCTO MÁS VENDIDO (Mayor Volumen)", value=f"{res['cant_mas_vendido']} Unidades")
        st.caption(f"**Nombre:** {res['mas_vendido']}")
    
    with col2:
        st.metric(label="💤 PRODUCTO DORMIDO (Alerta de Inventario)", value=f"{res['cant_menos_vendido']} Unidades")
        st.caption(f"**Nombre:** {res['menos_vendido']}")
        
        st.metric(label="💰 PRODUCTO PREMIUM vs 🏷️ ECONÓMICO", value=f"${res['precio_mas_caro']:,.2f}")
        st.caption(f"**Más Caro:** {res['mas_caro']} | **Más Barato:** ${res['precio_mas_barato']:,.2f} (**Nombre:** {res['mas_barato']})")

# ---- PESTAÑA 2: SIMULADOR ----
with pestana_simulador:
    st.header("🎛️ Panel de Proyecciones Estratégicas")
    
    st.sidebar.header("🎯 Controles de Simulación")
    slider_precio = st.sidebar.slider("Ajuste de Precios del Supermercado (%)", min_value=-20, max_value=20, value=0, step=1)
    slider_mkt = st.sidebar.slider("Presupuesto de Publicidad Mensual ($)", min_value=0, max_value=2000, value=0, step=50)
    
    # Enviamos el costo del proveedor dinámico al simulador de negocio
    v_h, g_h, v_s, g_s = simular_escenario_negocio(df_app, slider_precio, slider_mkt, slider_costo_prov)
    ig_i, fb_i, tk_i, gg_i, cl_n = optimizar_marketing(slider_mkt)
    
    st.subheader("📊 Proyección Financiera Total")
    fig_fin = go.Figure(data=[
        go.Bar(name='Histórico (Pasado)', x=['Ventas Totales', 'Ganancia Neta'], y=[v_h, g_h], marker_color='#636EFA'),
        go.Bar(name='Simulado (Futuro)', x=['Ventas Totales Proyectadas', 'Ganancia Proyectada'], y=[v_s, g_s], marker_color='#00CC96')
    ])
    fig_fin.update_layout(barmode='group', height=400)
    fig_fin.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')
    st.plotly_chart(fig_fin, use_container_width=True)
    
    if slider_mkt > 0:
        st.markdown("---")
        st.subheader("📢 Recomendación del Asesor Digital de Marketing")
        st.info(f"🎯 Con una inversión óptma de **${slider_mkt:.2f}**, estimamos la captación de **{cl_n} clientes nuevos** mensuales.")
        
        datos_mkt = {
            'Canal de Red Social': ['Instagram', 'Facebook', 'TikTok', 'Google Ads'],
            'Asignación Sugerida ($)': [ig_i, fb_i, tk_i, gg_i]
        }
        fig_mkt = px.bar(
            datos_mkt, x='Canal de Red Social', y='Asignación Sugerida ($)', text='Asignación Sugerida ($)',
            color='Canal de Red Social',
            color_discrete_map={'Instagram': '#E1306C', 'Facebook': '#1877F2', 'TikTok': '#000000', 'Google Ads': '#4285F4'}
        )
        fig_mkt.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
        fig_mkt.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_mkt, use_container_width=True)
