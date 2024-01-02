y## DOKIMI ME PYTHONANYWHERE 1/1/24 
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import re
from datetime import datetime
from googleapiclient.http import MediaFileUpload

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

with open('pharmacy_data.json', 'w') as file:
    json.dump(pharmacy_data, file)
    
service_account_json_string = r'''
{
  "type": "service_account",
  "project_id": "efhmeries",
  "private_key_id": "67618972745a9a092f8e32587f6fabb5d29cf2c4",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCkC005cIPCKR48\ntYwX4CZbP5l+FSdrt0FKlD1HYez6OwnKHWO3OdxHKTRjmLNt/XtOvaKTdFmxfX9L\nVheh3eG7bt4GlcAc/li685jcGlReHhuUitXDiWDOADWvmKLtEvP/oKB6A/Y5caAq\nkn3Ce7sqRxjp/0L/9eDiNyZ72UucAYvekZJPpw4kw3W3ac8TnQgwVCUxHlsK6DRb\n9ifP+PB+BIdzOoU0lXmxAn3Bda/wkJFYpLKz/Qcze8DyDisJ7mjrt1xJEhRCstyj\nIa86wrfP/jyYBWfAlKjJ8WNNrj652TCU440WUpooT+7ZO1I+0zDU+vKGa8X6kOlm\njrg1tk7XAgMBAAECggEAJS2eiecTJXz2KmIm5v5ZExMd8XJP5dy5gnKIVNY/xBJ/\nTHxOricB4mrXQb9I4yOwv47A+tRCw7Qilmtjnb7Quw8MaMelq6yFZZFx0mhxOIdw\nTsEMY22OMAHiKPLZ8gr6m7PGywB83FYBK8TZlas/JvzIC7hbcfFCz2IaabU8qpVe\nJx2IgdhqoXD/OKhrZfG80C6r4oCuJzkln2C9EWJGunxfaw+V95W/P6YIHFMBaknA\n8UEWUwMLy70seJqK9gS3XHDXdwgBglOZLp52al7yRXD3qaVgfuXg5ITz6bz1qguJ\n2pqxlZUtQ26Y4Jkyhx3L180NvVNQ6a83Yo1direZwQKBgQDWW8D/hXpf8fGEQv6n\nlXxQO0w+Ol/ICwW5xrTI192L0jK+rYn3eqpoKKZhYwx8ORbPd1StXiamOJ1Bp78r\niaVEnL27NJmd47rAY87pdO/h7FXNmltJh+ZllalXsqjpv/VOPY2WcUZgRJ8c/JZz\nRiCF2uQm67cqQTkKEiVJ9aTwIQKBgQDD6V8v4q9RYywbuOs/g0dmPqK6bJMGnhFP\ngJVr0yXjRUQcB6IGBxHRIjv0EN24EEmhs3/6O9/PXDvBW6ohSlgLR5yt7DM8KSQA\nJk2rk9n1wE28+KX2Ouo2If9E77f4xAaHhkJCi6Egfaz89vYicX8ZiGesLWWCmDJv\nffia3yq/9wKBgQCrpfeK5ViUAcpzLa57hZFxMbqgzd+q8WCZXcugVHM8poop9A7Z\nlGlmVL6+lzEFPDXO1fCBjzYFvqn2TBwiAevMYHLxuHIWY6hErOegPBpm3/fpVuQo\nomFVER30csUdwK/vAg0h3f0L04dSD9Vt40bhyOEPZYtbk7TYIqWnbsOv4QKBgQDC\nODrokxdxXRreRN3bcj83asMShA7iEZRht7zqT0KRZBrYmuySgzGznffHx2y3TFZi\n2zv1jKQdw3duAnzQUg6k6BK5DZ/hdXu+Njrr7UC4dDPdMrf9Onz0u5GA+xHsqhE7\nC+vmYtyTBGSZyA9NKC1z15nHxJ2M8WuWwlDS4IlWEwKBgGpixJwMswHqjHmk5zqK\n75m8xyGUAbCsYgzQ7qzjAzug5zyGbrYymE6QsVH8H8krmTA2iY/jgnq4CvasQxB/\n5KuYgAOs78L55Kyn8u9GJ/iEJiX7IT3IrT7aDvDownehlPZma2kJgY9CZeKB8thx\nBSGYGVwtwyi8Se7KBZ5KuVBZ\n-----END PRIVATE KEY-----\n",
  "client_email": "efhmeries@efhmeries.iam.gserviceaccount.com",
  "client_id": "111010436983476497507",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/efhmeries%40efhmeries.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
'''


# Authenticate using the service account
service_account_info = json.loads(service_account_json_string)
credentials = service_account.Credentials.from_service_account_info(service_account_info)

# Build the Google Drive service
service = build('drive', 'v3', credentials=credentials)

# File metadata
file_metadata = {'name': 'pharmacy_data.json', 'mimeType': 'application/json'}

# Upload the file
media = MediaFileUpload('pharmacy_data.json', mimetype='application/json')
file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
