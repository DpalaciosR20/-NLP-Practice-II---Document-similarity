import polars as pl
from scrapers import arxiv_scraper, pubmed_scraper

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


if __name__ == "__main__":
    print("Iniciando el proceso de recolección de artículos...")
    
    # Puedes elegir cuál construir o construir ambos
    build_arxiv_corpus()
    # build_pubmed_corpus() # Descomentar cuando el scraper de PubMed esté listo