import spacy
import re

print("Cargando modelo de spaCy (sm)...")
nlp = spacy.load("en_core_web_sm")

# --- INICIO DE LA PERSONALIZACIÓN DEL TOKENIZADOR ---

# 1. Obtener las reglas de infijo por defecto de spaCy.
#    Los "infijos" son los caracteres que spaCy usa para dividir una palabra por la mitad.
infix_re = re.compile(r'''[.\,\?\!\:\;\...\‘\’\`\“\”\"\'~]''')

# 2. Modificar el tokenizador para que NO divida las palabras con guiones.
#    Le decimos que trate las palabras alfanuméricas que incluyen guiones como un solo token.
nlp.tokenizer.infix_finditer = infix_re.finditer


def normalize_text(text: str) -> str:
    """
    Normaliza un texto conservando guiones en palabras y puntuación clave.
    Elimina solo las stop words por categoría gramatical.
    """
    if not isinstance(text, str):
        return ""

    doc = nlp(text)
    
    pos_to_remove = ['DET', 'ADP', 'CCCONJ', 'SCONJ', 'PRON']
    
    processed_tokens = []
    
    for token in doc:
        # Ignorar solo las categorías gramaticales no deseadas y los espacios.
        if token.pos_ in pos_to_remove or token.is_space:
            continue
        
        # Para todo lo demás (palabras, números, puntuación), añadimos el lema en minúsculas.
        # Para la puntuación, el lema es el propio carácter.
        processed_tokens.append(token.lemma_.lower())
            
    # Finalmente, unimos los tokens para formar la cadena de texto normalizada.
    return " ".join(processed_tokens)

# --- EJEMPLO DE DIAGNÓSTICO (puedes ejecutar este archivo para probar) ---
if __name__ == '__main__':
    test_text_1 = "RPG: A Repository Planning Graph for Unified and Scalable Codebase Generation"
    test_text_2 = "This is a state-of-the-art method."

    print("\n--- ANTES DE LA CORRECCIÓN (TOKENIZADOR POR DEFECTO) ---")
    # Carga una instancia limpia para comparar
    nlp_default = spacy.load("en_core_web_sm")
    print([token.text for token in nlp_default(test_text_2)])
    
    print("\n--- DESPUÉS DE LA CORRECCIÓN (TOKENIZADOR PERSONALIZADO) ---")
    print("Texto 1:", [token.text for token in nlp(test_text_1)])
    print("Texto 2:", [token.text for token in nlp(test_text_2)])

    print("\n--- RESULTADO DE LA NORMALIZACIÓN ---")
    print("Normalizado 1:", normalize_text(test_text_1))
    print("Normalizado 2:", normalize_text(test_text_2))