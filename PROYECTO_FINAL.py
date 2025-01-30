import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import streamlit as st

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("moviescreds.json")  
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Función para cargar datos de Firestore (Solo si no están en caché)
@st.cache_data
def load_data(collection_name):
    try:
        docs = db.collection(collection_name).stream()
        data = [{**doc.to_dict(), 'id': doc.id} for doc in docs]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

# Cargar datos solo una vez y almacenarlo en session_state
if "df" not in st.session_state:
    st.session_state.df = load_data("netflix")

df = st.session_state.df  # Usar df desde session_state

st.title("Dashboard de Filmes")

# Mostrar todos los filmes
show_films = st.sidebar.checkbox("Mostrar todos los filmes", value=True)
if show_films:
    st.header("Lista de Filmes")
    st.dataframe(df)
else:
    st.info("Selecciona el checkbox para mostrar la lista de filmes.")

# Buscar por nombre
search_name = st.sidebar.text_input("Buscar por nombre:")
if st.sidebar.button("Buscar Nombre"):
    if search_name:
        filtered_df = df[df['name'].str.contains(search_name, case=False, na=False)]
        st.write(f"Se encontraron {len(filtered_df)} filmes.")
        st.dataframe(filtered_df)
    else:
        st.info("Escribe un nombre para buscar.")

# Filtrar por director
if "director" in df.columns:  # Evitar error si la columna no existe
    directors = df['director'].dropna().unique().tolist()
    selected_director = st.sidebar.selectbox("Selecciona un director", [""] + directors)  # Agregar opción vacía
    if st.sidebar.button("Filtrar por Director") and selected_director:
        filtered_by_director = df[df['director'] == selected_director]
        st.write(f"Se encontraron {len(filtered_by_director)} filmes dirigidos por {selected_director}.")
        st.dataframe(filtered_by_director)

# Formulario de inserción
with st.sidebar.form("insert_film_form"):
    st.header("Insertar un nuevo filme")
    new_name = st.text_input("Nombre:")
    new_genre = st.text_input("Género:")
    new_director = st.text_input("Director:")
    new_company = st.text_input("Compañía:")
    
    submit_button = st.form_submit_button("Insertar Filme")

    if submit_button:
        if new_name and new_genre and new_director and new_company:
            if df[df['name'].str.contains(new_name, case=False, na=False)].empty:
                # Insertar en Firebase y actualizar df localmente
                new_film = {'name': new_name, 'genre': new_genre, 'director': new_director, 'company': new_company}
                db.collection('netflix').add(new_film)

                # Actualizar DataFrame localmente sin recargar Firestore
                new_film["id"] = "temp_id"  # Evitar errores con Firestore
                st.session_state.df = pd.concat([df, pd.DataFrame([new_film])], ignore_index=True)

                st.success(f"¡El filme '{new_name}' ha sido insertado exitosamente!")
            else:
                st.warning(f"El filme '{new_name}' ya existe en la base de datos.")
        else:
            st.error("Por favor completa todos los campos del formulario.")