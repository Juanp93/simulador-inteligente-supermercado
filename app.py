import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuración de alta fidelidad para la página web
st.set_page_config(page_title="IntelRetail Pro - Sistema de Decisiones", layout="wide", page_icon="📈")

# Estilos CSS personalizados para tarjetas dinámicas basadas en rendimiento financiero
st.markdown("""
<style>
    .metric-container { background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid #636EFA; margin-bottom: 15px; }
    .metric-success { border-left: 5px solid #00CC96; }
    .metric-danger { border-left: 5px solid #EF553B; }
    .metric-title { font-size: 14px; color: #A3A3A3; font-weight: bold; }
    .metric-value { font-size: 24px; color: #FFFFFF; font-weight: bold; }
    .metric-caption { font-size: 12px; color: #858585; }
</style>
""", unsafe_value=True)

st.title("📈 IntelRetail Pro: Sistema de Inteligencia de Negocios y Simulación")
st.markdown("Plataforma avanzada de diagnóstico operativo, optimización presupuestal y modelado de escenarios financieros.")
st.markdown("---")

# ==============================================================================
# GESTIÓN DE CONFIGURACIÓN Y MONEDA (LOCALIZACIÓN)
# ==============================================================================

st.sidebar.header("📁 Carga de Información Financiera")
archivo_usuario = st.sidebar.file_uploader("Sube el archivo CSV de ventas de tu negocio:", type=['csv'])

st.sidebar.markdown("---")
st.sidebar.header("💱 Configuración de Divisa")
selector_moneda = st.sidebar.selectbox("Selecciona la moneda de visualización:", ["COP (Pesos Colombianos)", "USD (Dólares)", "MXN (Pesos Mexicanos)"])

# Definición de factores de conversión y símbolos
config_moneda = {
    "COP (Pesos Colombianos)": {"factor": 4000.0, "simbolo": "$", "sufijo": " COP"},
    "USD (Dólares)": {"factor": 1.0, "simbolo": "$", "sufijo": " USD"},
    "MXN (Pesos Mexicanos)": {"factor": 18.5, "simbolo": "$", "sufijo": " MXN"}
}
m_factor = config_moneda[selector_moneda]["factor"]
m_simbolo = config_moneda[selector_moneda]["simbolo"]
m_sufijo = config_moneda[selector_moneda]["sufijo"]

# ==============================================================================
# FUNCIONES CORE (PROCESAMIENTO Y MATEMÁTICAS PROSPECTIVAS)
# ==============================================================================

def limpiar_y_preparar_datos(file, porcentaje_costo_proveedor):
    df_temp = pd.read_csv(file)
    df_temp = df_temp.dropna(subset=['Order Date', 'Sales'])
    df_temp['Order Date'] = pd.to_datetime(df_temp['Order Date'], format='%d/%m/%Y', errors='coerce')
    df_temp = df_temp[df_temp['Sales'] > 0]
    
    # Ajuste de moneda base y simulación de cantidades físicas
    df_temp['Sales_Original'] = df_temp['Sales']
    df_temp['Sales'] = df_temp['Sales_Original'] * m_factor
    
    np.random.seed(42)
    df_temp['Quantity'] = np.random.randint(1, 6, size=len(df_temp))
    
    # Estructura de costos fijos y variables del comercio
    factor_costo = porcentaje_costo_proveedor / 100
    df_temp['Costo_Proveedor'] = df_temp['Sales'] * factor_costo
    df_temp['Ganancia_Neta'] = df_temp['Sales'] - df_temp['Costo_Proveedor']
    return df_temp

def analizar_datos_avanzados(df_limpio):
    # Productos Estrella
    df_agrupado = df_limpio.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
    df_limpio['Precio_Unitario'] = df_limpio['Sales'] / df_limpio['Quantity']
    
    # Estacionalidad (Día de la semana)
    df_limpio['Dia_Semana'] = df_limpio['Order Date'].dt.day_name()
    mapeo_dias = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
    df_limpio['Dia_Semana'] = df_limpio['Dia_Semana'].map(mapeo_dias)
    dia_dorado = df_limpio.groupby('Dia_Semana')['Sales'].sum().idxmax()
    
    # Análisis de Ticket Promedio
    ticket_promedio = df_limpio['Sales'].sum() / df_limpio['Quantity'].sum()
    
    # Clientes Top
    df_clientes = df_limpio.groupby('Customer Name')['Sales'].sum().reset_index().sort_values(by='Sales', ascending=False).head(5)
    
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
        "top_clientes": df_clientes
    }

def optimizar_marketing_avanzado(presupuesto_total):
    # Umbral de activación realista adaptado a la divisa seleccionada
    limite_minimo = 20 * m_factor
    if presupuesto_total < limite_minimo:
        return presupuesto_total, 0, 0, 0, int((presupuesto_total * 2.0) / (3 * m_factor)), "FACEBOOK_ONLY"
    
    # Lógica de distribución dinámica basada en rendimientos decrecientes y diversificación
    if presupuesto_total < (200 * m_factor):
        p_ig, p_fb, p_tk, p_gg = 0.40, 0.40, 0.20, 0.0
    else:
        p_ig, p_fb, p_tk, p_gg = 0.35, 0.30, 0.20, 0.15
        
    inv_ig = presupuesto_total * p_ig
    inv_fb = presupuesto_total * p_fb
    inv_tk = presupuesto_total * p_tk
    inv_gg = presupuesto_total * p_gg
    
    # Costos de adquisición indexados al valor de la divisa
    cac = 4 * m_factor
    cl_ig = (inv_ig * 3.5) / cac
    cl_fb = (inv_fb * 3.0) / cac
    cl_tk = (inv_tk * 2.5) / cac
    cl_gg = (inv_gg * 2.0) / cac
    
    total_clientes = int(cl_ig + cl_fb + cl_tk + cl_gg)
    return inv_ig, inv_fb, inv_tk, inv_gg, total_clientes, "DIVERSIFICADO"

def simular_escenario_negocio(df_original, cambio_precio_porcentaje, presupuesto_marketing, porcentaje_costo_proveedor):
    df_simulado = df_original.copy()
    
    # Ajuste de precios y análisis elástico de demanda
    factor_precio = 1 + (cambio_precio_porcentaje / 100)
    factor_cantidad = 1 - (cambio_precio_porcentaje / 100 * 0.5) 
    
    # Impulso operativo por conversiones publicitarias
    _, _, _, _, clientes_nuevos, _ = optimizar_marketing_avanzado(presupuesto_marketing)
    unidades_extra = clientes_nuevos * 1.5
    
    ventas_totales_historicas = df_simulado['Sales'].sum()
    ganancia_total_historica = df_simulado['Ganancia_Neta'].sum()
    
    # Cálculo preciso de ingresos y costos marginales sin desajustes
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
# COMPILACIÓN DE LA INTERFAZ DE USUARIO (UX/UI EN STREAMLIT)
# ==============================================================================

# Agrupación organizada en controles colapsables (Sidebar)
with st.sidebar.expander("⚙️ Configuración Operativa", expanded=True):
    slider_costo_prov = st.slider("Costo del Proveedor (%)", min_value=10, max_value=90, value=70, step=5)

# Inicialización condicionada del conjunto de datos
if archivo_usuario is not None:
    df_app = limpiar_y_preparar_datos(archivo_usuario, slider_costo_prov)
    st.sidebar.success("¡Datos empresariales procesados con éxito!")
else:
    try:
        df_app = limpiar_y_preparar_datos('train.csv', slider_costo_prov)
        st.sidebar.info("Utilizando registros maestros de demostración.")
    except:
        st.error("Error crítico: Falta el archivo base 'train.csv'.")
        st.stop()

# Extracción de analítica avanzada
analisis = analizar_datos_avanzados(df_app)

# Menú de pestañas optimizado
pestana_diagnostico, pestana_simulador = st.tabs(["🔍 Diagnóstico Avanzado de Catálogo", "🎛️ Simulador de Escenarios Estratégicos"])

# ---- PESTAÑA 1: DIAGNÓSTICO PROFUNDO ----
with pestana_diagnostico:
    st.header("📊 Diagnóstico de Salud Comercial")
    
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
            <div class="metric-value">{analisis['cant_mas_vendido']:,} Unidades</div>
            <div class="metric-caption"><b>SKU / Nombre:</b> {analisis['mas_vendido']}</div>
        </div>
        <div class="metric-container">
            <div class="metric-title">🛒 TICKET PROMEDIO POR CLIENTE</div>
            <div class="metric-value">{m_simbolo}{analisis['ticket_promedio']:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Monto medio facturado por artículo adquirido [finance].</div>
        </div>
        """, unsafe_value=True)
        
    with col_b:
        st.markdown(f"""
        <div class="metric-container metric-danger">
            <div class="metric-title">💤 ALERTA: PRODUCTO DORMIDO (CERO MOVIMIENTO)</div>
            <div class="metric-value">{analisis['cant_menos_vendido']} Unidades</div>
            <div class="metric-caption"><b>SKU / Nombre:</b> {analisis['menos_vendido']}<br><span style='color:#FF6B6B;'>Riesgo de dinero congelado en almacén [finance].</span></div>
        </div>
        <div class="metric-container">
            <div class="metric-title">🗓️ DÍA DORADO DE FACTURACIÓN</div>
            <div class="metric-value">Cada {analisis['dia_dorado']}</div>
            <div class="metric-caption">Día de la semana con mayor concentración de flujo de caja [finance].</div>
        </div>
        <div class="metric-container">
            <div class="metric-title">💰 RANGO DE PRECIOS EN CATÁLOGO</div>
            <div class="metric-value">Máx: {m_simbolo}{analisis['precio_mas_caro']:,.2f}</div>
            <div class="metric-caption">Mínimo registrado: {m_simbolo}{analisis['precio_mas_barato']:,.2f}{m_sufijo}</div>
        </div>
        """, unsafe_value=True)
        
    st.markdown("---")
    st.subheader("👥 Concentración de Ventas: Top 5 Clientes de Mayor Valor")
    fig_cl = px.bar(analisis['top_clientes'], x='Sales', y='Customer Name', orientation='h',
                    labels={'Sales': f'Total Facturado ({m_sufijo})', 'Customer Name': 'Cliente'},
                    color='Sales', color_continuous_scale='Viridis')
    fig_cl.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig_cl, use_container_width=True)

# ---- PESTAÑA 2: SIMULADOR DE ESCENARIOS ----
with pestana_simulador:
    st.header("🎛️ Modelado Financiero Predictivo")
    
    with st.sidebar.expander("🎯 Palanca de Decisiones", expanded=True):
        slider_precio = st.slider("Ajuste de Precios (%)", min_value=-20, max_value=20, value=0, step=1)
        # Adaptación dinámica de límites de presupuesto según divisa [finance]
        max_p_mkt = 5000000 if selector_moneda == "COP (Pesos Colombianos)" else 2000
        step_p_mkt = 100000 if selector_moneda == "COP (Pesos Colombianos)" else 50
        slider_mkt = st.slider("Presupuesto Publicitario", min_value=0, max_value=max_p_mkt, value=0, step=step_p_mkt)

    # Procesamiento del motor predictivo equilibrado
    v_h, g_h, v_s, g_s = simular_escenario_negocio(df_app, slider_precio, slider_mkt, slider_costo_prov)
    ig_i, fb_i, tk_i, gg_i, cl_n, modo_mkt = optimizar_marketing_avanzado(slider_mkt)
    
    # Semáforo dinámico corporativo de alertas [finance]
    if g_s > g_h:
        st.success(f"🟢 **Escenario Favorable:** Las proyecciones estiman un incremento en las ganancias netas del **{((g_s - g_h)/g_h)*100:.2f}%** [finance].")
    elif g_s < 0:
        st.error("🔴 **Alerta Crítica de Pérdidas:** La estrategia planteada destruye el margen comercial. Estás operando por debajo de tu punto de equilibrio financiero [finance].")
    else:
        st.warning(f"🟡 **Escenario de Riesgo Moderado:** Las utilidades proyectadas disminuyen un **{abs(((g_s - g_h)/g_h)*100):.2f}%** frente al histórico básico [finance].")
        
    st.subheader("📊 Proyección del Impacto Financiero Global")
    fig_fin = go.Figure(data=[
        go.Bar(name='Histórico (Pasado)', x=['Ventas Totales', 'Ganancia Neta'], y=[v_h, g_h], marker_color='#636EFA'),
        go.Bar(name='Simulado (Futuro Proyectado)', x=['Ventas Totales Proyectadas', 'Ganancia Proyectada'], y=[v_s, g_s], marker_color='#00CC96')
    ])
    fig_fin.update_layout(barmode='group', height=400)
    fig_fin.update_traces(texttemplate=m_simbolo + '%{y:,.2f}' + m_sufijo, textposition='outside')
    st.plotly_chart(fig_fin, use_container_width=True)
    
    # Asesor de Marketing Sintonizado con Matrices de Contenido Estratégico
    if slider_mkt > 0:
        st.markdown("---")
        st.subheader("📢 Recomendación Avanzada del Asesor Temático")
        
        if modo_mkt == "FACEBOOK_ONLY":
            st.warning(f"⚠️ **Presupuesto Inicial Limitado:** El capital ingresado es bajo para fragmentarlo en múltiples canales. El algoritmo optimiza concentrando el 100% de la pauta en **Facebook Ads** local [finance].")
            st.info(f"🎯 **Tracción Estimada:** Captación proyectada de **{cl_n} clientes nuevos** en el mes.")
            
            # Consultoría Estratégica de Contenido Integrada
            with st.expander("💡 Ideas de Contenido Recomendadas para Facebook (Nicho Abarrotes)", expanded=True):
                st.markdown(f"""
                *   **Post de Tracción Local (Promoción Vecinal):** *"¿Planeando el almuerzo familiar? 🛒 En tu tienda aliada de barrio tenemos el combo arrocero con el 15% de descuento solo por esta semana. ¡Te esperamos a la vuelta de la esquina!"*
                *   **Estrategia de Video Short:** Graba un video de 15 segundos mostrando la llegada de frutas y verduras frescas los días **{analisis['dia_dorado']}**, haciendo énfasis en frescura y economía local.
                *   **Llamado a la Action (CTA):** *"Haz clic en el botón de abajo para pedir tu lista por WhatsApp de forma directa."*
                """)
        else:
            st.info(f"🎯 **Optimización Diversificada:** Asignación inteligente multimedios. Captación estimada de **{cl_n} compradores nuevos** directos [finance].")
            
            datos_mkt = {
                'Red Social': ['Instagram', 'Facebook', 'TikTok', 'Google Ads'],
                'Inversión Sugerida': [ig_i, fb_i, tk_i, gg_i]
            }
            fig_mkt = px.bar(datos_mkt, x='Red Social', y='Inversión Sugerida', text='Inversión Sugerida',
                            color='Red Social',
                            color_discrete_map={'Instagram': '#E1306C', 'Facebook': '#1877F2', 'TikTok': '#000000', 'Google Ads': '#4285F4'})
            fig_mkt.update_traces(texttemplate=m_simbolo + '%{text:,.2f}' + m_sufijo, textposition='outside')
            fig_mkt.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_mkt, use_container_width=True)
            
            # Consultoría Multiplataforma basada en el Producto Estrella del Negocio
            with st.expander("💡 Consultoría Estratégica de Contenido Multiplataforma", expanded=True):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown(f"""
                    **📸 Estrategia para Instagram (Canal Principal - Enfoque Visual):**
                    *   **Idea de Contenido:** Publica carruseles estéticos de alta calidad mostrando "Combos de despensa express". La comida y el orden entran por los ojos.
                    *   **Gancho Visual:** Aprovecha que tu producto con más ventas acumuladas es el artículo **{analisis['mas_vendido']}** para armar ofertas cruzadas estacionales.
                    """)
                with col_c2:
                    st.markdown(f"""
                    **🎵 Estrategia para TikTok (Canal de Virilidad Local):**
                    *   **Idea de Video:** Realiza un reto divertido con tus empleados mostrando "Detrás de escena de cómo ordenamos los abarrotes que más piden los vecinos".
                    *   **Enfoque de Audio:** Utiliza sonidos en tendencia y geolocaliza el video estrictamente en tu municipio/barrio para atraer público real de cercanía.
                    """)

