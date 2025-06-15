import requests

def download_credentials():
    # Publicly share the file and use its direct download link here
    url = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"
    response = requests.get(url)

    if response.status_code == 200:
        with open("credentials.json", "wb") as f:
            f.write(response.content)
        print("✅ credentials.json downloaded.")
    else:
        print("❌ Failed to download credentials.json")
