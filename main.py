import polars as pl
import pandas as pd
from scrapers import arxiv_scraper, pubmed_scraper
from normalization import text_normalizer

# ***********************************************************************
#                     --- 1. RECOLECCIÓN DE LOS ARTÍCULOS ---
# ***********************************************************************
def build_arxiv_corpus():
    """Recolecta datos de todas las secciones de arXiv y crea el corpus CSV."""
    all_arxiv_articles = []
    
    # Recolectar 100 artículos de cada sección 
    for section_name, section_url in arxiv_scraper.ARXIV_SECTIONS.items():
        articles = arxiv_scraper.scrape_arxiv_section(section_name, section_url, num_articles=100)
        all_arxiv_articles.extend(articles)

    if not all_arxiv_articles:
        print("No se recolectaron artículos de arXiv. Abortando la creación del corpus.")
        return

    # Crear DataFrame con Polars
    df = pl.DataFrame(all_arxiv_articles)
    
    # Asegurar el orden de las columnas según la especificación
    df = df.select(["DOI", "Title", "Authors", "Abstract", "Section", "Date"])
    
    # Guardar en CSV con separador de tabulación [cite: 67]
    output_file = "arxiv_raw_corpus.csv"
    df.write_csv(output_file, separator='\t')
    print(f"Corpus de arXiv guardado exitosamente en '{output_file}' con {len(df)} artículos.")

def build_pubmed_corpus():
    """Recolecta datos de PubMed y crea el corpus CSV."""
    # Recolectar 300 artículos 
    all_pubmed_articles = pubmed_scraper.scrape_pubmed(num_articles=300)

    if not all_pubmed_articles:
        print("No se recolectaron artículos de PubMed. Abortando la creación del corpus.")
        return

    df = pl.DataFrame(all_pubmed_articles)
    
    # Asegurar el orden de las columnas [cite: 70]
    df = df.select(["DOI", "Title", "Authors", "Abstract", "Journal", "Date"])

    # Guardar en CSV con separador de tabulación [cite: 77]
    output_file = "pubmed_raw_corpus.csv"
    df.write_csv(output_file, separator='\t')
    print(f"Corpus de PubMed guardado exitosamente en '{output_file}' con {len(df)} artículos.")

# ***********************************************************************
#              --- 2. NORMALIZACIÓN DE CADA CORPUS DE TEXTO ---
# ***********************************************************************
def build_corpus_normalization():
    """ Normaliza el corpus crudo de ArXiv y PubMed """
    
    # 1. Cargar el corpus crudo de arXiv
    print("Cargando el corpus crudo...")
    input_csv_path = 'arxiv_raw_corpus.csv'
    try:
        df = pd.read_csv(input_csv_path, sep='\t')
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{input_csv_path}'. Asegúrate de que esté en la misma carpeta.")
        return

    # Crear una copia para la normalización
    normalized_df = df.copy()

    # 2. Aplicar la normalización a las columnas deseadas
    print("Normalizando la columna 'Title'...")
    normalized_df['Title'] = df['Title'].apply(text_normalizer.normalize_text)

    print("Normalizando la columna 'Abstract'...")
    normalized_df['Abstract'] = df['Abstract'].astype(str).apply(text_normalizer.normalize_text)

    # 3. Guardar el corpus normalizado
    output_csv_path = 'arxiv_normalized_corpus.csv'
    print(f"Guardando el corpus normalizado en '{output_csv_path}'...")
    normalized_df.to_csv(output_csv_path, index=False, encoding='utf-8')

    print("¡Proceso completado con éxito!")

    # Ejemplo de uso con una consulta (esto también estaría en tu script principal)
    user_query = "I am looking for articles about Large Language Models and their challenges in NLP"
    normalized_query = text_normalizer.normalize_text(user_query)
    print("\n--- Ejemplo de Normalización de Consulta ---")
    print(f"Consulta Original: {user_query}")
    print(f"Consulta Normalizada: {normalized_query}")

    
if __name__ == "__main__":
    print("Iniciando el proceso de recolección de artículos...")
    
    # Puedes elegir cuál construir o construir ambos
    #build_arxiv_corpus()
    build_pubmed_corpus() # Descomentar cuando el scraper de PubMed esté listo
    # build_corpus_normalization()