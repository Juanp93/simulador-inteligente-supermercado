import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import google.generativeai as genai

# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="IntelRetail Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# ESTILOS CORPORATIVOS (MODO OSCURO ENTERPRISE - SIN VIDEOS)
# ==============================================================================
st.markdown("""
<style>
    .stApp {
        background-color: #080D10 !important;
        color: #F3F4F6 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0C1519 !important;
        border-right: 1px solid rgba(207, 157, 123, 0.2) !important;
    }
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    .metric-container, .home-card { 
        background: linear-gradient(135deg, rgba(22, 33, 39, 0.75) 0%, rgba(12, 21, 25, 0.90) 100%);
        border: 1px solid rgba(114, 75, 57, 0.35); 
        border-radius: 16px; 
        color: #F3F4F6; 
        box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    }
    .metric-container { padding: 22px; margin-bottom: 15px; border-left: 4px solid #CF9D7B; }
    .metric-success { border-left: 4px solid #00CC96; }
    .metric-warning { border-left: 4px solid #FFA15A; }
    .metric-danger { border-left: 4px solid #EF553B; }
    
    .metric-title { font-size: 12px; color: #CF9D7B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 26px; color: #FFFFFF; font-weight: 700; margin-top: 8px; margin-bottom: 4px; }
    .metric-caption { font-size: 12px; color: #8F95A3; line-height: 1.4; }
    
    .home-card { padding: 30px; margin-bottom: 20px; text-align: center; }
    .home-card h3 { color: #FFFFFF; margin-bottom: 12px; font-size: 19px; font-weight: 600; }
    .home-card p { color: #8F95A3; font-size: 14px; margin-bottom: 25px; min-height: 45px; line-height: 1.5; }
    .sidebar-chat { margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(114, 75, 57, 0.2); }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# INICIALIZACIÓN DE ESTADOS
# ==============================================================================
if 'pantalla_actual' not in st.session_state: st.session_state.pantalla_actual = "home"
if 'df_bruto' not in st.session_state: st.session_state.df_bruto = pd.DataFrame()
if 'costos_editados' not in st.session_state: st.session_state.costos_editados = pd.DataFrame()
if 'apuntes_ia' not in st.session_state: st.session_state.apuntes_ia = ""

# ==============================================================================
# FUNCIÓN DE REPORTE EJECUTIVO
# ==============================================================================
def generar_informe_texto(ventas_tot, ganancia_tot, simbolo, notas_ia, ticket, estrella, dormido):
    contenido = f"""
======================================================================
              INTELRETAIL PRO - REPORTE EJECUTIVO GLOBAL
======================================================================
Fecha de Emisión: Reporte en Tiempo Real
Generado por: Inteligencia Comercial Automatizada

[ 1. ESTADO FINANCIERO DEL CATÁLOGO ]
----------------------------------------------------------------------
> Ventas Totales Registradas : {simbolo}{ventas_tot:,.2f}
> Ganancia Neta Libre        : {simbolo}{ganancia_tot:,.2f}
> Ticket Promedio por Venta  : {simbolo}{ticket:,.2f}

[ 2. RENDIMIENTO DE INVENTARIO ]
----------------------------------------------------------------------
> Producto ESTRELLA (Top Ganancia) : {estrella}
> Producto DORMIDO (Baja Rotación) : {dormido}
* Nota: Revisa la Matriz ABC en la plataforma para detalles de stock.

[ 3. ESTRATEGIAS Y APUNTES DE INTELIGENCIA ARTIFICIAL ]
----------------------------------------------------------------------
{notas_ia if notas_ia != "" else "No se solicitaron estrategias a la IA durante esta sesión."}

======================================================================
     Gracias por utilizar IntelRetail Pro - Tu Copiloto Estratégico.
======================================================================
"""
    return contenido.encode('utf-8')

# ==============================================================================
# BARRA LATERAL DE NAVEGACIÓN Y CONFIGURACIÓN
# ==============================================================================
with st.sidebar:
    st.title("🚀 IntelRetail Pro")
    st.markdown("---")
    
    if st.button("🏠 Inicio / Carga", use_container_width=True):
        st.session_state.pantalla_actual = "home"
        st.rerun()
    if st.button("⚡ Diagnóstico Express", use_container_width=True):
        st.session_state.pantalla_actual = "diagnostico"
        st.rerun()
    if st.button("📊 Auditoría de Catálogo", use_container_width=True):
        st.session_state.pantalla_actual = "diagnostico"
        st.rerun()
        
    st.markdown("---")
    st.subheader("⚙️ Configuración Global")
    m_moneda = st.selectbox("Moneda", ["COP ($)", "USD ($)", "EUR (€)"])
    m_simbolo = "$" if "$" in m_moneda else "€"
    aplicar_conversion = st.checkbox("Aplicar factor multiplicador", value=False)
    m_factor = st.number_input("Factor", value=1.0, min_value=0.1, step=0.1)

# ==============================================================================
# 3. PROCESAMIENTO MATEMÁTICO (GLOBAL CON CANDADO DE SEGURIDAD)
# ==============================================================================
df_final = pd.DataFrame()
if not st.session_state.df_bruto.empty:
    df_temp = st.session_state.df_bruto.copy().dropna(how='all')
    col_map = {}
    for col in df_temp.columns:
        c = str(col).strip().lower()
        if any(x in c for x in ['venta', 'sales', 'monto']) and 'Sales' not in col_map.values(): col_map[col] = 'Sales'
        elif any(x in c for x in ['producto', 'product', 'sku']) and 'Product Name' not in col_map.values(): col_map[col] = 'Product Name'
        elif any(x in c for x in ['cantidad', 'quantity', 'cant']) and 'Quantity' not in col_map.values(): col_map[col] = 'Quantity'
        elif any(x in c for x in ['cliente', 'customer']) and 'Customer Name' not in col_map.values(): col_map[col] = 'Customer Name'
            
    df_temp = df_temp.rename(columns=col_map)
    df_temp = df_temp.loc[:, ~df_temp.columns.duplicated()] 
    
    if 'Product Name' in df_temp.columns:
        df_temp['Product Name'] = df_temp['Product Name'].replace(r'^\s*$', np.nan, regex=True)
        df_temp = df_temp.dropna(subset=['Product Name'])
        df_temp = df_temp[~df_temp['Product Name'].astype(str).str.lower().str.contains('total', na=False)]
    
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
# ENRUTAMIENTO DE PANTALLAS
# ==============================================================================
if st.session_state.pantalla_actual == "home":
    st.markdown("<h1 style='text-align: center;'>🚀 Bienvenido a IntelRetail Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8F95A3;'>Tu copiloto estratégico de inteligencia comercial.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class='home-card'>
            <h3>⚡ Diagnóstico y Auditoría</h3>
            <p>Carga tu archivo de datos para auditar costos, márgenes y clasificar el inventario automáticamente.</p>
        </div>
        """, unsafe_allow_html=True)
        archivo_subido = st.file_uploader("Sube tu archivo Excel o CSV", type=["xlsx", "csv"])
        if archivo_subido:
            try:
                if archivo_subido.name.endswith('.csv'):
                    st.session_state.df_bruto = pd.read_csv(archivo_subido)
                else:
                    st.session_state.df_bruto = pd.read_excel(archivo_subido)
                st.success("¡Archivo cargado con éxito!")
                if st.button("Ir a Auditoría de Catálogo"):
                    st.session_state.pantalla_actual = "diagnostico"
                    st.rerun()
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

    with col2:
        st.markdown("""
        <div class='home-card'>
            <h3>📊 Estado del Sistema</h3>
            <p>Monitorea registros cargados y configura los parámetros globales de simulación de tu negocio.</p>
        </div>
        """, unsafe_allow_html=True)
        if not st.session_state.df_bruto.empty:
            st.info(f"Registros activos en memoria: {len(st.session_state.df_bruto)}")
        else:
            st.warning("No hay datos cargados actualmente.")

elif st.session_state.pantalla_actual == "diagnostico":
    st.title("📊 Auditoría de Catálogo e Inteligencia Comercial")
    
    if df_final.empty:
        st.warning("⚠️ Por favor carga un archivo de datos desde la pantalla de Inicio para ver la auditoría.")
    else:
        # Métricas principales
        ventas_totales_global = df_final['Sales'].sum()
        ganancia_neta_global = df_final['Ganancia_Neta'].sum()
        ticket_promedio = ventas_totales_global / df_final['Quantity'].sum() if df_final['Quantity'].sum() > 0 else 0
        
        df_prod = df_final.groupby('Product Name').agg({'Sales': 'sum', 'Ganancia_Neta': 'sum', 'Quantity': 'sum'}).reset_index()
        prod_estrella = df_prod.loc[df_prod['Ganancia_Neta'].idxmax()]['Product Name'] if not df_prod.empty else "N/A"
        prod_dormido = df_prod.loc[df_prod['Quantity'].idxmin()]['Product Name'] if not df_prod.empty else "N/A"

        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"{m_simbolo}{ventas_totales_global:,.2f}")
        c2.metric("Ganancia Neta Libre", f"{m_simbolo}{ganancia_neta_global:,.2f}")
        c3.metric("Ticket Promedio", f"{m_simbolo}{ticket_promedio:,.2f}")

        # ==============================================================================
        # MÓDULO FASE 2: SEGMENTACIÓN ABC (PARETO)
        # ==============================================================================
        st.markdown("---")
        st.subheader("🥇 2.5 Segmentación Inteligente ABC (Ley de Pareto)")
        st.markdown("Clasificación matemática automática de tu catálogo basada en la ganancia real que aportan a la caja.")
        
        df_pareto = df_prod.copy()
        df_pareto = df_pareto.sort_values(by='Ganancia_Neta', ascending=False).reset_index(drop=True)
        total_ganancia_positiva = df_pareto[df_pareto['Ganancia_Neta'] > 0]['Ganancia_Neta'].sum()
        
        if total_ganancia_positiva > 0:
            df_pareto['Porcentaje'] = np.where(df_pareto['Ganancia_Neta'] > 0, df_pareto['Ganancia_Neta'] / total_ganancia_positiva * 100, 0)
            df_pareto['Acumulado'] = df_pareto['Porcentaje'].cumsum()
            condiciones = [
                (df_pareto['Acumulado'] <= 80) & (df_pareto['Ganancia_Neta'] > 0),
                (df_pareto['Acumulado'] > 80) & (df_pareto['Acumulado'] <= 95) & (df_pareto['Ganancia_Neta'] > 0)
            ]
            opciones = ['🥇 Tipo A (Top 80%)', '🥈 Tipo B (Medio 15%)']
            df_pareto['Clasificación'] = np.select(condiciones, opciones, default='🥉 Tipo C (Bajo 5% o Pérdida)')
        else:
            df_pareto['Clasificación'] = '🥉 Tipo C (Pérdida)'

        cat_A = len(df_pareto[df_pareto['Clasificación'].str.contains('Tipo A')])
        cat_B = len(df_pareto[df_pareto['Clasificación'].str.contains('Tipo B')])
        cat_C = len(df_pareto[df_pareto['Clasificación'].str.contains('Tipo C')])

        col_a, col_b, col_c = st.columns(3)
        col_a.info(f"🥇 **{cat_A} Prod. Tipo A:** Nunca te quedes sin stock. Estos sostienen toda tu rentabilidad.")
        col_b.warning(f"🥈 **{cat_B} Prod. Tipo B:** Rotación estándar y estable. Vigila que sus costos no suban.")
        col_c.error(f"🥉 **{cat_C} Prod. Tipo C:** Capital congelado. ¡Urge armar promociones para liquidar esto!")
        
        st.dataframe(
            df_pareto[['Product Name', 'Clasificación', 'Ganancia_Neta', 'Quantity']],
            hide_index=True,
            use_container_width=True,
            column_config={
                "Product Name": "Nombre del Producto",
                "Clasificación": "Clasificación ABC",
                "Ganancia_Neta": st.column_config.NumberColumn("Dinero Libre Aportado", format=f"{m_simbolo}%.2f"),
                "Quantity": "Unidades Vendidas"
            }
        )

        # ==============================================================================
        # MATRIZ BCG Y DESCARGA EJECUTIVA
        # ==============================================================================
        st.markdown("---")
        st.subheader("🎯 3. Matriz BCG: Rentabilidad vs. Rotación")
        fig_bcg = px.scatter(df_prod, x='Quantity', y='Ganancia_Neta', size='Sales', color='Product Name', hover_name='Product Name')
        st.plotly_chart(fig_bcg, use_container_width=True)

        st.markdown("---")
        st.subheader("📥 4. Reporte Ejecutivo y Estrategias IA")
        
        if st.button("🤖 Generar Análisis Estratégico con IA"):
            try:
                # Código restaurado con la sintaxis correcta que ya te funcionaba
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Analiza estos datos de un negocio: Ventas totales {ventas_totales_global}, Ganancia neta {ganancia_neta_global}, Producto estrella {prod_estrella}. Dame 3 recomendaciones comerciales gerenciales clave en español."
                response = model.generate_content(prompt)
                st.session_state.apuntes_ia = response.text
                st.success("¡Estrategias generadas con éxito por la IA!")
            except Exception as e:
                st.error(f"Error al conectar con la IA: {e}")

        if st.session_state.apuntes_ia != "":
            with st.expander("📝 Apuntes Estratégicos de la IA", expanded=True):
                st.markdown(st.session_state.apuntes_ia)

        txt_reporte = generar_informe_texto(ventas_totales_global, ganancia_neta_global, m_simbolo, st.session_state.apuntes_ia, ticket_promedio, prod_estrella, prod_dormido)
        st.download_button(
            label="📥 Descargar Informe Ejecutivo Gerencial (.txt)",
            data=txt_reporte,
            file_name="Reporte_Ejecutivo_IntelRetail.txt",
            mime="text/plain"
        )
