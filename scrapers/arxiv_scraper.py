# scrapers/arxiv_scraper.py

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re
import logging

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# --- FIN DE CONFIGURACIÓN ---

ARXIV_SECTIONS = {
    "Computation and Language": "https://arxiv.org/list/cs.CL/recent",
    "Computer Vision and Pattern Recognition": "https://arxiv.org/list/cs.CV/recent",
    "Cryptography and Security": "https://arxiv.org/list/cs.CR/recent",
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_remaining_details(preliminary_data: dict, abs_page_url: str, html_page_url: str) -> dict | None:
    """
    Obtiene los datos restantes (Fecha y Abstract) visitando las páginas correspondientes.
    """
    try:
        # --- Petición a la página de Abstract para la FECHA ---
        abs_response = requests.get(f"https://arxiv.org{abs_page_url}", headers=HEADERS)
        abs_response.raise_for_status()
        abs_soup = BeautifulSoup(abs_response.content, 'lxml')

        # --- Petición a la página HTML para el ABSTRACT ---
        html_response = requests.get(html_page_url, headers=HEADERS)
        html_response.raise_for_status()
        html_soup = BeautifulSoup(html_response.content, 'lxml')
        
        logging.debug(f"Peticiones de detalle completadas para {preliminary_data['DOI']}")

        # Extraer fecha de la página /abs
        date_text = abs_soup.select_one('div.dateline').text.strip()
        raw_date_match = re.search(r'(\d{1,2}\s\w{3}\s\d{4})', date_text)
        if raw_date_match:
            preliminary_data['Date'] = datetime.strptime(raw_date_match.group(1), '%d %b %Y').strftime('%d/%m/%Y')
        else:
            preliminary_data['Date'] = "N/A"

        # Extraer abstract de la página /html
        abstract_content = html_soup.select_one('div.ltx_abstract p.ltx_p')
        preliminary_data['Abstract'] = abstract_content.text.strip().replace('\n', ' ') if abstract_content else "N/A"

        return preliminary_data

    except Exception as e:
        logging.error(f"Error obteniendo detalles para {preliminary_data['DOI']}: {e}", exc_info=False)
        return None

def scrape_arxiv_section(section_name: str, section_url: str, num_articles: int = 100) -> list:
    """
    Scrapea una sección de arXiv, extrayendo la mayor parte de los datos de la página de listado.
    """
    logging.info(f"Iniciando scraping de la sección: '{section_name}'...")
    articles_data = []
    page_size = 50
    articles_collected = 0

    for i in range(10): 
        if articles_collected >= num_articles:
            break
        
        paginated_url = f"{section_url}?skip={i * page_size}&show={page_size}"
        logging.info(f"Accediendo a la página de listado: {paginated_url}")

        try:
            response = requests.get(paginated_url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            dt_tags = soup.select("dl#articles dt")
            logging.info(f"Se encontraron {len(dt_tags)} artículos potenciales en la página.")
            if not dt_tags:
                logging.warning("No se encontraron más artículos. Finalizando sección.")
                break

            for dt_tag in dt_tags:
                if articles_collected >= num_articles:
                    break

                dd_tag = dt_tag.find_next_sibling("dd")
                html_link_tag = dt_tag.select_one("a[title='View HTML']")
                abs_link_tag = dt_tag.select_one("a[title='Abstract']")

                if not html_link_tag or not abs_link_tag or not dd_tag:
                    logging.warning("Artículo descartado por falta de enlaces o metadatos.")
                    continue

                try:
                    # --- Extracción desde la página de listado (más fiable) ---
                    title = dd_tag.select_one("div.list-title").text.replace("Title:", "").strip()
                    authors = ", ".join([a.text.strip() for a in dd_tag.select("div.list-authors a")])
                    
                    article_id = abs_link_tag['href'].split('/')[-1]
                    doi = f"10.48550/arXiv.{article_id}"
                    
                    preliminary_data = {
                        "DOI": doi,
                        "Title": title,
                        "Authors": authors,
                        "Section": section_name
                    }

                    # --- Obtener los datos restantes de las páginas de detalle ---
                    full_details = get_remaining_details(preliminary_data, abs_link_tag['href'], html_link_tag['href'])

                    if full_details:
                        articles_data.append(full_details)
                        articles_collected += 1
                        logging.info(f"[{articles_collected}/{num_articles}] Artículo recolectado: {full_details['Title'][:60]}...")
                    
                    time.sleep(1) # Pausa respetuosa

                except Exception as e:
                    logging.error(f"Error procesando un artículo de la lista: {e}")
                    continue
        
        except Exception as e:
            logging.error(f"Error crítico al acceder a {paginated_url}: {e}")
            break

    logging.info(f"Scraping de '{section_name}' completado. Total de artículos: {len(articles_data)}.")
    return articles_data