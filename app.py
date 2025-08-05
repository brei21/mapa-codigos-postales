# app.py ────────────────────────────────────────────────────────────
import streamlit as st
import pgeocode
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html as st_html
from collections import Counter

# ───────────────────────── Configuración ───────────────────────────
st.set_page_config(page_title="Mapa de Códigos Postales", layout="wide")
st.title("📍 Mapeador de Códigos Postales (España)")

# ───────────────────────── Sidebar ─────────────────────────────────
with st.sidebar:
    st.header("🎛️  Opciones de mapa")
    tiles = st.selectbox(
        "Estilo base",
        {
            "CartoDB Positron":   "CartoDB positron",
            "CartoDB DarkMatter": "CartoDB dark_matter",
            "OpenStreetMap":      "OpenStreetMap",
            "Stamen Toner":       "Stamen Toner",
        },
    )
    start_zoom = st.slider("Zoom inicial", 3, 10, 6)
    map_height = st.slider("Alto del mapa (px)", 300, 900, 600)

# ───────────────────────── Formulario ──────────────────────────────
with st.form("postcode_form", clear_on_submit=False):
    codes_input = st.text_area(
        "Introduce códigos postales separados por comas, espacios o saltos de línea:",
        height=120,
        placeholder="28001, 08001, 50006…",
    )
    submitted = st.form_submit_button("🗺️ Mostrar mapa")

# ───────────────────────── Helper mapa ─────────────────────────────
def build_map(df_unique, zoom, tiles):
    m = folium.Map(
        location=[df_unique["latitude"].mean(), df_unique["longitude"].mean()],
        zoom_start=zoom,
        tiles=tiles,
    )
    target = MarkerCluster().add_to(m) if len(df_unique) >= 10 else m
    for _, row in df_unique.iterrows():
        folium.Marker(
            location=[float(row.latitude), float(row.longitude)],
            popup=row.postal_code,
            icon=folium.Icon(color="red", icon="map-marker"),
        ).add_to(target)
    return m

# ───────────────────────── Al pulsar botón ─────────────────────────
if submitted:
    raw = [c.strip() for c in codes_input.replace(",", " ").split()]
    try:
        postcodes = [f"{int(c):05d}" for c in raw if c]  # mantiene duplicados
    except ValueError:
        st.error("⚠️ Todos los códigos deben ser numéricos (5 dígitos).")
        st.stop()
    if not postcodes:
        st.warning("Introduce al menos un código postal.")
        st.stop()

    freq = Counter(postcodes)                 # {'28027': 3, '08001': 1, ...}
    codes_unique = list(freq.keys())

    nomi = pgeocode.Nominatim("es")
    df_geo = nomi.query_postal_code(codes_unique)[
        ["postal_code", "latitude", "longitude", "place_name"]
    ].dropna(subset=["latitude", "longitude"])

    if df_geo.empty:
        st.error("❌ Ninguno de los códigos parece válido en España.")
        st.stop()

    # Tabla resumen
    summary = (
        pd.DataFrame({"postal_code": list(freq.keys()), "Veces": list(freq.values())})
        .merge(df_geo[["postal_code", "place_name"]], on="postal_code", how="left")
        .rename(columns={"postal_code": "Código postal", "place_name": "Localidad"})
        .sort_values("Veces", ascending=False)
    )

    # GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df_geo,
        geometry=gpd.points_from_xy(df_geo.longitude, df_geo.latitude),
        crs="EPSG:4326",
    )

    # Guardar en session_state
    m = build_map(gdf, start_zoom, tiles)
    st.session_state["map_html"]    = m.get_root().render()
    st.session_state["height"]      = map_height
    st.session_state["summary_df"]  = summary

    # ---------- Generar HTML estilizado para la tabla -------------
    header_props = [("background-color", "#f0f2f6"),
                    ("color", "black"),
                    ("font-weight", "bold"),
                    ("border-bottom", "1px solid #d0d0d0")]

    cell_props   = [("border-bottom", "1px solid #e6e6e6")]

    alternating  = {"selector": "tbody tr:nth-child(even)",
                    "props": [("background-color", "#fafbfc")]}

    styler = (
        summary.style
        .hide(axis="index")                           # sin índice
        .set_table_styles(
            [{"selector": "th", "props": header_props},
             {"selector": "td", "props": cell_props},
             alternating]
        )
        .set_properties(**{"text-align": "left", "padding": "6px 8px"})
    )

    st.session_state["summary_html"] = styler.to_html()

# ───────────────────────── Mostrar mapa + tabla ────────────────────
if "map_html" in st.session_state:
    st_html(
        st.session_state["map_html"],
        height=int(st.session_state["height"]),
        width=None,
        scrolling=False,
    )

    st.download_button(
        "💾 Descargar mapa HTML",
        data=st.session_state["map_html"].encode("utf-8"),
        file_name="mapa_postales.html",
        mime="text/html",
    )

    st.subheader("📋 Detalle de códigos mapeados")
    st.dataframe(
        st.session_state["summary_df"],
        hide_index=True,
    )

    st.download_button(
        "💾 Descargar tabla HTML",
        data=st.session_state["summary_html"].encode("utf-8"),
        file_name="tabla_codigos_postales.html",
        mime="text/html",
    )

    total = int(st.session_state["summary_df"]["Veces"].sum())
    st.success(f"Se han mapeado {total} códigos postales.")
