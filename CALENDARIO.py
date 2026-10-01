import datetime
import gspread
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Calendario Compartido", layout="wide")


# 2. CONEXIÓN A GOOGLE SHEETS
def obtener_worksheet():
  credentials = dict(st.secrets["gcp_service_account"])
  gc = gspread.service_account_from_dict(credentials)
  sh = gc.open("Calendario_Compartido")
  return sh.get_worksheet(0)


# 3. CARGAR DATOS
@st.cache_data(ttl=5)
def cargar_datos_sheets():
  worksheet = obtener_worksheet()
  datos = worksheet.get_all_records()
  df = pd.DataFrame(datos)

  if not df.empty:
    df.columns = [col.capitalize() for col in df.columns]

    if "Estado" not in df.columns:
      df["Estado"] = "Pendiente"

    if "Hora" not in df.columns:
      df["Hora"] = "All-day"

    if "Fecha" in df.columns:
      df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

  return df


# 4. GUARDAR NUEVA ACTIVIDAD CON SOPORTE ALL-DAY
def guardar_en_sheets(fecha, hora_str, actividad, persona, prioridad):
  worksheet = obtener_worksheet()
  fecha_str = fecha.strftime("%Y-%m-%d")
  worksheet.append_row(
      [fecha_str, actividad, persona, prioridad, "Pendiente", hora_str]
  )


# 5. CAMBIAR ESTADO
def cambiar_estado_en_sheets(index_fila_df, nuevo_estado):
  worksheet = obtener_worksheet()
  num_fila_sheets = index_fila_df + 2
  worksheet.update_cell(num_fila_sheets, 5, nuevo_estado)


# 6. CARGAR DATOS
df_actividades = cargar_datos_sheets()

st.title("📅 Calendario Compartido Alexos 📅")

# COLORES ASIGNADOS
COLORES_PERSONAS = {
    "Alex": "#3498db",  # Azul
    "Alexa": "#e91e63",  # Rosa
}
COLOR_COMPLETADO = "#2ecc71"  # Verde brillante

# 7. BARRA LATERAL: FORMULARIO MEJORADO
st.sidebar.header("➕ Agregar nueva actividad")

persona = st.sidebar.selectbox("¿Quién la agrega?", list(COLORES_PERSONAS.keys()))
actividad = st.sidebar.text_input("Descripción de la actividad")
fecha = st.sidebar.date_input("Fecha de la actividad", value=datetime.date.today())

# Casilla para definir si es de todo el día
todo_el_dia = st.sidebar.checkbox("📌 Evento de todo el día", value=True)

if not todo_el_dia:
  hora_input = st.sidebar.time_input(
      "Hora de la actividad", value=datetime.time(9, 0)
  )
  hora_guardar = hora_input.strftime("%H:%M")
else:
  hora_guardar = "All-day"

prioridad = st.sidebar.selectbox("Prioridad", ["Baja", "Media", "Alta"])

if st.sidebar.button("Guardar Actividad"):
  if actividad.strip():
    try:
      guardar_en_sheets(fecha, hora_guardar, actividad, persona, prioridad)
      st.cache_data.clear()
      st.sidebar.success("¡Actividad Guardada!")
      st.rerun()
    except Exception as e:
      st.sidebar.error(f"Error al guardar: {e}")
  else:
    st.sidebar.error("Por favor, ingresa una descripción")

# 8. VISTA DEL DÍA ACTUAL
hoy = datetime.date.today()
st.header(f"☀️ Tareas de Hoy ({hoy.strftime('%d-%m-%Y')})")

if not df_actividades.empty and "Fecha" in df_actividades.columns:
  df_hoy = df_actividades[df_actividades["Fecha"].dt.date == hoy]
else:
  df_hoy = pd.DataFrame()

if not df_hoy.empty:
  for idx, row in df_hoy.iterrows():
    es_completada = row.get("Estado") == "Completada"
    color = (
        COLOR_COMPLETADO
        if es_completada
        else COLORES_PERSONAS.get(row["Persona"], "#888888")
    )
    texto_estado = " (COMPLETADA)" if es_completada else ""
    hora_evento = str(row.get("Hora", "All-day"))

    col1, col2 = st.columns([5, 1])
    with col1:
      st.markdown(
          f"""
                <div style="background-color: {color}22; border-left: 6px solid {color}; padding: 10px; border-radius: 5px; margin-bottom: 8px;">
                    <strong>🕒 {hora_evento} | 👤 {row['Persona']}</strong> — {row['Actividad']} <em>(Prioridad: {row['Prioridad']})</em> <strong>{texto_estado}</strong>
                </div>
                """,
          unsafe_allow_html=True,
      )
    with col2:
      if not es_completada:
        if st.button("✅ Marcar Lista", key=f"btn_hoy_{idx}"):
          cambiar_estado_en_sheets(idx, "Completada")
          st.cache_data.clear()
          st.success("¡Tarea marcada como completada!")
          st.rerun()
      else:
        st.write("🎉 Lista")
else:
  st.info("No hay actividades registradas para el día de hoy")

st.markdown("----")

# 9. SECCIÓN CALENDARIO Y GESTIÓN CON SOPORTE ALL-DAY
st.header("🗓️ Calendario Mensual y Gestión 🗓️")

tab1, tab2 = st.tabs(
    ["📅 Vista Calendario (iOS Style)", "📋 Lista de Tareas y Gestión"]
)

with tab1:
  if not df_actividades.empty and "Fecha" in df_actividades.columns:
    eventos = []
    for idx, row in df_actividades.iterrows():
      if pd.notnull(row["Fecha"]):
        fecha_str = row["Fecha"].strftime("%Y-%m-%d")
        hora_val = str(row.get("Hora", "All-day"))

        es_completada = row.get("Estado") == "Completada"
        color_evento = (
            COLOR_COMPLETADO
            if es_completada
            else COLORES_PERSONAS.get(row["Persona"], "#3788d8")
        )
        titulo_evento = (
            f"✅ [{row['Persona']}] {row['Actividad']}"
            if es_completada
            else f"[{row['Persona']}] {row['Actividad']}"
        )

        # Lógica para All-day vs Hora específica
        if hora_val == "All-day" or hora_val == "":
          is_all_day = True
          start_val = fecha_str
        else:
          is_all_day = False
          start_val = f"{fecha_str}T{hora_val}:00"

        eventos.append({
            "id": str(idx),
            "title": titulo_evento,
            "start": start_val,
            "end": start_val,
            "color": color_evento,
            "allDay": is_all_day,
        })

    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek",
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "editable": False,
        "slotMinTime": "06:00:00",
        "slotMaxTime": "23:00:00",
    }

    calendar(events=eventos, options=calendar_options, key="apple_calendar")
  else:
    st.write("Aún no hay actividades para mostrar en el calendario.")

with tab2:
  if not df_actividades.empty:
    df_ordenado = df_actividades.sort_values(by="Fecha", ascending=True)

    col_f, col_h, col_a, col_p, col_pr, col_est, col_acc = st.columns(
        [2, 1, 3, 2, 2, 2, 2]
    )
    col_f.markdown("**Fecha**")
    col_h.markdown("**Hora**")
    col_a.markdown("**Actividad**")
    col_p.markdown("**Persona**")
    col_pr.markdown("**Prioridad**")
    col_est.markdown("**Estado**")
    col_acc.markdown("**Acción**")
    st.markdown("---")

    for idx, row in df_ordenado.iterrows():
      c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1, 3, 2, 2, 2, 2])

      # FORMATO: DD-MM-AAAA
      fecha_str = (
          row["Fecha"].strftime("%d-%m-%Y")
          if pd.notnull(row["Fecha"])
          else "Sin Fecha"
      )
      hora_str = str(row.get("Hora", "All-day"))
      estado_actual = row.get("Estado", "Pendiente")

      c1.write(fecha_str)
      c2.write(hora_str)
      c3.write(row["Actividad"])
      c4.write(row["Persona"])
      c5.write(row["Prioridad"])
      c6.write(
          f"🟢 {estado_actual}"
          if estado_actual == "Completada"
          else f"🟡 {estado_actual}"
      )

      if estado_actual != "Completada":
        if c7.button("✅ Marcar Lista", key=f"btn_completar_{idx}"):
          cambiar_estado_en_sheets(idx, "Completada")
          st.cache_data.clear()
          st.success(f"¡'{row['Actividad']}' completada!")
          st.rerun()
      else:
        c7.write("✔️ Finalizada")
  else:
    st.write("Aún no se han agregado actividades")
