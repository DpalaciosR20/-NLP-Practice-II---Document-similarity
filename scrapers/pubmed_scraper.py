# scrapers/pubmed_scraper.py

from playwright.sync_api import sync_playwright, expect, Page, Locator, TimeoutError as PlaywrightTimeoutError
import time
import logging
import re
import os

# --- Configuración de Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

PUBMED_TRENDING_URL = "https://pubmed.ncbi.nlm.nih.gov/trending/?size=200"

def parse_nbib_data(nbib_text: str) -> dict | None:
    """
    Analiza un bloque de texto en formato NBIB/MEDLINE.
    Esta función no ha cambiado.
    """
    nbib_map = {
        'Title': 'TI', 'Authors': 'AU', 'Abstract': 'AB',
        'Journal': 'JT', 'Date': 'DP', 'DOI': 'LID'
    }
    required_fields = list(nbib_map.keys())
    
    data = {}
    authors = []
    last_tag = None

    for line in nbib_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        match = re.match(r'^([A-Z]{2,4})\s*-\s*(.*)', line)
        if match:
            tag, value = match.groups()
            last_tag = tag.strip()
            
            if last_tag == nbib_map['DOI'] and '[doi]' in line:
                data['DOI'] = value.split(' ')[0].strip()
            elif last_tag == nbib_map['Authors']:
                authors.append(value.strip())
            elif last_tag in nbib_map.values():
                field_name = [k for k, v in nbib_map.items() if v == last_tag][0]
                if field_name not in data:
                    data[field_name] = value.strip()
        elif last_tag and last_tag == nbib_map['Abstract'] and 'Abstract' in data:
            data['Abstract'] += ' ' + line

    if authors:
        data['Authors'] = ", ".join(authors)

    for field in required_fields:
        if field not in data or not data[field]:
            logging.warning(f"Artículo descartado. Campo requerido '{field}' no encontrado en el NBIB.")
            return None
            
    return data

def scrape_pubmed(num_articles: int = 300) -> list:
    """
    Scrapea la sección 'trending' de PubMed usando Playwright con una estrategia de múltiples pestañas
    y manteniendo los XPaths absolutos solicitados.
    """
    logging.info("Iniciando scraping de PubMed con Playwright...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        all_articles_data = []
        try:
            page.goto(PUBMED_TRENDING_URL, timeout=60000)
            page.wait_for_selector('article.full-docsum')
            viewed_articles=0
            
            while len(all_articles_data) < num_articles:
                # Esperar y contar artículos
                articles = page.locator('article.full-docsum')
                count_articles = articles.count()
                # logging.info(f"viewed={viewed_articles}, saved={len(all_articles_data)}, showing={count_articles}")
                
                
                if viewed_articles==count_articles:
                    logging.info("Cargando más artículos...")
                    page.locator('button[data-ga-action="show_more"]').click()
                
                for i in range(200):
                    if len(all_articles_data) < num_articles:
                        article = articles.nth(viewed_articles)
                        viewed_articles+=1
                        # logging.info(f"Titulo={article.locator('a.docsum-title').inner_text()}")
                        article.locator(selector_or_locator='button[data-ga-action="cite"]').nth(0).click()
                        with page.expect_download() as download_info:
                            page.locator("div.cite-dropdown.active").locator("span", has_text="Download .nbib").click()
                        # print(page.locator("div.cite-dropdown.active").locator("span", has_text="Download .nbib").count())
                        
                        page.keyboard.press("Escape")
                        download = download_info.value
                        temp_path = download.path()
                        # logging.info(f"  -> Archivo '{download.suggested_filename}' descargado.")  
                        with open(temp_path, 'r', encoding='utf-8') as f:
                            nbib_content = f.read()
                        
                        article_data = parse_nbib_data(nbib_content)
                        
                        if article_data:
                            all_articles_data.append(article_data)
                            # logging.info(f"  -> Artículo validado y agregado.")
                            logging.info(f"[{len(all_articles_data)}/{num_articles}] Articulos obtenidos...")



        #     # Si no hay suficientes artículos nuevos, cargar más
        #     if article_count < len(processed_urls) + 10 and article_count < num_articles:
        #         show_more_button = page.locator('button[data-ga-action="show_more"]')
        #         if show_more_button.is_visible():
        #             logging.info("Haciendo clic en 'Show more' para cargar más artículos...")
        #             show_more_button.click()
        #             page.wait_for_load_state('networkidle', timeout=10000)
        #             continue # Reiniciar el bucle para recontar y procesar
        #         else:
        #             logging.warning("No hay más botón 'Show more'. Finalizando.")
        #             break
            
        #     # Obtener la lista de URLs que aún no hemos procesado
        #     article_locators = page.locator('a.docsum-title').all()
        #     urls_to_process = [loc.get_attribute('href') for loc in article_locators if loc.get_attribute('href') not in processed_urls]

        #     if not urls_to_process:
        #         logging.info("No hay más artículos nuevos para procesar en esta tanda.")
        #         break
            
        #     for rel_url in urls_to_process:
        #         if len(all_articles_data) >= num_articles:
        #             break

        #         full_url = f"https://pubmed.ncbi.nlm.nih.gov{rel_url}"
        #         processed_urls.add(rel_url)
                
        #         article_page = context.new_page()
        #         try:
        #             logging.info(f"[{len(all_articles_data) + 1}/{num_articles}] Abriendo artículo en nueva pestaña...")
        #             article_page.goto(full_url, timeout=60000)

        #             # --- Flujo de Descarga con XPaths Absolutos ---
                    
        #             # 1. Clic en "Cite" (usando tu XPath absoluto)
        #             article_page.locator('xpath=/html/body/div[5]/aside/div/div[2]/div/button[1]').click()
        #             time.sleep(1)
                    
        #             # 2. Esperar la descarga y hacer clic en "Create File" (usando tu XPath absoluto)
        #             with article_page.expect_download() as download_info:
        #                 article_page.locator('xpath=/html/body/div[5]/div[2]/div/div[2]/div[2]/form/button').click()
                    
        #             download = download_info.value
        #             temp_path = download.path()
        #             logging.info(f"  -> Archivo '{download.suggested_filename}' descargado.")

        #             # 3. Leer, parsear y validar
        #             with open(temp_path, 'r', encoding='utf-8') as f:
        #                 nbib_content = f.read()
                    
        #             article_data = parse_nbib_data(nbib_content)
                    
        #             if article_data:
        #                 all_articles_data.append(article_data)
        #                 logging.info(f"  -> Artículo validado y agregado.")

        #         except PlaywrightTimeoutError:
        #             logging.warning(f"Timeout en {full_url}. El artículo podría no tener los elementos esperados. Saltando.")
        #         except Exception as e:
        #             logging.error(f"Error inesperado en {full_url}: {e}")
        #         finally:
        #             article_page.close()
        
        finally:
            browser.close()
            logging.info(f"Scraping de PubMed completado. Total de artículos recolectados: {len(all_articles_data)}.")
            return all_articles_data