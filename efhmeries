## DOKIMI ME PYTHONANYWHERE 1/1/24 
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import re
from datetime import datetime

def extract_date_from_text(text):
    date_pattern = r'\d{2}/\d{2}/\d{4}'
    match = re.search(date_pattern, text)
    return match.group() if match else None

def extract_date_from_url(url):
    date_pattern = r'\d{2}-\d{2}-\d{4}'
    match = re.search(date_pattern, url)
    return match.group() if match else None

def compare_dates(url_date, text_date):
    if url_date and text_date:
        # Compare dates, if both are present
        if url_date == text_date:
            return url_date
        else:
            # Handle the case where dates don't match
            print("Warning: Dates from URL and text content do not match.")
            return text_date  # Prefer text content date
    return url_date or text_date  # Return whichever date is available

def string_to_datetime(date_str):
    for fmt in ("%d-%m-%Y", "%d/%m/%Y"):  # Add more formats if needed
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None  # If no format matched

def extract_pdf_urls(base_url, page_url):
    # Sends a GET request to the page URL
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all PDF links
    pdf_links = []
    for link in soup.select('div.webpage-body a[href$=".pdf"]'):
        href = link.get('href')
        if href:
            full_url = base_url + href
            pdf_links.append(full_url)
    return pdf_links

def download_pdf(url):
    response = requests.get(url)
    return io.BytesIO(response.content)

def pdf_to_text(pdf_file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:  # Check if text was extracted
            text += page_text
    return text

def categorize_pharmacies(text, weekday=True):
    # Define a regex pattern for phone numbers
    phone_pattern = r'\b2410?\s?\d{6,7}(?: & 2410?\s?\d{6,7})?\b'

    # Find all matches
    matches = re.findall(phone_pattern, text)

    # Initialize variables for start and end phrases
    start_phrase = "ΕΦΗΜΕΡΕΥΟΥΝ"
    end_phrase = "ΑΝΟΙΚΤΑ"

    # Process matches to categorize pharmacies
    categorized_pharmacies = []
    if weekday:
        # Weekday logic
        for index, match in enumerate(matches):
            number = match.split(' & ')[0].replace(" ", "")
            tag = 'overnight' if index == 0 else 'on-duty'
            categorized_pharmacies.append((number, tag))
    else:
        # Non-weekday logic
        start_index = text.find(start_phrase)
        end_index = text.find(end_phrase, start_index)
        relevant_text = text[start_index:end_index]

        on_duty_phones = re.findall(phone_pattern, relevant_text)

        for phone in on_duty_phones:
            number = phone.split(' & ')[0].replace(" ", "")
            categorized_pharmacies.append((number, 'on-duty'))

        epikouriko_phones = re.findall(phone_pattern, text[end_index:])
        for index, phone in enumerate(epikouriko_phones):
            number = phone.split(' & ')[0].replace(" ", "")
            tag = 'overnight' if index == len(epikouriko_phones) - 1 else 'epikouriko'
            categorized_pharmacies.append((number, tag))

    return categorized_pharmacies


def determine_day(phone_count):
    if phone_count >= 12:  # Change the threshold to 12
        return "Saturday"
    else:
        return "Weekday"
    

def fetch_pharmacy_data():
    base_url = 'https://www.fslarisas.gr'
    page_url = base_url + '/9FA8ACB4.el.aspx'
    pdf_urls = extract_pdf_urls(base_url, page_url)

    all_pharmacy_data = []  # List to hold all data

    for pdf_url in pdf_urls:
        try:
            pdf_file = download_pdf(pdf_url)
            text_content = pdf_to_text(pdf_file)

            url_date = extract_date_from_url(pdf_url)
            text_date = extract_date_from_text(text_content)
            final_date = compare_dates(url_date, text_date)

            phone_count = len(re.findall(r'\b2410?\s?\d{6,7}(?: & 2410?\s?\d{6,7})?\b', text_content))
            day_type = determine_day(phone_count)
            weekday = day_type == "Weekday"

            categorized_pharmacies = categorize_pharmacies(text_content, weekday)

            # Structure the data in a dictionary
            day_data = {
                'date': final_date,
                'pharmacies': categorized_pharmacies
            }
            all_pharmacy_data.append(day_data)

        except Exception as e:
            print(f"Error processing {pdf_url}: {e}")

    return all_pharmacy_data

# Example usage of the function
pharmacy_data = fetch_pharmacy_data()
print(pharmacy_data)
