# Batch Grab Reports

This Python script automates the process of downloading reports from a specific website using Selenium WebDriver with Firefox. Users need to provide their own URLs and document IDs for the script to function correctly.

## Features

- Automatically logs into a website using credentials stored in a YAML file.
- Searches for documents by ID across multiple pages.
- Downloads PDF files directly to a specified directory.
- Handles download status checks to ensure complete downloads.
- Logs failed download attempts to a separate file.

## Requirements
- Python 3.x
- Selenium library
- Firefox web browser
- Geckodriver (compatible with your Firefox version)
- YAML library

## Installation

1. Clone the repository or download the script file.

2. Install required Python packages: `pip install selenium pyyaml`

3. Download Geckodriver:

    - Download Geckodriver from the official site.
    - Ensure that the location of `geckodriver.exe` is specified in the script.

4. Edit the YAML file for credentials:


## Usage
1. Edit the Script:
    - Update the `download_dir` variable in the script to specify where to save the downloaded PDFs.
    - Update the URL strings so that they point to a real website

2. Run the Script
 
