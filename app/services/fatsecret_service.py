import os
import requests
from dotenv import load_dotenv
from fastapi import Depends

load_dotenv()

class FatSecretService:
    def __init__(self):
        self.client_id = os.getenv("FATSECRET_CLIENT_ID")
        self.client_secret = os.getenv("FATSECRET_CLIENT_SECRET")
        self.base_url = "https://platform.fatsecret.com/rest/server.api"

    def _get_access_token(self):
        # Check if we have a valid cached token
        if hasattr(self, '_cached_token') and self._cached_token:
            return self._cached_token['access_token']

        # Get new token from FatSecret OAuth2 endpoint
        auth_url = "https://oauth.fatsecret.com/connect/token"
        auth_data = {
            "grant_type": "client_credentials",
            "scope": "basic"
        }
        auth = (self.client_id, self.client_secret)

        try:
            response = requests.post(
                auth_url,
                data=auth_data,
                auth=auth,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

            # Cache the token with expiration time
            self._cached_token = response.json()
            return self._cached_token['access_token']

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get access token: {str(e)}")

    def search_foods(self, query: str):
        params = {
            "method": "foods.search",
            "search_expression": query,
            "format": "json"
        }

        headers = {
            "Authorization": f"Bearer {self._get_access_token()}"
        }

        response = requests.get(
            self.base_url,
            params=params,
            headers=headers,
        )
        print(f"FatSecret API Response Status Code: {response.status_code}")
        print(f"FatSecret API Response Content: {response.content}")
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        
        try:
            response_json = response.json()
            foods = response_json.get("foods", {}).get("food", [])
            return foods
        except ValueError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Response text: {response.text}")
            return []
