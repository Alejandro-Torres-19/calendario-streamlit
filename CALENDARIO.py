import streamlit as st
import pandas as pd
import gspread
import datetime

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
        # Asegurar que los nombres de las columnas tengan la primera letra mayúscula
        df.columns = [col.capitalize() for col in df.columns]
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df

# GUARDAR ACTIVIDAD
def guardar_en_sheets(fecha, actividad, persona, prioridad):
    worksheet = obtener_worksheet()
    fecha_str = fecha.strftime("%Y-%m-%d")
    worksheet.append_row([fecha_str, actividad, persona, prioridad])

# ELIMINAR/COMPLETAR ACTIVIDAD POR ÍNDICE EN GOOGLE SHEETS
def eliminar_de_sheets(index_fila_df):
    worksheet = obtener_worksheet()
    # +2 porque gspread usa índice base 1 y la fila 1 son los encabezados
    num_fila_sheets = index_fila_df + 2
    worksheet.delete_rows(num_fila_sheets)

# CARGAR DATOS EN MEMORIA
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
        color = COLORES_PERSONAS.get(row["Persona"], "#CCCCCC")
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

# VISTA GENERAL Y GESTIÓN DE TAREAS
st.header("🗓️ Vista General y Gestión 🗓️")

tab1, tab2 = st.tabs(["📋 Lista con Opción de Completar", "📆 Filtrar por Mes/Persona"])

with tab1:
    if not df_actividades.empty:
        # Ordenar conservando el índice original para eliminar la fila correcta en Sheets
        df_ordenado = df_actividades.sort_values(by="Fecha", ascending=True)
        
        # Encabezado de la tabla de gestión
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

with tab2:
    col_filtro1, col_filtro2 = st.columns(2)

    with col_filtro1:
        persona_filtro = st.multiselect("Filtrar por Persona: ", options=list(COLORES_PERSONAS.keys()), default=list(COLORES_PERSONAS.keys()))

    with col_filtro2:
        mes_filtro = st.slider("Seleccionar Mes: ", 1, 12, hoy.month)

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
