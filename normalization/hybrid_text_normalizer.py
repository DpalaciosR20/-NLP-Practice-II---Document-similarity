import spacy
import nltk
from nltk.stem import WordNetLemmatizer

# --- CONFIGURACIÓN INICIAL (se ejecuta una sola vez) ---
try:
    # Intenta usar el lematizador. Si falla, descarga los datos necesarios.
    _ = WordNetLemmatizer().lemmatize("test")
except LookupError:
    print("Descargando recursos de NLTK (wordnet)...")
    nltk.download('wordnet')

# Cargar el modelo de spaCy (puedes usar 'lg' para mayor precisión)
print("Cargando modelo de spaCy...")
nlp = spacy.load("en_core_web_lg")
print("Modelo cargado.")

# Instanciar el lematizador de NLTK que usaremos para forzar la forma verbal
wn_lemmatizer = WordNetLemmatizer()
# ---------------------------------------------------------


def normalize_text(text: str) -> str:
    """
    Normaliza un texto con un enfoque híbrido: usa spaCy para el contexto
    y NLTK para forzar la lematización de verbos en casos ambiguos.
    """
    if not isinstance(text, str):
        return ""

    doc = nlp(text)
    
    pos_to_remove = ['DET', 'ADP', 'CCONJ', 'SCONJ', 'PRON']
    
    lemmas = []
    for token in doc:
        # Condiciones para conservar un token
        if (token.pos_ not in pos_to_remove and
            not token.is_punct and
            not token.is_space):
            
            # --- INICIO DE LA LÓGICA HÍBRIDA ---
            # Si spaCy lo ve como sustantivo/adjetivo pero parece un verbo...
            if token.pos_ in ['NOUN', 'ADJ'] and (token.text.endswith('ing') or token.text.endswith('ed')):
                # ...forzamos la lematización a su forma de verbo con NLTK.
                lemma = wn_lemmatizer.lemmatize(token.text, pos='v')
            else:
                # Si no, confiamos en el lema de spaCy.
                lemma = token.lemma_
            # --- FIN DE LA LÓGICA HÍBRIDA ---
            
            lemmas.append(lemma.lower())
            
    return " ".join(lemmas)