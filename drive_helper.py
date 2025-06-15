# drive_helper.py
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def authenticate():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("credentials.json")
    return GoogleDrive(gauth)

def read_chat_ids_file(drive):
    file_list = drive.ListFile({'q': "title = 'chat_ids.txt' and trashed = false"}).GetList()
    if not file_list:
        return set(), None
    
    file = file_list[0]
    content = file.GetContentString()
    chat_ids = set(content.strip().splitlines())
    return chat_ids, file['id']

def write_chat_ids_file(drive, chat_ids, file_id=None):
    content = "\n".join(chat_ids)
    if file_id:
        file = drive.CreateFile({'id': file_id})
    else:
        file = drive.CreateFile({'title': 'chat_ids.txt'})
    file.SetContentString(content)
    file.Upload()
