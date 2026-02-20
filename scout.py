import json
import os, re
from firecrawl import FirecrawlApp
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class SDRScout:
    def __init__(self):
        self.firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        self.ai = OpenAI(api_key=os.getenv("OLLAMA_API_KEY"), base_url=os.getenv("OLLAMA_BASE_URL"))
        self.model = os.getenv("OLLAMA_MODEL")

    def _extract_socials(self, markdown):
        """Finds X and LinkedIn links directly in the page markdown."""
        if not markdown:
            return {"x_from_site": "", "li_from_site": ""}
            
        x_match = re.search(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+', markdown, re.IGNORECASE)
        li_match = re.search(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9_-]+', markdown, re.IGNORECASE)
        
        return {
            "x_from_site": x_match.group(0) if x_match else "",
            "li_from_site": li_match.group(0) if li_match else ""
        }

    def scrape_website(self, url: str) -> dict:
        print(f"[*] Intelligence Gathering: Accessing {url}...")
        try:
            # Main Scrape
            scrape_result = self.firecrawl.scrape(url)
            main_content = scrape_result.get('markdown', "") if isinstance(scrape_result, dict) else scrape_result.markdown
            
            # Find About/Team links
            about_link = None
            links = re.findall(r'\[([^\]]*? (?:About|Team|Leadership|Who we are|Staff)[^\]]*?)\]\((.*?)\)', main_content, re.IGNORECASE)
            
            if links:
                potential_path = links[0][1]
                if potential_path.startswith('/'):
                    base_url = "/".join(url.split('/')[:3])
                    about_link = base_url + potential_path
                elif potential_path.startswith('http'):
                    about_link = potential_path

            about_content = ""
            if about_link:
                print(f"[*] Scout: Found leadership page at {about_link}. Scraping...")
                about_scrape = self.firecrawl.scrape(about_link)
                about_content = about_scrape.get('markdown', "") if isinstance(about_scrape, dict) else about_scrape.markdown

            # HERE IS THE FIX: Extract socials and include them in the return dict
            combined_content = (main_content or "") + "\n" + (about_content or "")
            socials = self._extract_socials(combined_content)

            return {
                "main_md": main_content,
                "about_md": about_content,
                "found_socials": socials  # This key was missing!
            }
            
        except Exception as e:
            print(f"[!] Scraping failed: {e}")
            # Ensure we return empty structure on failure so main.py doesn't crash
            return {
                "main_md": "", 
                "about_md": "", 
                "found_socials": {"x_from_site": "", "li_from_site": ""}
            }

    def analyze_business_model(self, markdown_content: str, fallback_name: str) -> str:
        print(f"[*] Gatekeeper: Verifying business type...")
        
        system_prompt = f"""
            You are a Lead Qualification Specialist. 
            Analyze the website content and determine if this is a REAL individual business providing services.
            
            QUALIFICATION RULES:
            1. If directory, 'Top 10' list, blog, or portal -> "is_qualified_business": false.
            2. If single business selling services -> "is_qualified_business": true.
            
            JSON Output Format:
            {{
                "is_qualified_business": true/false,
                "reason_for_disqualification": "only if false",
                "company_name": "Exact Name",
                "core_business": "Short description",
                "operational_pain_points": ["point 1", "point 2"],
                "krykos_automation_hypothesis": "pitch"
            }}
            """
        try:
            content = markdown_content[:6000] if markdown_content else "No content"
            response = self.ai.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": content}],
                response_format={'type': 'json_object'}
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"is_qualified_business": False, "company_name": fallback_name})