import os
import time
from ddgs import DDGS
from urllib.parse import urlparse

class LeadDiscoverer:
    def __init__(self):
        self.blacklist_domains = [
            'clutch.co', 'yelp.com', 'linkedin.com', 'facebook.com', 
            'instagram.com', 'twitter.com', 'glassdoor.com', 'upwork.com',
            'expert.com', 'wikipedia.org', 'crunchbase.com',
            'yellowpages.com', 'bbb.org', 'angis.com', 'houzz.com', 'thumbtack.com',
            'expertise.com', 'upcity.com', 'designrush.com', 
            'goodfirms.co', 'sortlist.com', 'topagencies', 'bestagencies', 
            'agencies.com', 'directory', 'listing', 'review',
            'builtinaustin.com', 'nogood.io', 'writingstudio.com',
            'medium.com', 'hubspot.com', 'wordpress.com',
            'zhihu.com', 'quora.com', 'reddit.com', 'stackoverflow.com',
            'youtube.com', 'vimeo.com', 'slideshare.net', 'issuu.com'
        ]
        
        self.path_blacklist = [
            '/blog/', '/articles/', '/news/', '/post/', 
            '/list/', '/top-', '/best-', '/directory/', '/review/',
            '/question/', '/answer/', '/topic/'
        ]

    def is_blacklisted(self, url):
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        for b in self.blacklist_domains:
            if b in domain:
                return True
        
        for p in self.path_blacklist:
            if p in path:
                return True
        
        return False

    def find_companies(self, niche_query, count=3):
        print(f"[*] Discoverer: Searching via Stable HTML for '{niche_query}'...")
        companies = []
        
        try:
            with DDGS() as ddgs:
                search_query = f"{niche_query} official website -zhihu.com -quora.com -reddit.com -youtube.com"
                
                search_results = ddgs.text(
                    search_query, 
                    region='us-en', 
                    safesearch='off', 
                    backend='html', 
                    max_results=count + 10
                )
                
                if not search_results:
                    print("[!] No results returned from search engine.")
                    return []

                for r in search_results:
                    url = r.get('href')
                    title = r.get('title', '')
                    if not url:
                        continue
                    
                    if self.is_blacklisted(url):
                        continue
                    
                    if url in [c['url'] for c in companies]:
                        continue

                    companies.append({
                        "name": title,
                        "url": url
                    })
                    
                    if len(companies) >= count:
                        break
                        
        except Exception as e:
            print(f"[!] Discoverer Search Error: {e}")
        
        print(f"[+] Discoverer: Found {len(companies)} potential targets.")
        return companies