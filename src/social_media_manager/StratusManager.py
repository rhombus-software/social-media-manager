import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv
load_dotenv()
class StratusManager:
    def __init__(self, bucket_name: str, region_domain: str = "https://accounts.zoho.in"):
        self.bucket_name = bucket_name
        self.client_id = os.getenv("CATALYST_CLIENT_ID")
        self.client_secret = os.getenv("CATALYST_CLIENT_SECRET")
        self.refresh_token = os.getenv("CATALYST_REFRESH_TOKEN")
        self.accounts_domain = region_domain
        self.access_token = self._get_access_token()
        self.bucket_url = f"https://{self.bucket_name}-development.zohostratus.in"
    def _get_access_token(self) -> str:
        """Exchanges the persistent refresh token for a fresh short-lived access token."""
        url = f"{self.accounts_domain}/oauth/v2/token"
        payload = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        response = requests.post(url, data=payload)
        response_data = response.json()
        print(response_data)
        if "access_token" not in response_data:
            raise RuntimeError(f"Failed to generate access token: {response_data}")
            
        return response_data["access_token"]

    def upload_file(self, local_path: str, remote_key: str):
        """Uploads a file to Stratus using standard HTTP PUT."""
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")
            
        encoded_key = quote(remote_key)
        url = f"{self.bucket_url}/{encoded_key}"
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}"
        }
        
        # Read the file contents fully as raw binary bytes
        with open(local_path, "rb") as file_stream:
            binary_data = file_stream.read()
            
        response = requests.put(url, headers=headers, data=binary_data)

        if response.status_code in [200, 201]:
            print(f"Successfully uploaded {local_path} to Stratus key: {remote_key}")
            return True
        else:
            raise RuntimeError(f"Upload failed [{response.status_code}]: {response.text}")

    def download_file(self, remote_key: str, local_path: str):
        """Downloads an object from Stratus using standard HTTP GET."""
        # URL-encode the key to handle spaces and special characters safely
        encoded_key = quote(remote_key)
        url = f"{self.bucket_url}/{encoded_key}"
        print(f"Requesting URL: {url}")
        
        # Must use Zoho-oauthtoken instead of Bearer for Zoho resource servers
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(response.content)
            print(f"Successfully downloaded Stratus key {remote_key} to {local_path}")
            return local_path
        else:
            raise RuntimeError(f"Download failed [{response.status_code}]: {response.text}")