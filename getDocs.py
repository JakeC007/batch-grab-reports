"""
Pulls PDFs from an annoying website; you'll need to supply your own URLS.
10/8/2024
J. Chanenson
"""
import yaml
from selenium import webdriver
from selenium.webdriver.firefox.service import Service  # Import the Service class
from selenium.webdriver.firefox.options import Options  # Import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time, os
from datetime import datetime

def setup(download_dir):
    """
    Set up the Selenium WebDriver for Firefox with specified download preferences.

    Parameters:
    - download_dir (str): The directory where downloaded files should be saved.

    Returns:
    tuple: A tuple containing two elements:
        - Service: A Service object for geckodriver.
        - Options: A Firefox Options object with custom preferences set for downloading files.
    """
    # Set up Selenium with Firefox
    driver_path = r'geckodriver.exe'

    ## Because selenium is being fussy 
    # Set the path to the Firefox binary
    firefox_binary_path = r'C:\Program Files\Mozilla Firefox\firefox.exe'
    # Create a Service object with the path to geckodriver
    service = Service(executable_path=driver_path)
    # Create Firefox options and set the binary location
    options = Options()
    options.binary_location = firefox_binary_path

    # Set preferences for automatic downloads using Firefox options
    options.set_preference("browser.download.folderList", 2)  # Use custom download path
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")  # MIME types to download automatically
    options.set_preference("pdfjs.disabled", True)  # Disable PDF viewer
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.manager.alertOnEXEOpen", False)
    options.set_preference("browser.download.manager.closeWhenDone", True)
    options.set_preference("browser.download.manager.showAlertOnComplete", False)
    options.set_preference("browser.download.manager.focusWhenStarting", False)

    return service, options

def login():
    """
    Logs into the WEBSITE application using credentials stored in a YAML file.
    """
    cred_f = "credentials.yml"
    with open(cred_f, 'r') as file:
        config = yaml.safe_load(file)

    username = config['login']['username']
    password = config['login']['password']

    driver.get('example.com')  

    # Find and fill login form fields using credentials from the YAML file
    username_field = driver.find_element(By.ID, 'username')  
    password_field = driver.find_element(By.ID, 'password') 
    login_button = driver.find_element(By.XPATH, '//input[@value="Login"]') 

    # Enter the credentials from the YAML file
    username_field.send_keys(username)
    password_field.send_keys(password)
    login_button.click()
    
    # Wait for the page to load
    time.sleep(5)

def getDoc(doc_id):
    """
    Search for a document by its ID (via pagination) and navigate to its report.

    Parameters:
        doc_id (int or str): The ID of the document to search for, which is expected to be 
                             the number part of the document title.
    """
    driver.get('example.com')  # Go to the main page

    while True:
        # Wait until the document table loads
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.document_row'))
        )

        # Find all the rows in the document table
        rows = driver.find_elements(By.CSS_SELECTOR, '.document_row')

        # Flag to check if the document is found
        doc_found = False

        for row in rows:
            # Find the span with the document title
            doc_title_span = row.find_element(By.CSS_SELECTOR, '.td_title .document_title')
            doc_title = doc_title_span.text.strip()

            # Extract the document number from the title (e.g., extract '8250' from '8250-doc.pdf')
            doc_number = doc_title.split('-')[0]

            # Check if the extracted document number matches the doc_id we are looking for
            if str(doc_id) == doc_number:
                print(f"Found document with number: {doc_id}")

                # Now find and click the similarity report link for this document row
                report_link = row.find_element(By.CSS_SELECTOR, 'a.btn.btn-default-alt')

                # Print the link to ensure it is correct (optional for debugging)
                report_url = report_link.get_attribute('href')
                # print(f"Report URL: {report_url}")

                doc_found = True
 
                clickDownloadButton(report_url, doc_id)
                break

        # If the document was found, exit the loop
        if doc_found:
            break

        # Otherwise, check if there is a "Next" button and click it to go to the next page
        try:
            next_button = driver.find_element(By.LINK_TEXT, 'Next')  # Using LINK_TEXT for the "Next" button
            print("Clicking the Next button to go to the next page.")
            next_button.click()

            # Wait for the next page to load
            time.sleep(3)

        except:
            # If no "Next" button is found, it means we've reached the last page
            print(f"Document with number {doc_id} not found after checking all pages.")
            break

def clickDownloadButton(report_url, doc_id):
    """
        Locate and click the download button to download the PDF of the current report view.

        Parameters:
            report_url (str): The URL of the report page from which to download the PDF.
            doc_id (int or str): The ID of the document, used for logging download failures.
    """
    
    driver.get(report_url) #load the DOM by going to it

    try:
        # Wait until the download button with the selector #sc2749 is present
        download_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="sc2749"]'))  # XPath to the button
        )
        download_button.click()
        print("Requested download")
        # time.sleep(30)
        check_downloads(doc_id)
        
        # If the download didn't happen in time; log it
        if not check_downloads:
            log_failed_download(doc_id)

    except Exception as e:
        print(f"Failed to click the download button: {e}")
        with open("page_source.html", "w", encoding="utf-8") as file:
            file.write(driver.page_source)

        print("Page source written to 'page_source.html'")

def check_downloads(doc_id):
    """
    Check if all files in the download directory have been fully downloaded.

    This function monitors the download directory for any incomplete files (with 
    extensions .part or .crdownload) and waits until they are fully downloaded. 
    If the specified document ID already exists in the directory, the function will 
    terminate early, indicating that the download is complete.

    Parameters:
        doc_id (int or str): The ID of the document being downloaded, which is used 
                             to construct the expected file name.

    Returns:
        bool: Returns True if the expected document file is found and is fully downloaded, 
              or False if the download did not complete within the specified timeout.
    """
    print(f"Checking for downloads in {download_dir}...")

    # Set the maximum wait time and the polling interval (in seconds)
    timeout = 120  # Maximum wait time in seconds
    polling_interval = 2  # Time to wait between checks

    # Construct the expected file name
    expected_file_name = f"{doc_id}_doc.pdf"

    # Check if the file already exists in the directory
    if expected_file_name in os.listdir(download_dir):
        print(f"File {expected_file_name} already exists in the directory. Stopping check.")
        return True

    start_time = time.time()

    while time.time() - start_time < timeout:
        # Get a list of files in the download directory
        files_in_directory = os.listdir(download_dir)

        # Check if there are any incomplete downloads (Firefox uses ".part")
        downloading = [f for f in files_in_directory if f.endswith(".part") or f.endswith(".crdownload")]

        if not downloading and expected_file_name in os.listdir(download_dir):
            # No incomplete downloads and the file exists, download is complete
            print("Download complete!")
            return True
        else:
            # Still downloading

            if not downloading:
                # If the downloading list is empty, print waiting message
                print("Waiting for download to start...")
            else:
                # Still downloading, print the current downloads
                print(f"Still downloading... {downloading}")
            time.sleep(polling_interval)  # Wait before checking again

    # Timeout exceeded
    print(f"Download did not complete within {timeout} seconds.")
    return False

def log_failed_download(doc_id):
    """
    Logs the failed download attempt with a timestamp to a file.
    
    Parameters:
    doc_id (int or str): The ID of the document to log.
    """
    with open(failed_downloads_file, 'a') as f:  # Open the file in append mode
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} - Failed to download document with ID: {doc_id}\n")


if __name__ == "__main__":
    # Set globals
    download_dir = r"\your\preferred\download_folder\path"
    failed_downloads_file = "failed.txt"

    # Set up Firefox
    service, options = setup(download_dir)

    # Initialize the WebDriver with the service object and options
    driver = webdriver.Firefox(service=service, options=options)

    login()
    # Run docs
    doclst = [4418, 9353, 7634]
    for doc in doclst:
        getDoc(doc)