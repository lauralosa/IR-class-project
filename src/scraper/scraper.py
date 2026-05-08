import time
import os
import platform
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service



def is_valid_executable(path):
    """
    Check if a path points to a valid executable file.

    Args:
        path (str): Path to check.

    Returns:
        bool: True if the path is a valid executable file, False otherwise.
    """
    if not os.path.isfile(path):
        return False

    # On Windows, os.access with os.X_OK may not work reliably
    # so we just check if the file exists
    if platform.system() == "Windows":
        return True

    # On Unix-like systems, check if the file is executable
    return os.access(path, os.X_OK)


def find_chrome_executable():
    """
    Attempts to find Chrome executable in common installation locations.

    Checks for Chrome in default installation paths on both Windows and Linux.
    Returns the path to the Chrome executable if found, otherwise returns None.

    Returns:
        str or None: Path to Chrome executable if found, None otherwise.
    """
    system = platform.system()

    # List of common Chrome executable paths
    chrome_paths = []

    if system == "Windows":
        # Windows default installation paths
        possible_paths = [
            # Chrome stable
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            # Chromium
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Chromium', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Chromium', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Chromium', 'Application', 'chrome.exe'),
        ]
        chrome_paths.extend(possible_paths)

        # Also add hardcoded paths for Chrome
        chrome_paths.extend([
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Users\\%USERNAME%\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files\\Chromium\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Chromium\\Application\\chrome.exe',
            'C:\\Users\\%USERNAME%\\AppData\\Local\\Chromium\\Application\\chrome.exe',
            'D:\\Portable\\chrome\\chrome.exe'
        ])

    elif system == "Linux":
        # Linux default installation paths
        possible_paths = [
            '/usr/bin/google-chrome',
            '/usr/local/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/local/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/local/bin/chromium',
            '/usr/local/bin/chromium-browser',
            '/snap/bin/chromium',
            '/opt/google/chrome/chrome',
            '/opt/google/chrome/google-chrome',
        ]
        chrome_paths.extend(possible_paths)

        # Also add hardcoded paths for Chrome inside the project directory (for portable Chrome)
        chrome_paths.extend([
            'chrome-linux64/chrome'
        ])

    elif system == "Darwin":  # macOS
        possible_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
        ]
        chrome_paths.extend(possible_paths)

    # Check each path
    for chrome_path in chrome_paths:
        if is_valid_executable(chrome_path):
            print(f"Found Chrome at: {chrome_path}")
            return chrome_path

    # If not found in common locations, check if 'google-chrome' or 'chromium' is in PATH
    for executable in ['google-chrome', 'chromium', 'chromium-browser', 'chrome']:
        chrome_in_path = shutil.which(executable)
        if chrome_in_path:
            print(f"Found Chrome in PATH: {chrome_in_path}")
            return chrome_in_path

    print("Chrome not found in default locations.")
    return None


class UMinhoDSpace8Scraper:
    def __init__(self, base_url, max_items=10):
        """
        Initialize the web scraper with Selenium WebDriver configuration.
        Args:
            base_url (str): The base URL of the website to scrape.
            max_items (int, optional): Maximum number of items to scrape. Defaults to 10.
        Note:
            Automatically detects Chrome in default installation locations on Windows and Linux.
            If you don't have Chrome, you can download a portable version from:
            https://googlechromelabs.github.io/chrome-for-testing/#stable
        """
        self.base_url = base_url
        chrome_options = Options()

        # Try to find Chrome in default installation locations
        chrome_path = find_chrome_executable()

        if chrome_path is None:
            raise FileNotFoundError("Chrome executable not found. Please install Chrome or provide a portable version.")

        chrome_options.binary_location = chrome_path
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

        # Time to wait for Angular to settle after page loads
        self.ANGULAR_SETTLE_TIME = 0.5  # seconds
        # Max items to scrape
        self.MAX_ITEMS = max_items

    def get_paper_info(self, url):
        
        """
        Versão Debug: Explica passo a passo o que está a acontecer.
        """
        # --- PASSO 1: LANDING PAGE (PDF) ---
        print(f"      > A aceder à Landing Page: {url}")
        self.driver.get(url)
        pdf_url = "N/A"
        
        try:
            # Espera pelo link do PDF (bitstream)
            wait_pdf = WebDriverWait(self.driver, 7)
            wait_pdf.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='bitstream']")))
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='bitstream']")
            for link in links:
                href = link.get_attribute("href")
                if href and any(term in href.lower() for term in ["download", "content", ".pdf"]):
                    pdf_url = href
                    print(f"        [OK] PDF encontrado: {pdf_url[:50]}...")
                    break
        except:
            print("        [!] PDF não encontrado nesta página.")

        # --- PASSO 2: METADADOS (/full) ---
        full_url = url + "/full"
        print(f"      > A mudar para Metadados: {full_url}")
        self.driver.get(full_url)
        
        # Inicializamos o dicionário com o que já temos
        data = { 
            "title": "N/A", "year": "N/A", "doi": "N/A", 
            "abstract": "N/A", "authors": [], "keywords": [], 
            "affiliations": [], "pdf_url": pdf_url 
        }

        try:
            # Espera forçada para a tabela carregar 
            wait_table = WebDriverWait(self.driver, 10)
            wait_table.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-striped tbody tr")))
            
            # Pequena pausa extra para o Angular "pintar" os dados
            time.sleep(1.5)

            targets = {
            "dc.title": "title",
            "dc.date.issued": "year",
            "dc.identifier.doi": "doi",
            "dc.contributor.author": "authors",
            "dc.description.abstract": "abstract",
            "dc.subject": "keywords",
            "sdum.uoei": "affiliations", 
            "dc.contributor.affiliation": "affiliations",
            "thesis.degree.grantor": "affiliations"
            }

            rows = self.driver.find_elements(By.CSS_SELECTOR, "table.table-striped tbody tr")
            found_fields = 0
            
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 2:
                    label = cols[0].text.strip()
                    val = cols[1].text.strip()
                    
                    if label in targets:
                        key = targets[label]
                        # Tratamos keywords, authors e affiliations como listas
                        if key in ["authors", "keywords", "affiliations"]:
                            data[key].append(val)
                        else:
                            data[key] = val
                        found_fields += 1
            
            print(f"        [OK] Extraídos {found_fields} campos de metadados.")

        except Exception as e:
            print(f"        [ERRO] Falha crítica na tabela: {e}")

        return data

    def go_to_next_page(self):
        """
        Attempts to click the next page button.
        Raises NoSuchElementException if the button is missing or disabled.
        """
        # XPath looking for an active (not disabled) 'Next' button
        next_button_xpath = "//li[contains(@class, 'page-item') and not(contains(@class, 'disabled'))]/a[@aria-label='Next']"

        try:
            next_button = self.driver.find_element(By.XPATH, next_button_xpath)

            # Scroll and Click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            next_button.click()

            # Wait for Angular to swap the content, Slightly longer wait after clicking
            time.sleep(self.ANGULAR_SETTLE_TIME + 1)
            return True

        except NoSuchElementException:
            # Re-raising the exception so the caller knows to stop the loop
            raise NoSuchElementException("Reached the last page: 'Next' button is missing or disabled.")

    def collect_all_links(self):
        """
        Iterates through pagination to collect paper URLs up to self.MAX_ITEMS.
        1. Loads the initial collection page.
        2. Extracts paper links from each item on the page.
        3. Navigates to the next page until no more pages or limit reached.
        4. Returns a list of unique paper URLs.
        """
        paper_urls = []

        # Load the initial collection page
        self.driver.get(self.base_url)

        # Wait for the Angular component that holds the item list
        print("Waiting for Angular to populate the item list...")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "ds-listable-object-component-loader")))

        # Give it a moment to render the links inside those components
        time.sleep(self.ANGULAR_SETTLE_TIME)

        while True:

            # 1. Locate all paper containers on the current page
            items = self.driver.find_elements(By.TAG_NAME, "ds-listable-object-component-loader")

            # Handle cases where the page didn't load any items
            if not items:
                if not paper_urls:
                    print("Error: Could not find any item links in the list.")
                    return []
                print("No items found on this page. Stopping pagination.")
                break

            # 2. Extract links from each item
            for item in items:
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, "a.item-list-title")
                    href = title_elem.get_attribute("href")

                    if href:
                        # Clean the URL (removes ?show=full etc.)
                        clean_url = href.split('?')[0]

                        if clean_url not in paper_urls:
                            paper_urls.append(clean_url)
                            print(f"  [{len(paper_urls)}] Found: {clean_url}")

                    # Stop immediately if we hit the limit
                    if len(paper_urls) >= self.MAX_ITEMS:
                        print(f"Reached limit of {self.MAX_ITEMS} items.")
                        return paper_urls

                except NoSuchElementException:
                    continue # Skip items that don't have a title link

            # 3. Attempt to move to the next page
            try:
                self.go_to_next_page()
            except NoSuchElementException:
                print("No more pages to scrape.")
                break

        return paper_urls

    def scrape(self):
        """
        Main method to scrape the collection and extract metadata for each paper.
        """
        results = []     # To store final results
        paper_urls = []  # To store unique paper URLs

        print(f"Loading collection list: {self.base_url}") # Debug print

        try:

            # Collect paper links across paginated collection
            paper_urls = self.collect_all_links()

            print(f"Found {len(paper_urls)} papers. Extracting metadata...") # Debug print

            # Visit each paper to get the abstract and authors
            for url in paper_urls:
                # print(f"   Opening Paper: {url}")               # Debug print
                paper_info = self.get_paper_info(url)     # get the paper info
                print(f"      Title: {paper_info['title']}")    # Debug print
                results.append(paper_info)

        finally:
            self.driver.quit()

        return results
