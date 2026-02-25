import json
import os
from urllib.parse import urlparse

DB_FILE = "history_db.json"

class HistoryDB:
    def __init__(self):
        self.processed_domains = self._load_db()

    def _load_db(self):
        if not os.path.exists(DB_FILE):
            return []
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                # Ensure we return a list
                return data if isinstance(data, list) else []
        except:
            return []

    def _get_domain(self, url):
        try:
            return urlparse(url).netloc.replace("www.", "").lower()
        except:
            return ""

    def exists(self, url):
        """Checks if a domain has already been processed."""
        domain = self._get_domain(url)
        return domain in self.processed_domains

    def add(self, url):
        """Adds a url to the history."""
        domain = self._get_domain(url)
        if domain and domain not in self.processed_domains:
            self.processed_domains.append(domain)
            self._save()

    def _save(self):
        with open(DB_FILE, 'w') as f:
            json.dump(self.processed_domains, f, indent=2)