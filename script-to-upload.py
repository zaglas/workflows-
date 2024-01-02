import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    creds = Credentials(None,
                        refresh_token=os.environ['REFRESH_TOKEN'],
                        token_uri='https://oauth2.googleapis.com/token',
                        client_id=os.environ['CLIENT_ID'],
                        client_secret=os.environ['CLIENT_SECRET'])

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': 'myfile.txt'}
    media = MediaFileUpload(os.environ['FILE_PATH'],
                            mimetype='text/plain')

    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    print('File ID: %s' % file.get('id'))

if __name__ == '__main__':
    main()
