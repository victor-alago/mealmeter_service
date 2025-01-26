import requests
import os
from app.config import settings

class ApiNinjasService:
    def __init__(self):
        self.api_key = settings.api_ninjas_api_key
        self.base_url = 'https://api.api-ninjas.com/v1/nutrition'

    def search_foods(self, query: str):
        api_url = f'{self.base_url}?query={query}'
        response = requests.get(api_url, headers={'X-Api-Key': self.api_key})
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            raise Exception(f"API Ninjas API error: {response.status_code} - {response.text}")
