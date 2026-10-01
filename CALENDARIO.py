import streamlit as st
import pandas as pd
import gspread
import datetime


#AUTENTIFICACIÓN DATOS GUARDADOS EN SECRETS.TOML
@st.cache_data(ttl=60) #RECARGA DATOS CADA 60 SEG
def cargar_datos_sheets():
    #OBTENER CREDENCIALES
    credentials = dict(st.secrets["gcp_service_account"])

    #AUTENTIFICAR GSPREAD
    gc = gspread.service_account_from_dict(credentials)

    #ABRIR HOJA DE CÁLCULO
    sh = gc.open("Calendario_Compartido")

    #SELECCIONAR 1° HOJA
    worksheet = sh.get_worksheet(0)

    #CONVERTIR DATOS A PANDAS
    datos = worksheet.get_all_records()
    df = pd.DataFrame(datos)

    return df

#CARGAR LOS DATOS
df_actividades = cargar_datos_sheets()


#CONFIGURACIÓN PÁGINA
st.set_page_config(page_title ="Calendario Compartido", layout = "wide")

st.title("📅 Calendario Compartido Alexos 📅")

#MOSTRAR DATOS
st.dataframe(df_actividades, use_container_width=True)

#INICIAR BASE DE DATOS QUE SE MANTIENE EN MEMORIA
if "actividades" not in st.session_state:
    st.session_state.actividades = pd.DataFrame(
        columns=["Fecha", "Actividad", "Persona", "Prioridad"]
    )

#COLORES ASIGNADOS PARA CADA UNO
COLORES_PERSONAS = {
    "Alex" : "#87CEEB",
    "Alexa" : "#E4007C",
}

#BARRA AGREGAR ACTIVIDAD
st.sidebar.header("➕ Agregar nueva actividad")

persona = st.sidebar.selectbox("¿Quién la agrega?", list(COLORES_PERSONAS.keys()))
actividad = st.sidebar.text_input("Descripción de la actividad")
fecha = st.sidebar.date_input("Fecha de la actividad", value = datetime.date.today())
prioridad = st.sidebar.selectbox("Prioridad", ["Baja", "Media", "Alta"])

if st.sidebar.button("Guardar Actividad"):
    if actividad.strip():
        nueva_fila = pd.DataFrame([{
            "Fecha": fecha,
            "Actividad": actividad,
            "Persona": persona,
            "Prioridad": prioridad
        }])
        st.session_state.actividades = pd.concat([st.session_state.actividades, nueva_fila], ignore_index=True)
        st.sidebar.success("¡Actividad Guardada")
    else:
        st.sidebar.error("Porfavor, ingresa una descripción")

#VISTA DEL DÍA ACTUAL
st.header(f"☀️ Tareas de Hoy ({datetime.date.today().strftime('%d/%m/%Y')})")

hoy = datetime.date.today()
df_actividades = st.session_state.actividades

#FILTRADO DE FECHA DE HOY
df_hoy = df_actividades[df_actividades["Fecha"] == hoy]

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

#CALENDARIO COMPLETO Y LISTA MENSUAL
st.header("🗓️ Vista General 🗓️")

tab1, tab2 = st.tabs(["📋 Todas las Actividades", "📆 Filtrar por Mes/Persona"])

with tab1:
    if not df_actividades.empty:
        #ORDENAR POR FECHA
        df_ordenado = df_actividades.sort_value(by="Fecha")
        st.dataframe(df_ordenado, use_container_width=True)
    else:
        st.write("Aún no se han agregado actividades")

with tab2:
    col_filtro1, col_filtro2 = st.columns(2)

    with col_filtro1:
        persona_filtro = st.multiselect("Filtrar por Persona: ", options = list(COLORES_PERSONAS.keys()), default = list(COLORES_PERSONAS.keys()))

    with col_filtro2:
        mes_filtro = st.slider("Seleccionar Mes: ", 1, 12, hoy.month)

    #FILTRADO DE DATOS
    if not df_actividades.empty:
        df_actividades["Fecha"] = pd.to_datetime(df_actividades["Fecha"])
        df_filtrado = df_actividades[
            (df_actividades["Persona"].isin(persona_filtro)) &
            (df_actividades["Fecha"].dt.month == mes_filtro)
        ]
        st.write(f"Resultados para el mes **{mes_filtro}**:")
        st.dataframe(df_filtrado, use_container_width=True)











