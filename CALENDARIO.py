import streamlit as st
import pandas as pd
import gspread
import datetime
from streamlit_calendar import calendar

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Calendario Compartido", layout="wide")

# CONEXIÓN A GOOGLE SHEETS
def obtener_worksheet():
    credentials = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Calendario_Compartido")
    return sh.get_worksheet(0)

# CARGAR DATOS
@st.cache_data(ttl=5)
def cargar_datos_sheets():
    worksheet = obtener_worksheet()
    datos = worksheet.get_all_records()
    df = pd.DataFrame(datos)
    
    if not df.empty:
        df.columns = [col.capitalize() for col in df.columns]
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df

# GUARDAR ACTIVIDAD
def guardar_en_sheets(fecha, actividad, persona, prioridad):
    worksheet = obtener_worksheet()
    fecha_str = fecha.strftime("%Y-%m-%d")
    worksheet.append_row([fecha_str, actividad, persona, prioridad])

# ELIMINAR ACTIVIDAD
def eliminar_de_sheets(index_fila_df):
    worksheet = obtener_worksheet()
    num_fila_sheets = index_fila_df + 2
    worksheet.delete_rows(num_fila_sheets)

# CARGAR DATOS EN MEMORIA
df_actividades = cargar_datos_sheets()

st.title("📅 Calendario Compartido Alexos 📅")

# COLORES ASIGNADOS PARA CADA PERSONA (Estilo Apple Calendar)
COLORES_PERSONAS = {
    "Alex": "#3498db",   # Azul
    "Alexa": "#e91e63",  # Rosa / Magenta
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
            guardar_en_sheets(fecha, actividad, persona, prioridad)
            st.cache_data.clear()
            st.sidebar.success("¡Actividad Guardada!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error al guardar: {e}")
    else:
        st.sidebar.error("Por favor, ingresa una descripción")

# VISTA DEL DÍA ACTUAL
hoy = datetime.date.today()
st.header(f"☀️ Tareas de Hoy ({hoy.strftime('%d/%m/%Y')})")

if not df_actividades.empty and "Fecha" in df_actividades.columns:
    df_hoy = df_actividades[df_actividades["Fecha"].dt.date == hoy]
else:
    df_hoy = pd.DataFrame()

if not df_hoy.empty:
    for idx, row in df_hoy.iterrows():
        color = COLORES_PERSONAS.get(row["Persona"], "#888888")
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"""
                <div style="background-color: {color}22; border-left: 6px solid {color}; padding: 10px; border-radius: 5px; margin-bottom: 8px;">
                    <strong>👤 {row['Persona']}</strong> — {row['Actividad']} <em>(Prioridad: {row['Prioridad']})</em>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            if st.button("✅ Finalizar", key=f"btn_hoy_{idx}"):
                eliminar_de_sheets(idx)
                st.cache_data.clear()
                st.success("¡Tarea completada!")
                st.rerun()
else:
    st.info("No hay actividades registradas para el día de hoy")

st.markdown("----")

# SECCIÓN DE CALENDARIO VISUAL Y LISTA
st.header("🗓️ Calendario Mensual y Gestión 🗓️")

tab1, tab2 = st.tabs(["📅 Vista Calendario (iOS Style)", "📋 Lista de Tareas y Eliminación"])

with tab1:
    if not df_actividades.empty and "Fecha" in df_actividades.columns:
        # Preparar los eventos en el formato requerido por FullCalendar / streamlit-calendar
        eventos = []
        for idx, row in df_actividades.iterrows():
            if pd.notnull(row["Fecha"]):
                fecha_str = row["Fecha"].strftime("%Y-%m-%d")
                color = COLORES_PERSONAS.get(row["Persona"], "#3788d8")
                
                eventos.append({
                    "id": str(idx),
                    "title": f"[{row['Persona']}] {row['Actividad']}",
                    "start": fecha_str,
                    "end": fecha_str,
                    "color": color,
                    "allDay": True
                })

        # Opciones visuales del calendario
        calendar_options = {
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek"
            },
            "initialView": "dayGridMonth",
            "selectable": True,
            "editable": False,
        }

        # Renderizar el widget interactivo
        state = calendar(events=eventos, options=calendar_options, key="apple_calendar")
    else:
        st.write("Aún no hay actividades para mostrar en el calendario.")

with tab2:
    if not df_actividades.empty:
        df_ordenado = df_actividades.sort_values(by="Fecha", ascending=True)
        
        col_f, col_a, col_p, col_pr, col_acc = st.columns([2, 4, 2, 2, 2])
        col_f.markdown("**Fecha**")
        col_a.markdown("**Actividad**")
        col_p.markdown("**Persona**")
        col_pr.markdown("**Prioridad**")
        col_acc.markdown("**Acción**")
        st.markdown("---")

        for idx, row in df_ordenado.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2, 4, 2, 2, 2])
            fecha_str = row["Fecha"].strftime("%Y-%m-%d") if pd.notnull(row["Fecha"]) else "Sin Fecha"
            
            c1.write(fecha_str)
            c2.write(row["Actividad"])
            c3.write(row["Persona"])
            c4.write(row["Prioridad"])
            
            if c5.button("✅ Marcar Lista", key=f"btn_completar_{idx}"):
                eliminar_de_sheets(idx)
                st.cache_data.clear()
                st.success(f"¡'{row['Actividad']}' completada!")
                st.rerun()
    else:
        st.write("Aún no se han agregado actividades")
