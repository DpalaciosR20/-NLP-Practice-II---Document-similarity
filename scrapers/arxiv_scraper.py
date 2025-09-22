import requests
from bs4 import BeautifulSoup
import time

# URLs de las secciones de arXiv
ARXIV_SECTIONS = {
    "Computation and Language": "https://arxiv.org/list/cs.CL/recent",
    "Computer Vision and Pattern Recognition": "https://arxiv.org/list/cs.CV/recent",
    "Cryptography and Security": "https://arxiv.org/list/cs.CR/recent",
}

# Es buena práctica simular un navegador real con headers.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_article_details(html_url: str, section: str) -> dict:
    """Extrae los detalles de una única página de artículo de arXiv."""
    try:
        response = requests.get(f"https://arxiv.org{html_url}", headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        # TODO: Implementar la lógica de extracción para cada campo.
        # Usa .select_one() o .find() con los selectores CSS apropiados.
        # Ejemplo: title = soup.select_one('h1.title').text.replace('Title:', '').strip()
        
        doi = soup.select_one('meta[name="citation_doi"]')['content'] if soup.select_one('meta[name="citation_doi"]') else "N/A"
        title = soup.select_one('h1.title').text.replace('Title:', '').strip()
        authors = ", ".join([a.text for a in soup.select('div.authors a')])
        abstract = soup.select_one('blockquote.abstract').text.replace('Abstract:', '').strip().replace('\n', ' ')
        date_str = soup.select_one('div.dateline').text.strip().split('(')[-1].split(')')[0].replace('Submitted on ', '')
        
        return {
            "DOI": f"10.48550/arXiv.{html_url.split('/')[-1]}", # El DOI a veces no está en meta, se puede construir
            "Title": title,
            "Authors": authors,
            "Abstract": abstract,
            "Section": section,
            "Date": date_str, # Formato puede requerir post-procesamiento
        }
    except Exception as e:
        print(f"Error extrayendo detalles de {html_url}: {e}")
        return None

def scrape_arxiv_section(section_name: str, section_url: str, num_articles: int = 100) -> list:
    """Scrapea una sección de arXiv hasta obtener el número deseado de artículos."""
    print(f"Iniciando scraping de la sección: {section_name}...")
    articles_data = []
    # arXiv muestra 25 por página, "?show=25" es el default. skip para paginación.
    page_size = 25 
    pages_to_scrape = (num_articles + page_size - 1) // page_size # Calcular cuántas páginas

    for i in range(pages_to_scrape):
        paginated_url = f"{section_url}?skip={i * page_size}&show={page_size}"
        try:
            response = requests.get(paginated_url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')

            # Encontrar todos los enlaces que apuntan a la vista HTML del artículo
            html_links = [
                a_tag['href'] 
                for a_tag in soup.find_all('a', {'title': 'View HTML'})
            ]

            for link in html_links:
                if len(articles_data) >= num_articles:
                    break
                details = get_article_details(link, section_name)
                if details:
                    articles_data.append(details)
                    print(f"  [{len(articles_data)}/{num_articles}] Obtenido: {details['Title'][:50]}...")
                time.sleep(1) # Ser respetuosos con el servidor, esperar 1 segundo entre peticiones.
        
        except Exception as e:
            print(f"Error al acceder a la página de listado {paginated_url}: {e}")
            
        if len(articles_data) >= num_articles:
            break

    print(f"Scraping de '{section_name}' completado. Total de artículos: {len(articles_data)}.")
    return articles_data