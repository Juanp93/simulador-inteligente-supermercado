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
        pd.DataFrame({'Fecha': ['01/10/2026', '02/10/2026'], 'Producto': ['Producto A', 'Producto B'], 'Ventas': [100000, 250000], 'Cantidad': [2, 5], 'Cliente': ['Mostrador', 'VIP']}).to_excel(writer, index=False)
    return output.getvalue()

st.markdown("""
<style>
    .metric-container { background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid #636EFA; margin-bottom: 15px; }
    .metric-success { border-left: 5px solid #00CC96; }
    .metric-warning { border-left: 5px solid #FFA15A; }
    .metric-danger { border-left: 5px solid #EF553B; }
    .metric-title { font-size: 13px; color: #A3A3A3; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 22px; color: #FFFFFF; font-weight: bold; margin-top: 5px; }
    .metric-caption { font-size: 12px; color: #858585; margin-top: 4px; line-height: 1.4; }
    .home-card { background-color: #1a1c24; border: 1px solid #2d3139; border-radius: 12px; padding: 25px; margin-bottom: 20px; text-align: center; }
    .home-card h3 { color: #ffffff; margin-bottom: 10px; font-size: 18px; }
    .home-card p { color: #a0aec0; font-size: 14px; margin-bottom: 20px; min-height: 40px; }
    div[data-testid="stSidebarNav"] {display: none;}
    .sidebar-chat { margin-top: 30px; padding-top: 20px; border-top: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. BARRA LATERAL Y CHATBOT INFERIOR IZQUIERDO
# ==============================================================================
with st.sidebar:
    st.title("🧭 Navegación")
    if st.button("🏠 Inicio", use_container_width=True): cambiar_pantalla("home")
    if st.button("⚡ Diagnóstico Express", use_container_width=True): cambiar_pantalla("express")
    if st.button("🔍 Auditoría de Catálogo", use_container_width=True): cambiar_pantalla("diagnostico")
    if st.button("🎛️ Simulador y Marketing IA", use_container_width=True): cambiar_pantalla("simulador")
    if st.button("🎯 Planificador Metas", use_container_width=True): cambiar_pantalla("objetivos")
    
    st.markdown("---")
    selector_moneda = st.selectbox("💱 Divisa a mostrar:", ["COP (Pesos Colombianos)", "USD (Dólares)", "MXN (Pesos Mexicanos)"])
    if selector_moneda == "COP (Pesos Colombianos)": m_factor, m_simbolo, m_sufijo = st.number_input("Tasa (1 USD = X COP):", 100.0, value=4000.0, step=50.0), "$", " COP"
    elif selector_moneda == "MXN (Pesos Mexicanos)": m_factor, m_simbolo, m_sufijo = st.number_input("Tasa (1 USD = X MXN):", 1.0, value=18.5, step=0.5), "$", " MXN"
    else: m_factor, m_simbolo, m_sufijo = 1.0, "$", " USD"

    aplicar_conversion = st.checkbox("🔄 Convertir datos del archivo", help="Marca esta casilla SOLO si tu archivo Excel está en una moneda diferente a la que quieres ver (ej. El archivo está en Dólares, pero arriba seleccionaste COP).", value=False)

    st.markdown("---")
    st.download_button("📥 Bajar Plantilla", generar_plantilla_excel(), "plantilla.xlsx", use_container_width=True)
    archivo = st.file_uploader("📁 Sube tus ventas:", type=['csv', 'xlsx'])
    
    if archivo:
        if archivo.name.endswith('.xlsx'): st.session_state.df_bruto = pd.read_excel(archivo)
        else: st.session_state.df_bruto = pd.read_csv(archivo)
        st.success("¡Datos en memoria!")

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
        Actúa como consultor experto. Identifica el nicho del negocio según los datos provistos y adapta tus recomendaciones de marketing y ventas específicamente a ese sector.
        Responde breve y muy práctico a: {pregunta}
        """
        with chat_container.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    respuesta = modelo_ia.generate_content(prompt_experto)
                    st.write(respuesta.text)
                    st.session_state.historial_chat.append({"role": "assistant", "content": respuesta.text})
                except Exception as e: st.error("Error de conexión.")

# ==============================================================================
# 3. PROCESAMIENTO MATEMÁTICO INTELIGENTE
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
    st.title("🚀 Bienvenido a IntelRetail Pro")
    st.markdown("#### *Tu copiloto estratégico de inteligencia comercial.*")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="home-card"><h3>⚡ Diagnóstico Express</h3><p>Calcula tu rentabilidad separando servicios, productos y gastos a 8 semanas.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Diagnóstico", use_container_width=True, type="primary"): cambiar_pantalla("express"); st.rerun()
        st.markdown('<div class="home-card"><h3>🎛️ Simulador y Marketing IA</h3><p>Proyecta pauta realista y genera campañas automáticas con IA.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Simulador", use_container_width=True): cambiar_pantalla("simulador"); st.rerun()
    with c2:
        st.markdown('<div class="home-card"><h3>🔍 Auditoría de Catálogo</h3><p>Métricas claras sobre la salud de tus productos con ajuste de costos global.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Auditoría", use_container_width=True): cambiar_pantalla("diagnostico"); st.rerun()
        st.markdown('<div class="home-card"><h3>🎯 Planificador Estratégico</h3><p>Proyecta tarifas, meses pico y tu capacidad operativa tope.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Planificador", use_container_width=True): cambiar_pantalla("objetivos"); st.rerun()

elif st.session_state.pantalla_actual == "express":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("⚡ Diagnóstico Financiero Avanzado (Sin Archivos)")
    st.markdown("Ingresa los datos fraccionados de los últimos **2 meses** para un cálculo preciso de tu realidad comercial.")
    
    st.subheader("🗓️ 1. Ingresos Semanales (8 Semanas)")
    sw1, sw2, sw3, sw4 = st.columns(4)
    v_s1 = sw1.number_input("Semana 1", value=1250000.0, step=100000.0)
    v_s2 = sw2.number_input("Semana 2", value=1200000.0, step=100000.0)
    v_s3 = sw3.number_input("Semana 3", value=1300000.0, step=100000.0)
    v_s4 = sw4.number_input("Semana 4", value=1250000.0, step=100000.0)
    
    sw5, sw6, sw7, sw8 = st.columns(4)
    v_s5 = sw5.number_input("Semana 5", value=1250000.0, step=100000.0)
    v_s6 = sw6.number_input("Semana 6", value=1200000.0, step=100000.0)
    v_s7 = sw7.number_input("Semana 7", value=1300000.0, step=100000.0)
    v_s8 = sw8.number_input("Semana 8", value=1250000.0, step=100000.0)
    
    ventas_totales = v_s1 + v_s2 + v_s3 + v_s4 + v_s5 + v_s6 + v_s7 + v_s8
    
    st.subheader("💼 2. Estructura de Negocio y Egresos (Bimestral)")
    c1, c2, c3 = st.columns(3)
    with c1:
        mix_servicios = st.slider("% Ingresos por Servicios (vs. Productos físicos)", 0, 100, 60)
        margen_promedio = st.slider("Margen Neto Promedio (%)", 5, 90, 45)
    with c2:
        gastos_fijos = st.number_input("Gastos Fijos Acumulados (2 Meses)", value=2400000.0)
        gastos_variables = st.number_input("Costos Variables Estimados (2 Meses)", value=600000.0)
    with c3:
        clientes_mes = st.number_input("Atenciones/Clientes Totales (8 Semanas):", value=700)
    
    utilidad = (ventas_totales * (margen_promedio / 100)) - gastos_fijos - gastos_variables
    punto_eq = (gastos_fijos + gastos_variables) / (margen_promedio / 100) if margen_promedio > 0 else 0
    ticket = ventas_totales / clientes_mes if clientes_mes > 0 else 0
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container {"metric-success" if utilidad > 0 else "metric-danger"}"><div class="metric-title">UTILIDAD NETA (8 SEMANAS)</div><div class="metric-value">{m_simbolo}{utilidad:,.2f}</div><div class="metric-caption">Ganancia 100% real y libre del periodo.</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container metric-warning"><div class="metric-title">PUNTO DE EQUILIBRIO BIMESTRAL</div><div class="metric-value">{m_simbolo}{punto_eq:,.2f}</div><div class="metric-caption">Venta mínima en 2 meses para no tener pérdidas.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO</div><div class="metric-value">{m_simbolo}{ticket:,.2f}</div><div class="metric-caption">Dinero promedio por cada cliente atendido.</div></div>', unsafe_allow_html=True)

elif st.session_state.pantalla_actual == "diagnostico":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("📊 Auditoría de Catálogo y Costos")
    if df_final.empty: 
        st.warning("👈 Sube tu archivo de ventas en el menú de la izquierda para comenzar.")
    else:
        st.subheader("⚙️ 1. Ajuste de Costos (Proveedores o Producción)")
        st.markdown("💡 **¿Qué significa esto?** Es el porcentaje del precio de venta que te cuesta adquirir o fabricar el producto. Si vendes algo en $100 y te costó $70 al proveedor, tu costo es del 70%.")
        
        c_sl, c_btn = st.columns([3, 1])
        with c_sl: nuevo_costo_global = st.slider("Asignar un costo global a todo el catálogo (%)", 0.0, 100.0, 70.0, 1.0)
        with c_btn:
            st.write("") 
            st.write("")
            if st.button("Aplicar a todos", use_container_width=True, type="primary"):
                st.session_state.costos_editados['Costo (%)'] = float(nuevo_costo_global)
                st.rerun()

        st.markdown("Edita individualmente usando las celdas de la tabla (Soporta navegación rápida con teclado):")
        st.session_state.costos_editados = st.data_editor(
            st.session_state.costos_editados, hide_index=True, use_container_width=True,
            column_config={"Costo (%)": st.column_config.NumberColumn("Costo (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f %%")}
        )
        
        df_g = df_final.groupby('Product Name').agg({'Quantity': 'sum', 'Sales': 'sum', 'Ganancia_Neta': 'sum'}).reset_index()
        ticket_promedio = df_final['Sales'].sum() / len(df_final) if len(df_final) > 0 else 0
        
        st.markdown("---")
        st.subheader("🏆 2. Métricas Clave (Análisis Humano)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-container metric-success"><div class="metric-title">ESTRELLA (TU MEJOR NEGOCIO)</div><div class="metric-value">{m_simbolo}{df_g["Ganancia_Neta"].max():,.2f}</div><div class="metric-caption"><b>{df_g.loc[df_g["Ganancia_Neta"].idxmax()]["Product Name"]}</b><br>El campeón indiscutible. Es el artículo o servicio que más dinero libre y real deja en tu caja.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">LÍDER EN ROTACIÓN</div><div class="metric-value">{df_g["Quantity"].max()} Unds</div><div class="metric-caption"><b>{df_g.loc[df_g["Quantity"].idxmax()]["Product Name"]}</b><br>El favorito del público. Es el que más unidades vende y atrae el tráfico recurrente a tu local.</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-container metric-danger"><div class="metric-title">DORMIDO (ALERTA DE INVENTARIO)</div><div class="metric-value">{df_g["Quantity"].min()} Unds</div><div class="metric-caption"><b>{df_g.loc[df_g["Quantity"].idxmin()]["Product Name"]}</b><br>¡Alerta roja! Este producto está estancado y tienes dinero congelado. Necesita promoción urgente.</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-container"><div class="metric-title">TICKET PROMEDIO GLOBAL</div><div class="metric-value">{m_simbolo}{ticket_promedio:,.2f}</div><div class="metric-caption">Esta es la facturación media histórica extraída directamente de tu base de datos.</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🎯 3. Matriz BCG: Rentabilidad vs. Rotación")
        fig_bcg = px.scatter(df_g, x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name', hover_name='Product Name', labels={'Quantity': 'Unidades Vendidas', 'Ganancia_Neta': 'Ganancia Neta Libre'})
        fig_bcg.update_layout(showlegend=True, height=500, margin=dict(t=10, l=10, r=10, b=10))
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

        fig_extra.update_layout(height=450, showlegend=False, yaxis=dict(autorange="reversed"), margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_extra, use_container_width=True)

elif st.session_state.pantalla_actual == "simulador":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎛️ Simulador Financiero y Marketing IA")
    
    if df_final.empty: 
        st.warning("👈 Sube tu archivo de ventas en el menú de la izquierda.")
    else:
        st.markdown("### 1. Palancas Comerciales:")
        c1, c2, c3, c4 = st.columns(4)
        
        precio = c1.slider("Ajuste de Precios (%)", -50, 50, 0)
        
        val_inicial = int(25 * m_factor) 
        step_val = int(5 * m_factor)     
        pauta = c2.number_input(f"Presupuesto Pauta ({m_sufijo})", min_value=0, value=val_inicial, step=step_val)
        
        costo_lead = c3.number_input(f"Costo por Lead ({m_sufijo})", min_value=0.1, value=6000.0 if m_sufijo == " COP" else 1.5, help="Costo promedio de llevar a un cliente potencial a preguntar o visitar.")
        
        tasa_conversion = c4.slider("Tasa de Conversión (%)", 1.0, 100.0, 5.0, 0.5, help="Porcentaje realista de personas que terminan comprando. Un 3% a 5% es el estándar en retail.")
        
        factor_precio = 1 + (precio / 100)
        factor_cantidad = 1 - (precio / 100 * 0.5) 
        
        # LA NUEVA MATEMÁTICA REALISTA
        leads_generados = int(pauta / costo_lead) if costo_lead > 0 else 0
        clientes_reales = int(leads_generados * (tasa_conversion / 100))
        
        precio_m = df_final['Sales'].sum() / df_final['Quantity'].sum() if df_final['Quantity'].sum() > 0 else 0
        costo_promedio_porcentaje = st.session_state.costos_editados['Costo (%)'].mean() / 100
        
        v_sim = (df_final['Sales'] * factor_precio * factor_cantidad).sum() + (clientes_reales * precio_m * factor_precio)
        c_sim = (df_final['Sales'] * costo_promedio_porcentaje * factor_cantidad).sum() + (clientes_reales * precio_m * costo_promedio_porcentaje)
        g_sim = v_sim - c_sim - pauta
        
        fig = go.Figure(data=[
            go.Bar(name='Actual', x=['Ventas Totales', 'Ganancia Neta'], y=[df_final['Sales'].sum(), df_final['Ganancia_Neta'].sum()], marker_color='#636EFA', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside'),
            go.Bar(name='Proyectado (Realista)', x=['Ventas Totales', 'Ganancia Neta'], y=[v_sim, g_sim], marker_color='#00CC96', texttemplate=m_simbolo+'%{y:,.0f}', textposition='outside')
        ])
        fig.update_layout(barmode='group', height=400, margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)
        
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
            fig_pauta.update_layout(showlegend=False, margin=dict(t=30, b=10, l=10, r=10), height=350)
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
                with st.spinner("Creando magia... 🪄"):
                    try:
                        res_mkt = modelo_ia.generate_content(prompt_marketing)
                        st.markdown(f"<div style='background-color: #1a1c24; padding: 20px; border-radius: 10px; border-left: 5px solid #00F2FE;'>{res_mkt.text}</div>", unsafe_allow_html=True)
                    except: st.error("Error contactando a la IA.")

elif st.session_state.pantalla_actual == "objetivos":
    if st.button("⬅️ Volver al Inicio"): cambiar_pantalla("home"); st.rerun()
    st.header("🎯 Planificador Estratégico (Modo Dios)")
    
    st.markdown("### Configura el entorno operativo de tu negocio:")
    c1, c2, c3, c4 = st.columns(4)
    with c1: meta = st.number_input(f"Ganancia Deseada ({m_sufijo}):", value=10000000.0, step=500000.0)
    with c2: meses = st.slider("Horizonte (Meses):", 1, 12, 1)
    with c3: gastos = st.number_input(f"Gastos Fijos/Mes ({m_sufijo}):", value=1500000.0, step=100000.0)
    with c4: capacidad_max = st.number_input("Tope Operativo Diario:", value=20)
        
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
    alerta_capacidad = "metric-danger" if clientes_diarios > capacidad_max else "metric-warning"
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.markdown(f'<div class="metric-container metric-success"><div class="metric-title">FACTURACIÓN TOTAL REQUERIDA</div><div class="metric-value">{m_simbolo}{ventas_totales_req:,.2f}</div><div class="metric-caption">Ventas necesarias estimadas en {meses} mes(es).</div></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="metric-container"><div class="metric-title">META DE VENTA DIARIA</div><div class="metric-value">{m_simbolo}{ventas_diarias_req:,.2f}</div><div class="metric-caption">Venta mínima promedio cada día para llegar al objetivo.</div></div>', unsafe_allow_html=True)
    r3.markdown(f'<div class="metric-container {alerta_capacidad}"><div class="metric-title">CLIENTES DIARIOS REQUERIDOS</div><div class="metric-value">{clientes_diarios} Compras/Día</div><div class="metric-caption">Límite Operativo configurado: {capacidad_max} atenciones al día.</div></div>', unsafe_allow_html=True)
    
    if clientes_diarios > capacidad_max:
        st.error(f"🚨 ¡ALERTA OPERATIVA! Tu meta requiere {clientes_diarios} clientes diarios, pero tu negocio solo soporta {capacidad_max}. Debes subir tus tarifas, reducir tus costos operativos o extender el plazo de la meta.")
