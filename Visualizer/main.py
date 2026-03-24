import streamlit as st
import redis
import os
import pandas as pd

token = os.getenv("GITHUB_TOKEN")
REDIS_HOST = os.getenv("REDIS_HOST", "redis") 
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

st.set_page_config(page_title="GitHub Miner", layout="wide")
st.title("📊 GitHub Word Miner - Real Time")

st.sidebar.header("Configuración y Control")

current_status = r.get("miner_status") or "running"

if current_status == "running":
    if st.sidebar.button("🛑 Detener Actividad del Miner", use_container_width=True):
        r.set("miner_status", "stopped")
        st.rerun()
else:
    if st.sidebar.button("▶️ Reanudar Actividad del Miner", use_container_width=True, type="primary"):
        r.set("miner_status", "running")
        st.rerun()

status_color = "green" if current_status == "running" else "red"
st.sidebar.markdown(f"Estado del Miner: :{status_color}[{current_status.upper()}]")

top_n = st.sidebar.slider("Ver Top N palabras", 5, 50, 10)
refresh_rate = st.sidebar.selectbox("Refresco (segundos)", [2, 5, 10], index=0)

data = r.zrevrange("word_ranking", 0, top_n - 1, withscores=True)

if data:
    df = pd.DataFrame(data, columns=["Palabra", "Frecuencia"])
    st.subheader(f"Top {top_n} palabras encontradas")
    st.bar_chart(df.set_index("Palabra"))
    st.table(df)
else:
    st.info("Esperando datos del Miner... Asegúrate de que el contenedor 'miner' esté corriendo.")

st.fragment(run_every=refresh_rate)(lambda: st.rerun())()