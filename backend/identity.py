import os, json, time, random
from duckduckgo_search import DDGS
from openai import OpenAI
import requests

class IdentityHunter:
    def __init__(self):
        self.ai = OpenAI(api_key=os.getenv("OLLAMA_API_KEY", "ollama"), base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"))
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    def validate_url(self, url):
        """IMPROVEMENT 2: Mandatory URL Validation"""
        if not url or "http" not in url: return ""
        try:
            # We use a real User-Agent to avoid being blocked by X during a ping
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=5)
            # If 404 or "This account doesn't exist" in text, it's garbage
            if response.status_code == 404 or "account doesn't exist" in response.text.lower():
                return ""
            return url
        except:
            return url # Fallback if request fails but we aren't sure

    def find_decision_maker(self, company_name, site_context, site_socials):
        # Priority 1: Use what we found directly on the site
        if site_socials.get("x_from_site") or site_socials.get("li_from_site"):
            print(f"   [+] Found socials directly on website footer.")

        # Step 1: Extract name
        extract_prompt = f"Analyze site text for {company_name}. Find the Founder/CEO. If not found, return 'Unknown'. Text: {site_context[:4000]}"
        try:
            res = self.ai.chat.completions.create(model=self.model, messages=[{"role": "user", "content": extract_prompt}], response_format={'type': 'json_object'})
            full_name = json.loads(res.choices[0].message.content).get("name", "Unknown")
        except: full_name = "Unknown"

        # Step 2: Formulate Search Query
        # If we have a name, search for person. If not, search for company profile.
        if full_name != "Unknown" and full_name is not None:
            query = f'site:x.com "{full_name}" {company_name}'
        else:
            query = f'site:x.com {company_name} official profile'

        # Step 3: Search and Merge
        try:
            time.sleep(random.uniform(2, 4))
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region='us-en', backend='html', max_results=3))
                search_text = "\n".join([f"{r['href']} - {r['body']}" for r in results])
                
                final_res = self.ai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": f"Find X and LinkedIn links for {full_name} at {company_name}. Results: {search_text}"}],
                    response_format={'type': 'json_object'}
                )
                data = json.loads(final_res.choices[0].message.content)
                
                # Combine site footer links with search links (Footer links are usually more reliable)
                return {
                    "full_name": full_name,
                    "x_url": site_socials.get("x_from_site") or data.get("x_url", ""),
                    "linkedin_url": site_socials.get("li_from_site") or data.get("linkedin_url", ""),
                    "found_via": "footer" if site_socials.get("x_from_site") else "search"
                }
        except:
            return {"full_name": full_name, "x_url": site_socials.get("x_from_site"), "linkedin_url": site_socials.get("li_from_site")}