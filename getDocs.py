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
import pandas as pd
from tqdm import tqdm  


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
    driver_path = r'geckodriver.exe' #TODO: Edit This

    ## Because selenium is being fussy 
    # Set the path to the Firefox binary
    firefox_binary_path = r'C:\Program Files\Mozilla Firefox\firefox.exe' #TODO: Edit this, if needed
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

    driver.get('example.com/login')  #TODO: Edit This

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
    Search for a document by its ID and navigate to its similarity report.

    This function navigates to the iThenticate main folder page, searches for a document 
    by its ID (extracted from the document title), and, if found, clicks on the link to 
    view the similarity report for that document. It handles pagination by clicking the 
    "Next" button to load more documents if the document with the specified ID is not 
    found on the current page.

    Parameters:
        doc_id (int or str): The ID of the document to search for, which is expected to be 
                             the number part of the document title.
    """
    driver.get('example.com')  # Go to the main folder page; #TODO: Edit This
    acc = 0

    while True:
        global verbose

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
                if verbose:
                    print(f"\nFound document with number: {doc_id}")

                # Now find and click the similarity report link for this document row
                # report_link = row.find_element(By.CSS_SELECTOR, 'a.btn.btn-default-alt')
                report_link = row.find_element(By.CSS_SELECTOR, 'a.btn.btn-default-alt, a.btn.btn-primary')


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
            if verbose:
                # clear_terminal()
                print(f"Clicking the Next button to go to page {acc+2}.", end='\r')
                acc+=1
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

        This function navigates to the specified report URL and attempts to locate and click 
        the download button for the report. After initiating the download, it closes the current 
        tab and switches back to the original window. If the download button cannot be clicked 
        within the specified timeout, the function logs the error and saves the current page's 
        HTML source for debugging purposes.

        Parameters:
            report_url (str): The URL of the report page from which to download the PDF.
            doc_id (int or str): The ID of the document, used for logging download failures.

        Returns:
            None: This function does not return any value. It performs actions such as 
                navigating to a URL and clicking buttons.
    """
    
    driver.get(report_url) #load the DOM by going to it

    try:
        # Wait until the download button with the selector #sc2749 is present
        download_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="sc2749"]'))  # XPath to the button
        )
        download_button.click()
        global verbose
        if verbose:
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

        if verbose:
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
    # print(f"Checking for downloads in {download_dir}...")
    global verbose


    # Set the maximum wait time and the polling interval (in seconds)
    timeout = 120  # Maximum wait time in seconds
    polling_interval = 2  # Time to wait between checks

    # Construct the expected file name
    expected_file_name = f"{doc_id}_doc.pdf"

    # Check if the file already exists in the directory
    if expected_file_name in os.listdir(download_dir):
        if verbose:
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
            if verbose:
                print("\nDownload complete!")
            return True
        else:
            # Still downloading

            if not downloading:
                # If the downloading list is empty, print waiting message
                if verbose:
                    # clear_terminal()
                    print("Waiting for download to start...", end='\r')
            else:
                # Still downloading, print the current downloads
                if verbose:
                    print(f"Still downloading... {downloading}", end='\r')
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

def sortPapers(input_dir, output_dir, submissions_f):
    """
    Sort and zip paper submissions into subdirectories based on their Primary Subcommittee Selection.

    This function reads paper submission files from an input directory, filters the associated 
    metadata from a CSV file, and organizes the files into subdirectories based on their 
    'Primary Subcommittee Selection'. Each subdirectory is then zipped.

    Parameters:
    - input_dir (str): The directory containing the paper submission PDF files.
    - output_dir (str): The directory where the subcommittee subdirectories and zip files will be created.
    - submissions_f (str): The path to a CSV file containing the metadata, including Paper ID and Subcommittee Selection.

    Notes:
    - The filenames in the input directory should be the Paper ID followed by '.pdf'.
    - The CSV file must contain 'Paper ID' and 'Primary Subcommittee Selection' columns.

    Returns:
    - None
    """

    # Importing necessary libraries inside the function
    import shutil

    # Create the download and sorted directories if they don't exist
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(sorted_dir, exist_ok=True) 

    # Define the file ending (PDF in this case)
    FILE_ENDING = "_doc.pdf"

    # Load names of submission files.
    submissions = [int(x.split("_doc")[0]) for x in os.listdir(download_dir) if x.endswith('.pdf')]
    
    # Load submissions into a dataframe.
    df_all = pd.read_csv(submissions_f, low_memory=False)
    
    # Remove "pn" from Paper IDs and convert them to integers.
    df_all['Paper ID'] = df_all['Paper ID'].apply(lambda x: x.replace('pn', '')).astype(int)
    
    # Filter out submissions present in this batch of files.
    df = df_all[df_all['Paper ID'].isin(submissions)]
    
    # Split based on the primary subcommittee selection.
    subcommittees = df['Primary Subcommittee Selection'].unique()
    for SC in tqdm(subcommittees):
        # Filter rows belonging to the current subcommittee
        sc_df = df[df['Primary Subcommittee Selection'] == SC]
        
        # Create subdirectory for the current subcommittee if it doesn't exist
        sc_dir = os.path.join(output_dir, SC)
        os.makedirs(sc_dir, exist_ok=True)
        
        # Move files to their corresponding subdirectory
        for _, row in sc_df.iterrows():
            paper_id = row['Paper ID']
            filename = f"{paper_id}{FILE_ENDING}"
            src_path = os.path.join(input_dir, filename)
            dest_path = os.path.join(sc_dir, filename)
            
            if os.path.exists(src_path):
                # shutil.move(src_path, dest_path)
                shutil.copy2(src_path, dest_path)
            else:
                print(f"File {filename} not found in {input_dir}")

        # Zip the subcommittee folder
        zip_filename = os.path.join(output_dir, SC)
        shutil.make_archive(zip_filename, 'zip', sc_dir)

def importPaperIDs(submissions_f, paper_list, download_dir):
    """
    Remove 'DR's from the paper_list as to not download them. Also remove papers that have already been downloaded.

    Parameters:
    - submissions_f (str): Path to the CSV file containing submission data with 'Paper ID' and 'Decision' columns.
    - paper_list (str): Path to the CSV file containing the list of paper IDs to check.
    - download_dir (str): Directory where downloaded PDF files are stored.

    Returns:
    - List[int]: A list of Paper IDs that do NOT have 'DR' in the 'Decision' column.
    """
    # Read the submissions data
    df_submission = pd.read_csv(submissions_f, low_memory=False)
    
    # Clean up 'Paper ID' column (remove 'pn' and convert to integer)
    df_submission['Paper ID'] = df_submission['Paper ID'].apply(lambda x: x.replace('pn', '')).astype(int)
    
    # Read in the paper list
    paper_df = pd.read_csv(paper_list)
    
    # Ensure Paper ID column is of type integer in the paper list
    paper_df['Paper ID'] = paper_df['Paper ID'].astype(int)
    
    # Create a list of existing downloads
    downloads = [int(x.split("_doc")[0]) for x in os.listdir(download_dir) if x.endswith('.pdf')]
    
    # Store the original number of papers in the paper list for comparison
    original_count = len(paper_df)
    
    # Remove existing downloads from the paper list
    paper_df = paper_df[~paper_df['Paper ID'].isin(downloads)]
    
    # Filter the submissions to only include the Paper IDs from the updated paper list
    df_filtered = df_submission[df_submission['Paper ID'].isin(paper_df['Paper ID'])]
    
    # Identify papers that have 'DR' in their 'Decision' column
    dr_papers = df_filtered[df_filtered['Decision'].apply(lambda x: x.startswith('DR') if pd.notnull(x) else False)]
    
    # Filter out the 'DR' papers from the filtered DataFrame
    non_dr_papers = df_filtered[~df_filtered['Decision'].apply(lambda x: x.startswith('DR') if pd.notnull(x) else False)]
    
    # At the end, print the relevant stats
    total_papers = len(paper_df)  # Total number of papers in the paper list after filtering
    num_dr = len(dr_papers)  # Number of 'DR' papers
    num_non_dr = len(non_dr_papers)  # Number of non-'DR' papers
    
    # Calculate and print the number of papers excluded due to being already downloaded
    excluded_count = original_count - len(paper_df)
    
    # Print the stats
    global verbose
    if verbose:
        print(f"{'Number of entries in the original list:':45} {original_count}")
        print(f"{'Number of already downloaded (excluded):':45} {excluded_count}")
        print(f"{'Number of DR papers (excluded):':45} {num_dr}")
        print(f"{'=' * 50}")
        print(f"{'Number of papers remaining:':45} {num_non_dr}")
    
    # Return a list of Paper IDs that do NOT have 'DR' in the 'Decision' column
    return non_dr_papers['Paper ID'].tolist()

def clear_terminal():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Linux/MacOS
    else:
        os.system('clear')


if __name__ == "__main__":
    # Set globals
    global verbose
    verbose = True # Chatty output

    # Set paths
    download_dir = r"\your\preferred\download_folder\path" #TODO: Edit This
    failed_downloads_file = "failed.txt" #TODO: Edit This
    sorted_dir = "\sorted_download" #TODO: Edit This; a dir where you want the sorted files to be
    submissions_f = "submission.csv" #TODO: Edit This; the csv of all pdf submissions
    desired_f = "pull_papers.csv" #TODO: Edit This; the csv of Paper IDs that hit threshold

    # Set up Firefox
    service, options = setup(download_dir)

    # Initialize the WebDriver with the service object and options
    driver = webdriver.Firefox(service=service, options=options)

    # Read in documents 
    p_list = importPaperIDs(submissions_f, desired_f, download_dir)

    # Set up Firefox
    service, options = setup(download_dir)
    # Initialize the WebDriver with the service object and options
    driver = webdriver.Firefox(service=service, options=options)

    login()


    # Download
    for doc in tqdm(p_list):
        getDoc(doc)
    
    # Sort documents 
    sortPapers(download_dir, sorted_dir, submissions_f)