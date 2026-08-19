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
</style>
""", unsafe_allow_html=True)

st.title("📈 IntelRetail Pro: Sistema de Inteligencia de Negocios y Simulación")
st.markdown("Plataforma de diagnóstico operativo, optimización de presupuestos y modelado de escenarios comerciales para retail y microempresas.")
st.markdown("---")

# ==============================================================================
# LOCALIZACIÓN Y GESTIÓN DE DIVISAS
# ==============================================================================
st.sidebar.header("💱 Configuración de Divisa")
selector_moneda = st.sidebar.selectbox("Selecciona la moneda de visualización:", ["COP (Pesos Colombianos)", "USD (Dólares)", "MXN (Pesos Mexicanos)"])

config_moneda = {
    "COP (Pesos Colombianos)": {"factor": 4000.0, "simbolo": "$", "sufijo": " COP"},
    "USD (Dólares)": {"factor": 1.0, "simbolo": "$", "sufijo": " USD"},
    "MXN (Pesos Mexicanos)": {"factor": 18.5, "simbolo": "$", "sufijo": " MXN"}
}
m_factor = config_moneda[selector_moneda]["factor"]
m_simbolo = config_moneda[selector_moneda]["simbolo"]
m_sufijo = config_moneda[selector_moneda]["sufijo"]

# ==============================================================================
# CARGA DE ARCHIVO Y PLANTILLA CSV
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("📁 Carga de Información Financiera")

# Generador de plantilla descargable
@st.cache_data
def generar_plantilla_csv():
    df_plantilla = pd.DataFrame({
        'Order Date': ['01/10/2026', '02/10/2026', '03/10/2026'],
        'Product Name': ['Arroz Premium 1kg', 'Aceite Vegetal 900ml', 'Leche Entera 1L'],
        'Sales': [1.25, 2.50, 1.10],
        'Quantity': [10, 5, 12],
        'Customer Name': ['Cliente Mostrador', 'Supermercado Central', 'Tienda Doña Rosa']
    })
    return df_plantilla.to_csv(index=False).encode('utf-8')

st.sidebar.download_button(
    label="📥 Descargar Plantilla CSV Oficial",
    data=generar_plantilla_csv(),
    file_name="plantilla_ventas_intelretail.csv",
    mime="text/csv",
    help="Descarga este formato, complétalo con las ventas de tu negocio y súbelo aquí."
)

archivo_usuario = st.sidebar.file_uploader("Sube el archivo CSV de ventas de tu negocio:", type=['csv'])

# ==============================================================================
# FUNCIONES CORE CON CACHÉ DE RENDIMIENTO
# ==============================================================================
@st.cache_data
def limpiar_y_preparar_datos(file_bytes, porcentaje_costo_proveedor, factor_divisa):
    df_temp = pd.read_csv(io.BytesIO(file_bytes) if isinstance(file_bytes, bytes) else file_bytes)
    df_temp = df_temp.dropna(subset=['Order Date', 'Sales'])
    df_temp['Order Date'] = pd.to_datetime(df_temp['Order Date'], format='%d/%m/%Y', errors='coerce')
    df_temp = df_temp[df_temp['Sales'] > 0]
    
    # Conversión de divisa
    df_temp['Sales_Original'] = df_temp['Sales']
    df_temp['Sales'] = df_temp['Sales_Original'] * factor_divisa
    
    # Si el CSV no incluye columna Quantity, se genera una estimación
    if 'Quantity' not in df_temp.columns:
        np.random.seed(42)
        df_temp['Quantity'] = np.random.randint(1, 6, size=len(df_temp))
        
    factor_costo = porcentaje_costo_proveedor / 100
    df_temp['Costo_Proveedor'] = df_temp['Sales'] * factor_costo
    df_temp['Ganancia_Neta'] = df_temp['Sales'] - df_temp['Costo_Proveedor']
    return df_temp

def analizar_datos_avanzados(df_limpio):
    df_agrupado = df_limpio.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
    df_limpio['Precio_Unitario'] = df_limpio['Sales'] / df_limpio['Quantity']
    
    df_limpio['Dia_Semana'] = df_limpio['Order Date'].dt.day_name()
    mapeo_dias = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
    df_limpio['Dia_Semana'] = df_limpio['Dia_Semana'].map(mapeo_dias)
    dia_dorado = df_limpio.groupby('Dia_Semana')['Sales'].sum().idxmax()
    
    ticket_promedio = df_limpio['Sales'].sum() / len(df_limpio)
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
# CARGA DEL DATASET
# ==============================================================================
with st.sidebar.expander("⚙️ Configuración de Costos (CSV)", expanded=True):
    slider_costo_prov = st.slider("Costo del Proveedor (%)", min_value=10, max_value=90, value=70, step=5)

if archivo_usuario is not None:
    df_app = limpiar_y_preparar_datos(archivo_usuario.getvalue(), slider_costo_prov, m_factor)
    st.sidebar.success("¡Datos empresariales procesados con éxito!")
else:
    try:
        with open('train.csv', 'rb') as f:
            df_app = limpiar_y_preparar_datos(f.read(), slider_costo_prov, m_factor)
        st.sidebar.info("Utilizando registros maestros de demostración.")
    except:
        st.error("Error: Falta el archivo base 'train.csv'. Por favor sube un archivo CSV.")
        st.stop()

analisis = analizar_datos_avanzados(df_app)

# ==============================================================================
# PESTAÑAS DE LA APLICACIÓN
# ==============================================================================
pestana_express, pestana_diagnostico, pestana_simulador = st.tabs([
    "⚡ Diagnóstico Express (Sin CSV)",
    "🔍 Diagnóstico Avanzado de Catálogo",
    "🎛️ Simulador de Escenarios Estratégicos"
])

# ---- PESTAÑA 1: DIAGNÓSTICO EXPRESS (PARA MICRO-NEGOCIOS) ----
with pestana_express:
    st.header("⚡ Diagnóstico Rápido para Micro-Comercios")
    st.markdown("¿No tienes un historial masivo de ventas? Ingresa las métricas estimadas de tu negocio para obtener un análisis financiero instantáneo.")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        venta_mensual_est = st.number_input(f"Venta estimada promedio al mes ({m_sufijo}):", min_value=100.0, value=5000000.0 if selector_moneda == "COP (Pesos Colombianos)" else 2000.0, step=50000.0 if selector_moneda == "COP (Pesos Colombianos)" else 100.0)
        margen_bruto_pct = st.slider("Margen bruto sobre productos (% de ganancia estimada):", min_value=5, max_value=80, value=30, step=1)
    
    with col_e2:
        gastos_fijos_est = st.number_input(f"Gastos fijos mensuales (Arriendo, nómina, servicios en {m_sufijo}):", min_value=0.0, value=1200000.0 if selector_moneda == "COP (Pesos Colombianos)" else 500.0, step=50000.0 if selector_moneda == "COP (Pesos Colombianos)" else 50.0)
        clientes_mes_est = st.number_input("Número estimado de transacciones / clientes atendidos al mes:", min_value=1, value=350, step=10)

    # Cálculos Financieros Express
    utilidad_bruta_est = venta_mensual_est * (margen_bruto_pct / 100)
    utilidad_neta_est = utilidad_bruta_est - gastos_fijos_est
    ticket_prom_express = venta_mensual_est / clientes_mes_est
    
    # Punto de Equilibrio (Break-Even)
    punto_equilibrio_ventas = gastos_fijos_est / (margen_bruto_pct / 100) if margen_bruto_pct > 0 else 0
    clientes_punto_equilibrio = int(punto_equilibrio_ventas / ticket_prom_express) if ticket_prom_express > 0 else 0
    
    st.markdown("---")
    st.subheader("📌 Resultados del Diagnóstico Operativo")
    
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.markdown(f"""
        <div class="metric-container {'metric-success' if utilidad_neta_est > 0 else 'metric-danger'}">
            <div class="metric-title">💼 UTILIDAD NETA MENSUAL ESTIMADA</div>
            <div class="metric-value">{m_simbolo}{utilidad_neta_est:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Rendimiento después de cubrir costos y gastos fijos.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_r2:
        st.markdown(f"""
        <div class="metric-container metric-warning">
            <div class="metric-title">⚖️ PUNTO DE EQUILIBRIO FINANCIERO</div>
            <div class="metric-value">{m_simbolo}{punto_equilibrio_ventas:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Ventas mínimas requeridas para no operar en pérdidas.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_r3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">🛒 TICKET PROMEDIO / TRANSACCIÓN</div>
            <div class="metric-value">{m_simbolo}{ticket_prom_express:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Equivale a unos <b>{clientes_punto_equilibrio} clientes mínimos/mes</b> para el punto de equilibrio.</div>
        </div>
        """, unsafe_allow_html=True)

    # Recomendación Táctica para el Micro-Comercio
    st.markdown("### 💡 Plan de Acción Inmediato")
    if utilidad_neta_est < 0:
        st.error(f"⚠️ **Atención:** Actualmente estás por debajo de tu punto de equilibrio por **{m_simbolo}{abs(utilidad_neta_est):,.2f}{m_sufijo}**. Necesitas incrementar tus ventas mensuales en al menos {m_simbolo}{punto_equilibrio_ventas - venta_mensual_est:,.2f} o renegociar costos fijos.")
    else:
        st.success(f"✅ **Operación Saludable:** Tu negocio genera utilidades y supera el punto de equilibrio por **{m_simbolo}{venta_mensual_est - punto_equilibrio_ventas:,.2f}{m_sufijo}** al mes.")

    with st.expander("🚀 Estrategias Clave para Aumentar el Ticket Promedio sin Gastar en Publicidad", expanded=True):
        st.markdown("""
        * **Combos de Necesidad Inmediata (Cross-Selling):** Agrupa productos complementarios que el cliente suele olvidar (ej. arroz + aceite, o bebidas + pasabocas) con un descuento simbólico del 5%.
        * **Anclaje de Precios en Mostrador:** Coloca cerca de la caja artículos de bajo valor y alta rotación para compras de último momento por impulso.
        * **Fidelización por Recurrencia:** Ofrece una tarjeta física de sellos (ej. 'En tu décima compra, recibe un 10% de descuento') para incentivar visitas semanales.
        """)

# ---- PESTAÑA 2: DIAGNÓSTICO AVANZADO DE CATÁLOGO ----
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
            <div class="metric-value">{analisis['cant_mas_vendido']:,} {'Unidad' if analisis['cant_mas_vendido'] == 1 else 'Unidades'}</div>
            <div class="metric-caption"><b>SKU / Nombre:</b> {analisis['mas_vendido']}</div>
        </div>
        <div class="metric-container">
            <div class="metric-title">🛒 TICKET PROMEDIO POR TRANSACCIÓN</div>
            <div class="metric-value">{m_simbolo}{analisis['ticket_promedio']:,.2f}{m_sufijo}</div>
            <div class="metric-caption">Monto medio facturado por cada orden de compra.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown(f"""
        <div class="metric-container metric-danger">
            <div class="metric-title">💤 ALERTA: PRODUCTO DORMIDO (BAJA ROTACIÓN)</div>
            <div class="metric-value">{analisis['cant_menos_vendido']} {'Unidad' if analisis['cant_menos_vendido'] == 1 else 'Unidades'}</div>
            <div class="metric-caption"><b>SKU / Nombre:</b> {analisis['menos_vendido']}<br><span style='color:#FF6B6B;'>Riesgo de dinero inmovilizado en inventario.</span></div>
        </div>
        <div class="metric-container">
            <div class="metric-title">🗓️ DÍA DORADO DE FACTURACIÓN</div>
            <div class="metric-value">Cada {analisis['dia_dorado']}</div>
            <div class="metric-caption">Día de la semana con mayor concentración de ventas.</div>
        </div>
        <div class="metric-container">
            <div class="metric-title">💰 RANGO DE PRECIOS EN CATÁLOGO</div>
            <div class="metric-value">Máx: {m_simbolo}{analisis['precio_mas_caro']:,.2f}</div>
            <div class="metric-caption">Mínimo registrado: {m_simbolo}{analisis['precio_mas_barato']:,.2f}{m_sufijo}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("👥 Concentración de Ventas: Top 5 Clientes de Mayor Valor")
    fig_cl = px.bar(
        analisis['top_clientes'], x='Sales', y='Customer Name', orientation='h',
        labels={'Sales': f'Total Facturado ({m_sufijo})', 'Customer Name': 'Cliente'},
        color='Sales', color_continuous_scale='Blues'
    )
    fig_cl.update_layout(height=320, showlegend=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_cl, use_container_width=True)

# ---- PESTAÑA 3: SIMULADOR DE ESCENARIOS ----
with pestana_simulador:
    st.header("🎛️ Modelado Financiero Predictivo")
    
    with st.sidebar.expander("🎯 Palanca de Decisiones (Simulador)", expanded=True):
        slider_precio = st.slider("Ajuste de Precios (%)", min_value=-20, max_value=20, value=0, step=1)
        max_p_mkt = 5000000 if selector_moneda == "COP (Pesos Colombianos)" else 2000
        step_p_mkt = 100000 if selector_moneda == "COP (Pesos Colombianos)" else 50
        slider_mkt = st.slider("Presupuesto Publicitario", min_value=0, max_value=max_p_mkt, value=0, step=step_p_mkt)

    v_h, g_h, v_s, g_s = simular_escenario_negocio(df_app, slider_precio, slider_mkt, slider_costo_prov)
    ig_i, fb_i, tk_i, gg_i, cl_n, modo_mkt = optimizar_marketing_avanzado(slider_mkt)
    
    if g_s > g_h:
        st.success(f"🟢 **Escenario Favorable:** Las proyecciones estiman un incremento en las ganancias netas del **{((g_s - g_h)/g_h)*100:.2f}%**.")
    elif g_s < 0:
        st.error("🔴 **Alerta Crítica de Pérdidas:** La estrategia planteada destruye el margen comercial. Estás operando por debajo de tu punto de equilibrio financiero.")
    else:
        st.warning(f"🟡 **Escenario de Riesgo Moderado:** Las utilidades proyectadas disminuyen un **{abs(((g_s - g_h)/g_h)*100):.2f}%** frente al histórico básico.")
        
    st.subheader("📊 Proyección del Impacto Financiero Global")
    
    # Gráfico agrupado corregido
    fig_fin = go.Figure(data=[
        go.Bar(name='Histórico (Pasado)', x=['Ventas Totales', 'Ganancia Neta'], y=[v_h, g_h], marker_color='#636EFA'),
        go.Bar(name='Simulado (Futuro Proyectado)', x=['Ventas Totales', 'Ganancia Neta'], y=[v_s, g_s], marker_color='#00CC96')
    ])
    fig_fin.update_layout(barmode='group', height=400, yaxis_title=f"Monto ({m_sufijo})")
    fig_fin.update_traces(texttemplate=m_simbolo + '%{y:,.2f}' + m_sufijo, textposition='outside')
    st.plotly_chart(fig_fin, use_container_width=True)
    
    if slider_mkt > 0:
        st.markdown("---")
        st.subheader("📢 Recomendación de Asignación Presupuestal")
        
        if modo_mkt == "FACEBOOK_ONLY":
            st.warning(f"⚠️ **Presupuesto Inicial Concentrado:** El capital ingresado rinde mejor concentrando el 100% de la pauta en **Facebook Ads** local.")
            st.info(f"🎯 **Tracción Estimada:** Captación proyectada de **{cl_n} clientes nuevos** en el período.")
            
            with st.expander("💡 Ideas de Contenido Recomendadas para Facebook (Comercio Local)", expanded=True):
                st.markdown(f"""
                * **Post de Tracción Local (Promoción Vecinal):** *"¿Planeando las compras del hogar? 🛒 En tu tienda aliada de barrio tenemos promociones especiales esta semana. ¡Te esperamos!"*
                * **Estrategia de Video Corto:** Graba un video de 15 segundos mostrando la llegada de productos frescos los días **{analisis['dia_dorado']}**, destacando variedad y precios justos.
                * **Llamado a la Acción (CTA):** *"Haz clic en el botón para hacer tu pedido directo por WhatsApp con entrega rápida."*
                """)
        else:
            st.info(f"🎯 **Optimización Diversificada:** Asignación multimedios equilibrada. Captación estimada de **{cl_n} compradores nuevos**.")
            
            datos_mkt = {
                'Red Social': ['Instagram', 'Facebook', 'TikTok', 'Google Ads'],
                'Inversión Sugerida': [ig_i, fb_i, tk_i, gg_i]
            }
            fig_mkt = px.bar(
                datos_mkt, x='Red Social', y='Inversión Sugerida', text='Inversión Sugerida',
                color='Red Social',
                color_discrete_map={'Instagram': '#E1306C', 'Facebook': '#1877F2', 'TikTok': '#25F4EE', 'Google Ads': '#4285F4'}
            )
            fig_mkt.update_traces(texttemplate=m_simbolo + '%{text:,.2f}' + m_sufijo, textposition='outside')
            fig_mkt.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_mkt, use_container_width=True)
            
            with st.expander("💡 Consultoría Estratégica de Contenido Multiplataforma", expanded=True):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown(f"""
                    **📸 Estrategia para Instagram (Canal Visual):**
                    * **Idea de Contenido:** Publica carruseles con fotos claras mostrando 'Combos de despensa express'.
                    * **Gancho Visual:** Aprovecha tu producto líder en rotación (**{analisis['mas_vendido']}**) para diseñar promociones cruzadas.
                    """)
                with col_c2:
                    st.markdown(f"""
                    **🎵 Estrategia para TikTok (Canal de Alcance Local):**
                    * **Idea de Video:** Muestra el detrás de escena del negocio preparando los pedidos más populares de la semana.
                    * **Enfoque de Audio:** Usa audios en tendencia y etiqueta tu ciudad/barrio para atraer clientes del sector.
                    """)
