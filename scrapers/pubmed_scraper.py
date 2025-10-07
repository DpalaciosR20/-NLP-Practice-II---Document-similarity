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


def formatear_fecha(fecha: str):
    mes_num = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
           "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
    seasons_start_dates = {
        "Spring": "20/03",
        "Summer": "21/06",
        "Fall": "22/09",
        "Winter": "21/12"
    }
    # Suponiendo que al menos el año está (YYYY MM DD, YYYY MM, YYYY)
    # Formato original: YYYY MM DD
    print("fecha_org: "+fecha)
    fecha_separada = fecha.split(" ")
    año = fecha_separada[0]
    mes = (fecha_separada[1].split("-")[-1] if fecha_separada[1].split("-") else fecha_separada[1]) if len(fecha_separada) >= 2 else "Jan"
    if mes in ["Spring", "Summer", "Fall", "Winter"]:
        fecha_formateada=seasons_start_dates[mes]+"/"+año
    else:
        dia = (fecha_separada[2] if len(fecha_separada) == 3 else "1").zfill(2)
        fecha_formateada=dia+"/"+mes_num[mes]+"/"+año
    print("fecha-formt: "+fecha_formateada)
    return fecha_formateada    
   


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
            elif last_tag == nbib_map['Date']:
                data['Date'] = formatear_fecha(value)
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
                    time.sleep(1)
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
        
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            browser.close()
            logging.info(f"Scraping de PubMed completado. Total de artículos recolectados: {len(all_articles_data)}.")
            return all_articles_data