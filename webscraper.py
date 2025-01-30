import os
import pandas as pd
from bs4 import BeautifulSoup
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta

def push_to_github():
    # Change to the directory containing your CSV files
    os.chdir('FX Forward Outputs')

    # Add all changes
    subprocess.run(['git', 'add', '.'])

    # Commit changes with a timestamp
    commit_message = f"Update FX Forward Outputs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(['git', 'commit', '-m', commit_message])

    # Push to GitHub
    subprocess.run(['git', 'push', 'origin', 'main'])  # Replace 'main' with your branch name if different

    # Change back to the original directory
    os.chdir('..')

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode which is important as we are running this script on a server
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Define currency pairs and their URLs
currency_pairs = {
    "EUR-USD": "https://www.fxempire.com/currencies/eur-usd/forward-rates",
    "GBP-USD": "https://www.fxempire.com/currencies/gbp-usd/forward-rates",
    "USD-CAD": "https://www.fxempire.com/currencies/usd-cad/forward-rates",
    "GBP-EUR": "https://www.fxempire.com/currencies/gbp-eur/forward-rates"
}

# Date offsets for expiration dates
date_offsets = {
    "Overnight": 1,
    "Tomorrow Next": 2,
    "Spot Next": 3,
    "One Week": 7,
    "Two Week": 14,
    "Three Week": 21,
    "One Month": 30,
    "Two Month": 60,
    "Three Month": 90,
    "Four Month": 120,
    "Five Month": 150,
    "Six Month": 180,
    "Seven Month": 210,
    "Eight Month": 240,
    "Nine Month": 270,
    "Ten Month": 300,
    "Eleven Month": 330,
    "One Year": 365,
    "Two Year": 730,
    "Three Year": 1095,
    "Four Year": 1460,
    "Five Year": 1825,
    "Six Year": 2190,
    "Seven Year": 2555,
    "Ten Year": 3650
}

# Get the current datetime for the filename
current_datetime = datetime.now().strftime('%Y_%m_%d_%H_%M')

# Create the output directory if it doesn't exist
output_dir = 'FX Forward Outputs'
os.makedirs(output_dir, exist_ok=True)

# Loop through each currency pair (EUR-USD, GBP-USD, USD-CAD)
for pair, url in currency_pairs.items():
    # Fetch the webpage content
    driver.get(url)

    # Wait for the table to be present
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
    except TimeoutException:
        raise ValueError(f"No tables found on the webpage for {pair}")

    # Get the page source after the table is loaded
    html_content = driver.page_source

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the table data
    tables = soup.find_all('table')
    if not tables:
        raise ValueError(f"No tables found on the webpage for {pair}")

    table = tables[0]  # Assuming the first table is the required one
    rows = table.find_all('tr')

    # Extract headers
    headers = [header.text for header in rows[0].find_all('th')]

    # Extract rows data
    data = []
    for row in rows[1:]:
        cols = row.find_all('td')
        cols = [col.text.strip().replace(',', '') for col in cols]
        data.append(cols)

    # Create df
    df = pd.DataFrame(data, columns=headers)

    # Change column types
    df = df.astype({
        "Expiration": str,
        "Bid": float,
        "Ask": float,
        "Mid": float,
        "Points": float
    })

    # Add dates to the df
    start_date = datetime.today()
    df['Date'] = df['Expiration'].apply(lambda x: (start_date + timedelta(days=date_offsets.get(x, 0))).strftime('%Y-%m-%d'))

    # Save to CSV with datetime in filename
    output_path = os.path.join(output_dir, f'{current_datetime}_{pair}_forward_rates.csv')
    df.to_csv(output_path, index=False)

    print(f"Data for {pair} saved to {output_path}")

# Close the WebDriver
driver.quit()

# Push the generated CSV files to GitHub
push_to_github()
