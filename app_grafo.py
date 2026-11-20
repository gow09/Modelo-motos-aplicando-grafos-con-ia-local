import streamlit as st
import json
import ollama
from streamlit_agraph import agraph, Node, Edge, Config

# -------------------------------------------------------------
# Configuración de la Página
# -------------------------------------------------------------
st.set_page_config(page_title="Sistema Experto Mecánico", layout="wide")

st.markdown("""
<style>
    .main-title { font-family: 'Segoe UI', sans-serif; font-size: 2.2rem; font-weight: 700; color: #1E293B; border-bottom: 3px solid #EF4444; padding-bottom: 8px; margin-bottom: 20px; }
    .node-title { background-color: #F8FAFC; padding: 15px; border-radius: 8px; border-left: 5px solid #3B82F6; margin-bottom: 15px; }
    .diagnostico-box { background-color: #F0FDF4; padding: 20px; border-radius: 8px; border: 1px solid #BBF7D0; margin-top: 15px; white-space: pre-wrap; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { border-radius: 6px; font-weight: 600; background-color: #F1F5F9; color: #1E293B; border: 1px solid #CBD5E1; }
    .stButton>button:hover { background-color: #E2E8F0; }
    .prompt-box { background-color: #F8FAFC; padding: 10px; border-radius: 6px; border: 1px solid #CBD5E1; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Cargar Datos del Grafo
# -------------------------------------------------------------
@st.cache_data
def cargar_grafo():
    try:
        with open("grafo_moto.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Error: No se encontró 'grafo_moto.json'.")
        return None

data_grafo = cargar_grafo()

# -------------------------------------------------------------
# Hojas por componente (síntomas del árbol original)
# -------------------------------------------------------------
HOJAS_POR_COMPONENTE = {
    "nivel_aceite": ["Nivel correcto (entre MIN y MAX)", "Nivel bajo", "Nivel alto", "Aceite sucio o negro", "Fuga de aceite visible"],
    "lubricacion_cadena": ["Cadena limpia y lubricada", "Cadena seca", "Cadena oxidada", "Cadena con exceso de grasa"],
    "aceite_horquilla": ["Sin fugas", "Fuga leve", "Fuga abundante", "Horquilla muy blanda"],
    "presion_llantas": ["Presión correcta (según manual)", "Presión baja", "Presión alta", "No sabe la presión correcta"],
    "llanta_delantera": ["Dibujo en buen estado", "Dibujo desgastado", "Grietas o cuarteaduras", "Llanta ponchada", "Llanta con objeto incrustado"],
    "llanta_trasera": ["Dibujo en buen estado", "Dibujo desgastado", "Grietas o cuarteaduras", "Llanta ponchada", "Llanta con objeto incrustado"],
    "frenos_delanteros": ["Pastillas en buen estado", "Pastillas desgastadas", "Disco rayado", "Líquido de frenos bajo", "Fuga de líquido de frenos", "Freno esponjoso"],
    "frenos_traseros": ["Pastillas o tambor en buen estado", "Pastillas desgastadas", "Tambor rayado", "Líquido de frenos bajo", "Fuga de líquido de frenos", "Freno esponjoso"],
    "luces_delanteras": ["Luz baja funciona", "Luz alta funciona", "Luz baja no funciona", "Luz alta no funciona", "Luz parpadea"],
    "luces_traseras": ["Luz de posición funciona", "Luz de freno funciona", "Luz de posición no funciona", "Luz de freno no funciona", "Luz parpadea"],
    "direccionales": ["Ambos funcionan", "Izquierdo no funciona", "Derecho no funciona", "Parpadean muy rápido", "No parpadean"],
    "bateria": ["Voltaje correcto (12.4V - 12.8V)", "Voltaje bajo (menos de 12V)", "Terminales sulfatados", "Batería no retiene carga", "Batería hinchada"],
    "sistema_carga": ["Carga correcta (13.5V - 14.5V)", "No carga", "Sobrevoltaje (más de 15V)", "Ruido en el alternador", "Luz de batería encendida"],
    "bujia": ["Bujía limpia y en buen estado", "Bujía negra (mezcla rica)", "Bujía blanca (mezcla pobre)", "Bujía desgastada", "Bujía con aceite"],
    "filtro_aire": ["Filtro limpio", "Filtro sucio", "Filtro obstruido", "Filtro roto"],
    "cadena_correa": ["Tensión correcta", "Cadena floja", "Cadena muy tensa", "Correa desgastada", "Cadena o correa rota"],
    "embrague": ["Funciona suave y sin ruido", "Embrague patina", "Embrague duro", "Ruido al accionar", "No desengancha"],
    "cambios_marcha": ["Cambios suaves y precisos", "Cambios duros", "Se sale la marcha", "No engrana una marcha", "Ruido al cambiar"],
    "refrigeracion": ["Nivel de refrigerante correcto", "Refrigerante bajo", "Fuga de refrigerante", "Ventilador no enciende", "Motor se sobrecalienta"],
    "susp_delantera": ["Horquilla sin fugas", "Fuga de aceite en horquilla", "Suspensión muy blanda", "Suspensión muy dura", "Ruido al pasar baches"],
    "susp_trasera": ["Amortiguador en buen estado", "Amortiguador con fuga", "Rebote excesivo", "Ruido al pasar baches"],
    "direccion": ["Dirección suave y precisa", "Dirección dura", "Juego en el manubrio", "Vibración en el manubrio", "Ruido al girar"],
    "rodamientos": ["Ruedas giran suave", "Ruido al girar la rueda", "Juego en la rueda", "Vibración a alta velocidad"],
    "estado_escape": ["Escape en buen estado", "Escape con fuga", "Ruido excesivo", "Óxido perforado"],
    "humo_escape": ["Sin humo visible", "Humo blanco", "Humo azul", "Humo negro"],
    "olor_escape": ["Olor normal", "Olor a gasolina", "Olor a aceite quemado", "Olor dulce (refrigerante)"]
}

# -------------------------------------------------------------
# Configuración del Modelo (Fijo)
# -------------------------------------------------------------
MODELO_NOMBRE = "mecanico-moto-3b"

# -------------------------------------------------------------
# Estado de la Sesión
# -------------------------------------------------------------
if "nodo_actual" not in st.session_state:
    st.session_state.nodo_actual = "raiz"
if "canasta" not in st.session_state:
    st.session_state.canasta = []
if "diagnostico" not in st.session_state:
    st.session_state.diagnostico = None
if "prompt_enviado" not in st.session_state:
    st.session_state.prompt_enviado = ""

# -------------------------------------------------------------
# Barra Lateral
# -------------------------------------------------------------
with st.sidebar:
    st.title("Panel de Control")
    st.markdown(f"**Modelo activo:** `{MODELO_NOMBRE}`")
    st.caption("Modelo especializado con contexto técnico de motos en Colombia.")
    
    st.markdown("---")
    st.markdown("### Canasta de Síntomas")
    if st.session_state.canasta:
        for i, (comp, sintoma) in enumerate(st.session_state.canasta):
            st.write(f"{i+1}. {comp}: {sintoma}")
    else:
        st.info("Aún no has seleccionado síntomas.")
    
    if st.button("Vaciar Canasta", use_container_width=True):
        st.session_state.canasta = []
        st.session_state.diagnostico = None
        st.session_state.prompt_enviado = ""
        st.rerun()
    
    st.markdown("---")
    if st.button("Reiniciar Sistema", use_container_width=True):
        st.session_state.nodo_actual = "raiz"
        st.session_state.canasta = []
        st.session_state.diagnostico = None
        st.session_state.prompt_enviado = ""
        st.rerun()

# -------------------------------------------------------------
# Cabecera Principal
# -------------------------------------------------------------
st.markdown('<div class="main-title">Sistema Experto: Diagnóstico de Motos</div>', unsafe_allow_html=True)

if not data_grafo:
    st.stop()

# -------------------------------------------------------------
# Grafo Visual
# -------------------------------------------------------------
nodos_visuales = []
aristas_visuales = []
colores = {"central": "#FEF3C7", "secundario": "#D1FAE5", "hoja": "#F3F4F6"}

for n in data_grafo["nodos"]:
    es_actual = (n["id"] == st.session_state.nodo_actual)
    color_borde = "#EF4444" if es_actual else "#9CA3AF"
    grosor = 4 if es_actual else 1
    nodos_visuales.append(Node(
        id=n["id"], label=n["label"], size=25, shape="box",
        color={"background": colores.get(n["grupo"], "#fff"), "border": color_borde},
        borderWidth=grosor,
        font={"size": 12, "face": "Arial", "color": "#1f2937", "bold": es_actual}
    ))

for a in data_grafo["aristas"]:
    aristas_visuales.append(Edge(source=a["origen"], target=a["destino"], color="#9CA3AF", smooth=True))

config = Config(width="100%", height=500, directed=True, physics=True, hierarchical=False, nodeHighlightBehavior=True, highlightColor="#F7A7A6")
st.markdown("### Mapa de Conexiones")
agraph(nodes=nodos_visuales, edges=aristas_visuales, config=config)

st.divider()

# -------------------------------------------------------------
# Panel de Navegación e Información
# -------------------------------------------------------------
nodo_info = next((n for n in data_grafo["nodos"] if n["id"] == st.session_state.nodo_actual), None)

if nodo_info:
    st.markdown(f"""
    <div class="node-title">
        <h2 style="margin:0; color:#1E293B;">Ubicación: {nodo_info['label']}</h2>
    </div>
    """, unsafe_allow_html=True)

    vecinos_ids = set()
    for a in data_grafo["aristas"]:
        if a["origen"] == st.session_state.nodo_actual:
            vecinos_ids.add(a["destino"])
        elif a["destino"] == st.session_state.nodo_actual:
            vecinos_ids.add(a["origen"])
    
    st.markdown("#### Conexiones Disponibles")
    if vecinos_ids:
        cols = st.columns(min(len(vecinos_ids), 4))
        for i, vecino_id in enumerate(vecinos_ids):
            vecino_info = next((n for n in data_grafo["nodos"] if n["id"] == vecino_id), None)
            if vecino_info:
                col = cols[i % len(cols)]
                if col.button(f"Ir a {vecino_info['label']}", key=f"nav_{vecino_id}", use_container_width=True):
                    st.session_state.nodo_actual = vecino_id
                    st.rerun()
    else:
        st.info("Este es un nodo final.")

    if st.session_state.nodo_actual in HOJAS_POR_COMPONENTE:
        st.markdown("#### Selecciona el estado de este componente:")
        sintomas = HOJAS_POR_COMPONENTE[st.session_state.nodo_actual]
        seleccionados = []
        for sintoma in sintomas:
            if st.checkbox(sintoma, key=f"chk_{st.session_state.nodo_actual}_{sintoma}"):
                seleccionados.append(sintoma)
        
        if st.button("Agregar a la Canasta", use_container_width=True):
            for s in seleccionados:
                if (nodo_info['label'], s) not in st.session_state.canasta:
                    st.session_state.canasta.append((nodo_info['label'], s))
            st.success(f"Se agregaron {len(seleccionados)} síntomas a la canasta.")
            st.rerun()

    # -------------------------------------------------------------
    # Diagnóstico Completo con IA
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Diagnóstico Integral")
    
    if not st.session_state.canasta:
        st.info("Agrega al menos un síntoma a la canasta para generar un diagnóstico integral.")
    else:
        if st.button("Generar Diagnóstico Completo con IA", type="primary", use_container_width=True):
            with st.spinner("Consultando modelo especializado..."):
                sintomas_texto = "\n".join([f"- {comp}: {sintoma}" for comp, sintoma in st.session_state.canasta])
                
                prompt = (
                    f"Ruta: Revisión Preventiva de Moto para Viaje\n"
                    f"Síntomas seleccionados:\n{sintomas_texto}\n\n"
                    "Genera el diagnóstico final integrando todos los síntomas anteriores con el formato obligatorio."
                )
                
                st.session_state.prompt_enviado = prompt
                
                try:
                    mensajes = [{"role": "user", "content": prompt}]
                    
                    response = ollama.chat(
                        model=MODELO_NOMBRE,
                        messages=mensajes,
                        options={"temperature": 0.05}
                    )
                    
                    # Solo mostramos la respuesta del modelo, sin la explicación de uso
                    st.session_state.diagnostico = response['message']['content']
                except Exception as e:
                    st.error(f"Error al conectar con Ollama: {e}")
                    st.info("Asegúrate de que Ollama esté corriendo y el modelo descargado.")
        
        if st.session_state.diagnostico:
            st.markdown(f"""
            <div class="diagnostico-box">
                {st.session_state.diagnostico}
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.prompt_enviado:
            with st.expander("Ver prompt enviado al modelo"):
                st.markdown(f'<div class="prompt-box">{st.session_state.prompt_enviado}</div>', unsafe_allow_html=True)