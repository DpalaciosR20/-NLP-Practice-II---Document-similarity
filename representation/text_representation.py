import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import pickle
import os

def build_vector_representations(corpus_name: str):
    """
    Genera y guarda las 6 representaciones vectoriales para un corpus específico.

    Args:
        corpus_name (str): El nombre del corpus a procesar (ej. 'arxiv' o 'pubmed').
    """
    # Construcción dinámica de rutas basada en la estructura del proyecto
    input_csv_path = f'normalizated_corpus/{corpus_name}_normalized_corpus.csv'
    output_dir = f'representation/{corpus_name}_vectors'

    print(f"\n--- Iniciando la representación para el corpus: {corpus_name.upper()} ---")

    # 1. Cargar el corpus normalizado
    try:
        df = pd.read_csv(input_csv_path)
        print(f"Corpus '{input_csv_path}' cargado.")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{input_csv_path}'. Saltando este corpus.")
        return

    # 2. Combinar Título y Abstract
    df['combined_text'] = df['Title'].fillna('') + ' ' + df['Abstract'].fillna('')
    corpus_texts = df['combined_text']

    # 3. Definir las configuraciones de vectorización
    vectorizer_configs = {
        f'{corpus_name}_freq_unigram': CountVectorizer(ngram_range=(1, 1)),
        f'{corpus_name}_freq_bigram':  CountVectorizer(ngram_range=(2, 2)),
        f'{corpus_name}_binary_unigram': CountVectorizer(ngram_range=(1, 1), binary=True),
        f'{corpus_name}_binary_bigram':  CountVectorizer(ngram_range=(2, 2), binary=True),
        f'{corpus_name}_tfidf_unigram': TfidfVectorizer(ngram_range=(1, 1)),
        f'{corpus_name}_tfidf_bigram':  TfidfVectorizer(ngram_range=(2, 2))
    }

    # Crear el directorio de salida si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Directorio de salida creado en: '{output_dir}'")

    # 4. Iterar, generar y guardar cada representación
    for name, vectorizer in vectorizer_configs.items():
        print(f"Generando representación: {name}...")
        
        vector_matrix = vectorizer.fit_transform(corpus_texts)
        
        vectorizer_path = os.path.join(output_dir, f'{name}_vectorizer.pkl')
        matrix_path = os.path.join(output_dir, f'{name}_matrix.pkl')
        
        # 5. Guardar el vectorizador y la matriz
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(vectorizer, f)
        
        with open(matrix_path, 'wb') as f:
            pickle.dump(vector_matrix, f)
            
        print(f" -> Guardado en '{output_dir}'")

    print(f"--- Representación para {corpus_name.upper()} completada. ---")