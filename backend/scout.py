import json
import os, re
from firecrawl import FirecrawlApp
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class SDRScout:
    def __init__(self):
        self.firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        self.ai = OpenAI(
            api_key=os.getenv("OLLAMA_API_KEY"), 
            base_url=os.getenv("OLLAMA_BASE_URL")
        )
        self.model = os.getenv("OLLAMA_MODEL")

    def _extract_socials(self, markdown):
        if not markdown: return {"x_from_site": "", "li_from_site": ""}
        x_match = re.search(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+', markdown, re.IGNORECASE)
        li_match = re.search(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9_-]+', markdown, re.IGNORECASE)
        return {
            "x_from_site": x_match.group(0) if x_match else "",
            "li_from_site": li_match.group(0) if li_match else ""
        }

    def _detect_technical_signals(self, markdown):
        """
        Hard-coded logic to find specific triggers for Email Templates.
        """
        signals = []
        md_lower = markdown.lower()
        
        # Trigger for Template 1 (Manual Data Entry)
        if "contact us" in md_lower or "send message" in md_lower or "get in touch" in md_lower:
            signals.append("Has Generic Contact Form (Risk: Manual CRM Entry)")
            
        # Trigger for Template 2 (Speed/Scheduling)
        # If they ask to book but don't have a link like calendly/hubspot
        if ("book a call" in md_lower or "schedule" in md_lower) and not ("calendly" in md_lower or "hubspot" in md_lower):
            signals.append("Manual Scheduling Friction (No Auto-Booking detected)")
            
        # Trigger for Template 3 (Hiring/Scaling)
        if "careers" in md_lower or "we are hiring" in md_lower or "join the team" in md_lower:
            signals.append("Active Hiring (Growing Pains)")
            
        return signals

    def scrape_website(self, url: str) -> dict:
        print(f"[*] Intelligence Gathering: Accessing {url}...")
        try:
            scrape_result = self.firecrawl.scrape(url)
            main_content = scrape_result.get('markdown', "") if isinstance(scrape_result, dict) else scrape_result.markdown
            
            # Find About/Team links
            about_link = None
            links = re.findall(r'\[([^\]]*?(?:About|Team|Leadership|Who we are|Staff)[^\]]*?)\]\((.*?)\)', main_content, re.IGNORECASE)
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

            combined_content = (main_content or "") + "\n" + (about_content or "")
            socials = self._extract_socials(combined_content)

            return {
                "main_md": main_content,
                "about_md": about_content,
                "found_socials": socials
            }
        except Exception as e:
            print(f"[!] Scraping failed: {e}")
            return {"main_md": "", "about_md": "", "found_socials": {"x_from_site": "", "li_from_site": ""}}

    def analyze_business_model(self, markdown_content: str, fallback_name: str) -> str:
        print(f"[*] Analysis Engine: Detecting specific friction points...")
        
        # 1. Run Technical Signal Detector
        signals = self._detect_technical_signals(markdown_content)
        signals_str = ", ".join(signals) if signals else "No obvious technical triggers found."
        
        # 2. Refined Prompt
        system_prompt = f"""
            You are an Operations Audit Bot. Your ONLY goal is to find ONE high-friction manual process to sell automation against.
            
            TECHNICAL SIGNALS DETECTED ON PAGE:
            {signals_str}
            
            INSTRUCTIONS:
            1. If "Has Generic Contact Form" is detected -> Your Pain Point MUST be "Manual data entry from contact forms into CRM".
            2. If "Manual Scheduling Friction" is detected -> Your Pain Point MUST be "Back-and-forth email tagging to book meetings".
            3. If neither, look for "Client Portal" (Pain: Manual onboarding) or "Careers" (Pain: Resume filtering).
            4. Do NOT use generic phrases like "Operational inefficiency". Be specific.
            
            OUTPUT FORMAT (JSON):
            {{
                "is_qualified_business": true/false,
                "reason_for_disqualification": "only if false",
                "company_name": "Name",
                "core_business": "1 sentence description",
                "operational_pain_points": [
                    "PRIMARY SPECIFIC PAIN POINT (Based on signals above)",
                    "Secondary pain point"
                ],
                "krykos_automation_hypothesis": "1 sentence pitching the solution to the PRIMARY pain point."
            }}
            """
        
        try:
            content = markdown_content[:5000] if markdown_content else "No content"
            response = self.ai.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": content}],
                response_format={'type': 'json_object'},
                temperature=0.2 # Low temp = strict adherence to signals
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"is_qualified_business": False, "company_name": fallback_name})