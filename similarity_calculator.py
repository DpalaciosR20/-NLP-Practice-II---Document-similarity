# similarity_calculator.py (versión actualizada con tu normalización de spaCy)

import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

# --- NUEVO: INICIO DE CONFIGURACIÓN DE SPACY ---
# Importamos las librerías necesarias para tu normalización
import spacy
import re

print("Cargando modelo de spaCy (en_core_web_sm)...")
# Cargamos el modelo UNA SOLA VEZ cuando el script es importado.
# Esto es mucho más eficiente que cargarlo en cada búsqueda.
nlp = spacy.load("en_core_web_sm")

# Replicamos tu personalización del tokenizador para conservar guiones
infix_re = re.compile(r'''[.\,\?\!\:\;\...\‘\’\`\“\”\"\'~]''')
nlp.tokenizer.infix_finditer = infix_re.finditer

def normalize_text(text: str) -> str:
    """
    Normaliza un texto utilizando el pipeline de spaCy.
   réplica la normalizacion de los  .pkl.
    """
    if not isinstance(text, str):
        return ""

    # Usamos el objeto 'nlp' global que ya está configurado
    doc = nlp(text)
    
    # Lista de Part-of-Speech (categorías gramaticales) a eliminar
    pos_to_remove = ['DET', 'ADP', 'CCONJ', 'SCONJ', 'PRON']
    
    processed_tokens = []
    
    for token in doc:
        # Ignorar las categorías gramaticales no deseadas y los espacios
        if token.pos_ in pos_to_remove or token.is_space:
            continue
        
        # Para el resto, añadimos el lema en minúsculas.
        processed_tokens.append(token.lemma_.lower())
            
    # Unimos los tokens para formar la cadena de texto normalizada.
    return " ".join(processed_tokens)
# --- FIN DE CONFIGURACIÓN DE SPACY ---


def find_similar_documents(query_text: str, corpus: str, feature_type: str, vector_type: str, base_path: str = 'representation'):
    """
    Encuentra los 10 documentos más similares a un texto de consulta dado.
    """
    try:
        # 1. Construir las rutas a los archivos .pkl
        vector_path = Path(base_path) / f"{corpus}_vectors"
        matrix_file = vector_path / f"{corpus}_{vector_type}_{feature_type}_matrix.pkl"
        vectorizer_file = vector_path / f"{corpus}_{vector_type}_{feature_type}_vectorizer.pkl"

        # 2. Cargar la matriz del corpus y el vectorizador
        with open(matrix_file, 'rb') as f:
            corpus_matrix = pickle.load(f)
        
        with open(vectorizer_file, 'rb') as f:
            vectorizer = pickle.load(f)

        # 3. <<-- PASO CLAVE: Normalizamos el texto de la consulta -->>
     
        normalized_query = normalize_text(query_text)
        
        # 4. Transformar el texto YA NORMALIZADO usando el vectorizador cargado
        query_vector = vectorizer.transform([normalized_query])

        # 5. Aplicar el algoritmo de similitud del coseno
        cosine_similarities = cosine_similarity(query_vector, corpus_matrix).flatten()

        # 6. Obtener los índices de los 10 documentos más similares
        most_similar_indices = np.argsort(cosine_similarities)[-10:][::-1]

        # 7. Crear la lista de resultados con (índice, similitud)
        results = [(idx, cosine_similarities[idx]) for idx in most_similar_indices]
        
        return results

    except FileNotFoundError:
        print(f"Error: No se encontraron los archivos para la configuración:")
        print(f"Matrix: {matrix_file}")
        print(f"Vectorizer: {vectorizer_file}")
        return []
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return []