## DOKIMI ME PYTHONANYWHERE 1/1/24 
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
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

with open('pharmacy_data.json', 'w') as file:
    json.dump(pharmacy_data, file)
    
service_account_json_string = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "some_private_key_id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCixeH/LAcVIqTU\nQJZ5ZbqpbYn1WsNmhdM2JFUao+9qrnFWxrgQP3fSJY9W0okPofvUUeUHQtEiNK3n\n03IIl/4JDxgTRUsP+07m1onnhPcrMRfk1y3N/D+7sUdJYIvvuG5W+7HfqbaAyX6j\nkZQeXi4V2x8tbIWhwTq18PtsWXca/JWpDS86XiVQv4rMyEqgt6Un2zJOvqQURtAt\nqIe1YhyJQnWsvHPkswBzf/us0D9TZCg91JeS3uRTU2uDhsdrIU/8Vs7Au9MTfvfC\naZVC1erf/1gI32/tCTegNs3TuH5q/ikc1XNup17GDmF9bMxwhwkYzHY6/02sMTLH\nln9yGkxfAgMBAAECggEATsFJqGnH/3zknWGmrJQA7Yr3TgQdONSVLcQEfUBGTaqb\nYe4CDrJ2qfHMWajB8hNgwgjhtFKq107/uYP/z5KisgVgk6paOCBSu7Ofw6n84SP+\nuJU4L0rWF10d7a3N5y2oDWP4WwxFJijXohKExPCygZakjhjMy0evvWoca/8Zdq9r\nGZx14tFXbbQo3/wmw4O4vs1Pa4bnR4jvLHV4Z9aVfuvXolD0LYyqDSDM+jlKmraL\nxqpuYjdgTzN9LbjljNu+Z/EiXnS2nFOSnGX6jIMU18z6nuq9U5tXO1Y7Lgw3wrrL\nXdI9yZR4UKu7z+Qhjk8cPzH33n9//jCuNcCVVEgcYQKBgQDdN/w0mHLKhiOTEVNh\nMaxxKEQGsQTmu1brgpji4WIA3SXNWuhI8lPWGW9Kc0p2ejuTOieLbapFtROWOSYV\n/SCEGkSeJCm8oH0W4QAZuxLroUENdy9wKnqFzqoJf7KFeJEQbYSpPD3/ew+UrPDv\noVUyZy41g5hfB/YNcy9F+2Ek7wKBgQC8XXe1kfsH/4io1F78icVbnlZxqZMgRHgg\nXjJs3Fcg9uKc+7iVwQc9tqsiyxN5dEm8VIeR+zGD4eXsrXIti1j9ARnVOUybeYFE\n94dILe6IvIEfqOM5EgTHGDiIY4+7EI06VHHBuraJ74PYmLaPjR/g/jeO8792GY58\nBtHAp3uvkQKBgQDF/fWcnVUgLi5o0njt5KeSH5fC5Wydlc6Vuq1bYp10aHoM8fA0\nWa7vUJRq7gUXRQ9NFh+Oivh6qzZ8nWmZBJS1p00CvRsd2AYdFAQjA2xLuGegxauP\nmHVQjUdieQgurVooedziGyjiICIxzxdVYe/+zJpvCvi1FUsDfrQwzmyDwQKBgQCf\nlIfwWYZU1lYOwizewlFjNxeBH+q3MYqb0XHi7CEcmkyONmvA41GhJPqDdYxAHxbA\n6NQaBreCRYUnKCJNF3sCjUY3cF3Icf3kUdhYfCFT0m+KROiL1woZKhnq4n5IOtOL\nETN2rxoqbbJDc81mfGb/lB+5iiMwiKI/zP8yujF9IQKBgQC7O9ohDKOSabj3j7Ki\nk1d1n8/DQ8VpcfMQjsY9giZxX0BCudPwnYmhSrjQDE56yu1Odb5tqbQHlYz3vR90\nPt5OuwEb9+s1j5GDoZOrGuOtSO0Wczo8UTPCWAdXcFrtXDf+9LSYCbEwmYxEMKwE\nd8S3RZdn7DosuOT4GgZCzB67aw==\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account-email@your-project-id.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-email%40your-project-id.iam.gserviceaccount.com"
}
"""


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

