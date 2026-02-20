import os
import time
from duckduckgo_search import DDGS
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
            'youtube.com', 'vimeo.com', 'slideshare.net', 'issuu.com', 'clutch.co', 'expertise.com', 'yelp.com', 'linkedin.com', 'facebook.com', 
            'instagram.com', 'twitter.com', 'glassdoor.com', 'upwork.com', 'bbb.org',
            'yellowpages.com', 'angis.com', 'houzz.com', 'thumbtack.com', 'zillow.com', 'realtor.com'
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
        # SIMPLIFIED QUERY: Just the niche + "official website"
        # We removed the hard quotes and multiple -site operators to get more results
        search_query = f'{niche_query} official website'
        
        print(f"[*] Discoverer: Searching for '{niche_query}'...")
        potential_leads = []
        
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    search_query, 
                    region='us-en', 
                    backend='html', 
                    max_results=40 # Grab a decent pool
                )
                
                if not search_results:
                    print("[!] DuckDuckGo returned zero raw results. Try a broader niche.")
                    return []

                for r in search_results:
                    url = r.get('href', '').lower()
                    title = r.get('title', '').lower()
                    domain = urlparse(url).netloc
                    
                    # DEBUG: Let's see what's being rejected
                    
                    # 1. Filter Directories
                    if any(b in domain for b in self.blacklist_domains):
                        # print(f"   [x] Skipping directory: {domain}")
                        continue
                    
                    # 2. Filter Listicles/Blogs based on Title
                    if any(x in title for x in ['top ', 'best ', '10 ', '20 ', 'reviews']):
                        # print(f"   [x] Skipping listicle title: {title[:30]}")
                        continue
                        
                    # 3. Filter specific path garbage but be careful
                    if any(x in url for x in ['/directory/', '/category/', '/tags/']):
                        continue

                    potential_leads.append({
                        "name": r.get('title', 'Unknown'),
                        "url": url
                    })
                        
        except Exception as e:
            print(f"[!] Discoverer Search Error: {e}")
        
        print(f"[+] Discoverer: Found {len(potential_leads)} potential leads to audit.")
        return potential_leads