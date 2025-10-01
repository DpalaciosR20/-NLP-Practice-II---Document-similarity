import spacy

# Cargar el modelo de lenguaje solo una vez cuando se importa el módulo.
print("Cargando modelo de spaCy (lg)...")
nlp = spacy.load("en_core_web_lg")
print("Modelo cargado.")

def normalize_text(text: str) -> str:
    """
    Normaliza un texto aplicando tokenización, eliminación de stop words 
    por categoría gramatical específica y lematización.
    
    Args:
        text (str): El texto a normalizar.
        
    Returns:
        str: El texto normalizado como una cadena de lemas.
    """
    # Casos donde el texto no sea una cadena (Doble filtro)
    if not isinstance(text, str):
        return ""

    # Procesar el texto con el pipeline de spaCy
    doc = nlp(text)
    
    # DET: Artículos (a, an, the)
    # ADP: Preposiciones (in, to, on, with)
    # CCONJ: Conjunciones coordinantes (and, but, or)
    # SCONJ: Conjunciones subordinantes (if, while, that)
    # PRON: Pronombres (I, you, he, she, it)
    pos_to_remove = ['DET', 'ADP', 'CCONJ', 'SCONJ', 'PRON']
    
    # Lista para guardar los lemas filtrados
    lemmas = []
    
    for token in doc:
        if (token.pos_ not in pos_to_remove and
            not token.is_punct and
            not token.is_space):
            lemmas.append(token.lemma_.lower())
            
    return " ".join(lemmas)