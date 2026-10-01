import streamlit as st
import pandas as pd
import gspread
import datetime

# CONFIGURACIÓN DE PÁGINA (Debe ser la primera orden de Streamlit)
st.set_page_config(page_title="Calendario Compartido", layout="wide")

# AUTENTICACIÓN Y CARGA DE DATOS DESDE GOOGLE SHEETS
@st.cache_data(ttl=10)  # Recarga datos cada 10 segundos
def cargar_datos_sheets():
    credentials = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Calendario_Compartido")
    worksheet = sh.get_worksheet(0)
    
    datos = worksheet.get_all_records()
    df = pd.DataFrame(datos)
    
    if not df.empty and "Fecha" in df.columns:
        # Homologar la columna Fecha a tipo datetime
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df

# FUNCIÓN PARA GUARDAR NUEVA FILA EN GOOGLE SHEETS
def guardar_en_sheets(fecha, actividad, persona, prioridad):
    credentials = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Calendario_Compartido")
    worksheet = sh.get_worksheet(0)
    
    # Formato AAAA-MM-DD para guardar en la hoja
    fecha_str = fecha.strftime("%Y-%m-%d")
    
    # Insertar la fila al final de la hoja
    worksheet.append_row([fecha_str, actividad, persona, prioridad])

# CARGAR DATOS
df_actividades = cargar_datos_sheets()

st.title("📅 Calendario Compartido Alexos 📅")

# COLORES ASIGNADOS
COLORES_PERSONAS = {
    "Alex": "#87CEEB",
    "Alexa": "#E4007C",
}

# BARRA LATERAL: AGREGAR ACTIVIDAD
st.sidebar.header("➕ Agregar nueva actividad")

persona = st.sidebar.selectbox("¿Quién la agrega?", list(COLORES_PERSONAS.keys()))
actividad = st.sidebar.text_input("Descripción de la actividad")
fecha = st.sidebar.date_input("Fecha de la actividad", value=datetime.date.today())
prioridad = st.sidebar.selectbox("Prioridad", ["Baja", "Media", "Alta"])

if st.sidebar.button("Guardar Actividad"):
    if actividad.strip():
        try:
            # 1. Escribir directamente en Google Sheets
            guardar_en_sheets(fecha, actividad, persona, prioridad)
            
            # 2. Limpiar el caché de la lectura
            st.cache_data.clear()
            
            st.sidebar.success("¡Actividad Guardada en Google Sheets!")
            
            # 3. Recargar la aplicación para mostrar los datos nuevos
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error al guardar: {e}")
    else:
        st.sidebar.error("Por favor, ingresa una descripción")

# VISTA DEL DÍA ACTUAL
hoy = datetime.date.today()
st.header(f"☀️ Tareas de Hoy ({hoy.strftime('%d/%m/%Y')})")

if not df_actividades.empty and "Fecha" in df_actividades.columns:
    # Filtrar convirtiendo hoy a Timestamp para comparar con el dataframe
    df_hoy = df_actividades[df_actividades["Fecha"].dt.date == hoy]
else:
    df_hoy = pd.DataFrame()

if not df_hoy.empty:
    for idx, row in df_hoy.iterrows():
        color = COLORES_PERSONAS.get(row["Persona"], "#CCCCCC")
        st.markdown(
            f"""
            <div style="background-color: {color}22; border-left: 6px solid {color}; padding: 10px; border-radius: 5px; margin-bottom: 8px;">
                <strong>👤 {row['Persona']}</strong> — {row['Actividad']} <em>(Prioridad: {row['Prioridad']})</em>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.info("No hay actividades registradas para el día de hoy")

st.markdown("----")

# CALENDARIO COMPLETO Y LISTA MENSUAL
st.header("🗓️ Vista General 🗓️")

tab1, tab2 = st.tabs(["📋 Todas las Actividades", "📆 Filtrar por Mes/Persona"])

with tab1:
    if not df_actividades.empty:
        # Formatear la fecha para visualizar en tabla de forma limpia
        df_ordenado = df_actividades.sort_values(by="Fecha", ascending=True).copy()
        df_ordenado["Fecha"] = df_ordenado["Fecha"].dt.strftime("%Y-%m-%d")
        st.dataframe(df_ordenado, use_container_width=True)
    else:
        st.write("Aún no se han agregado actividades")

with tab2:
    col_filtro1, col_filtro2 = st.columns(2)

    with col_filtro1:
        persona_filtro = st.multiselect("Filtrar por Persona: ", options=list(COLORES_PERSONAS.keys()), default=list(COLORES_PERSONAS.keys()))

    with col_filtro2:
        mes_filtro = st.slider("Seleccionar Mes: ", 1, 12, hoy.month)

    # FILTRADO DE DATOS
    if not df_actividades.empty:
        df_filtrado = df_actividades[
            (df_actividades["Persona"].isin(persona_filtro)) &
            (df_actividades["Fecha"].dt.month == mes_filtro)
        ].copy()
        
        if not df_filtrado.empty:
            df_filtrado["Fecha"] = df_filtrado["Fecha"].dt.strftime("%Y-%m-%d")
            st.write(f"Resultados para el mes **{mes_filtro}**:")
            st.dataframe(df_filtrado, use_container_width=True)
        else:
            st.write("No se encontraron registros con los filtros seleccionados.")
