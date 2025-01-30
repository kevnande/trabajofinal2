import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import streamlit as st

# Inicializar Firebase si no está ya iniciado
if not firebase_admin._apps:
    cred = credentials.Certificate("moviescreds.json")  
    firebase_admin.initialize_app(cred)

db = firestore.client()

@st.cache_data
def load_data(collection_name):
    """Carga los datos desde Firestore a un DataFrame de pandas."""
    try:
        docs = db.collection(collection_name).stream()
        data = [{**doc.to_dict(), 'id': doc.id} for doc in docs]
        return pd.DataFrame(data) if data else pd.DataFrame(columns=['name', 'genre', 'director', 'company'])
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

# Cargar datos desde Firestore
df = load_data("netflix")

st.title("Dashboard de Filmes")

# Mostrar la lista de filmes
show_films = st.sidebar.checkbox("Mostrar todos los filmes", value=True)
if show_films:
    st.header("Lista de Filmes")
    st.dataframe(df)
else:
    st.info("Selecciona el checkbox para mostrar la lista de filmes.")

# Búsqueda por nombre
search_name = st.sidebar.text_input("Buscar por nombre:")
if st.sidebar.button("Buscar Nombre"):
    if search_name:
        filtered_df = df[df['name'].str.contains(search_name, case=False, na=False)]
        st.write(f"Se encontraron {len(filtered_df)} filmes.")
        st.dataframe(filtered_df)
    else:
        st.info("Escribe un nombre para buscar.")

# Filtro por director
directors = df['director'].dropna().unique().tolist()
selected_director = st.sidebar.selectbox("Selecciona un director", [""] + directors)
if st.sidebar.button("Filtrar por Director"):
    if selected_director:
        filtered_by_director = df[df['director'] == selected_director]
        st.write(f"Se encontraron {len(filtered_by_director)} filmes dirigidos por {selected_director}.")
        st.dataframe(filtered_by_director)
    else:
        st.info("Selecciona un director para filtrar.")

# Formulario para insertar un nuevo filme
with st.sidebar.form("insert_film_form"):
    st.header("Insertar un nuevo filme")
    new_name = st.text_input("Nombre:")
    new_genre = st.text_input("Género:")
    new_director = st.text_input("Director:")
    new_company = st.text_input("Compañía:")

    submit_button = st.form_submit_button("Insertar Filme")

    if submit_button:
        if new_name and new_genre and new_director and new_company:
            # Verificar si el filme ya existe en Firestore
            existing_films = list(db.collection("netflix").where("name", "==", new_name).stream())

            if existing_films:
                st.warning(f"El filme '{new_name}' ya existe en la base de datos.")
            else:
                new_film = {
                    "name": new_name,
                    "genre": new_genre,
                    "director": new_director,
                    "company": new_company
                }
                db.collection("netflix").add(new_film)  # Agregar sin sobrescribir
                st.success(f"¡El filme '{new_name}' ha sido insertado exitosamente!")

                # Recargar datos después de insertar
                df = load_data("netflix")
        else:
            st.error("Por favor completa todos los campos del formulario.")
