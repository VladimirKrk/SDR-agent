import os, json, time
from ddgs import DDGS
from openai import OpenAI

class IdentityHunter:
    def __init__(self):
        self.ai = OpenAI(api_key=os.getenv("OLLAMA_API_KEY", "ollama"), base_url=os.getenv("OLLAMA_BASE_URL"))
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def _clean_url(self, url):
        if not url or "null" in url or "home.x.com" in url or "login" in url:
            return ""
        return url

    def find_decision_maker(self, company_name, site_context):
        print(f"[*] Identity Hunter: Looking for names inside {company_name}'s website...")
        
        extract_prompt = f"""
        Analyze this website text from {company_name}. Find the Full Name and Title of the Founder, CEO, or Owner.
        Text: {site_context[:5000]}
        Return JSON: {{"name": "Name or null", "title": "Title or null"}}
        """
        
        name_on_site = "null"
        try:
            res = self.ai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extract_prompt}],
                response_format={'type': 'json_object'}
            )
            data = json.loads(res.choices[0].message.content)
            name_on_site = data.get("name")
        except: 
            pass

        if name_on_site and name_on_site != "null":
            print(f"[*] Hunter: Verifying socials for {name_on_site}...")
            query = f'"{name_on_site}" {company_name} LinkedIn X'
        else:
            print(f"[*] Hunter: No name on site. Searching web for {company_name} leadership...")
            query = f"{company_name} Founder CEO owner LinkedIn -NHL -Sports -Hockey"

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region='us-en', backend='html', max_results=5))
                search_text = "\n".join([f"{r['href']} - {r['body']}" for r in results])
                
                final_prompt = f"""
                Identify the Founder/CEO LinkedIn and X.com URLs. 
                Company: {company_name}
                Context: {search_text}
                Return JSON: {{"full_name": "Name", "linkedin_url": "URL", "x_url": "URL"}}
                """
                res = self.ai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": final_prompt}],
                    response_format={'type': 'json_object'}
                )
                data = json.loads(res.choices[0].message.content)
                data['linkedin_url'] = self._clean_url(data.get('linkedin_url', ''))
                data['x_url'] = self._clean_url(data.get('x_url', ''))
                return data
        except Exception as e:
            return {"error": str(e)}