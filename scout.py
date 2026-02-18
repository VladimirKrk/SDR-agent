import json
import os, re
from firecrawl import FirecrawlApp
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class SDRScout:
    def __init__(self):
        self.firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        self.ai = OpenAI(api_key=os.getenv("OLLAMA_API_KEY", "ollama"), base_url=os.getenv("OLLAMA_BASE_URL"))
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def scrape_website(self, url: str) -> dict:
        print(f"[*] Intelligence Gathering: Accessing {url}...")
        try:
            scrape_result = self.firecrawl.scrape(url)
            main_content = scrape_result.get('markdown', "") if isinstance(scrape_result, dict) else scrape_result.markdown
            
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

            return {
                "main_md": main_content,
                "about_md": about_content
            }
        except Exception as e:
            print(f"[!] Scraping failed: {e}")
            return {"main_md": "", "about_md": ""}

    def analyze_business_model(self, markdown_content: str, fallback_name: str) -> str:
        print(f"[*] Analysis Engine: Running local model (Operational Audit)...")
        
        system_prompt = f"""
            You are an expert Operations Efficiency Consultant, specializing in identifying time-consuming manual processes that distract business owners and their teams from high-value strategic work. Your methodology, "Krykos AI", focuses on uncovering "low-value" repetitive tasks that can be safely automated without interfering with the company's core product or service.

            Your task: Analyze the provided website content of a company. Your goal is to identify 2-3 specific, concrete examples of manual, low-value tasks that the company likely performs regularly. These tasks should be operational in nature (e.g., admin work, lead qualification, scheduling, customer support triage) — NOT related to automating the core service they sell to clients.

            RULES:
            1. NEVER suggest automating the company's core offering. For example, if they are a marketing agency, do NOT propose automating SEO, ad creation, or content writing. If they are a roofing company, do NOT propose automating roof inspections or installations.
            2. Look for evidence on their website that indicates manual processes. Pay special attention to:
            - "Contact Us" forms: This usually means someone manually reads and enters lead data into a CRM.
            - "Book a Consultation" or "Schedule a Call": Often involves back-and-forth emails to find a mutual time — a perfect candidate for automated scheduling.
            - "FAQ" pages: Frequent, repetitive questions suggest customer support staff spend time answering the same queries. An AI chatbot could handle tier-1 support.
            - "Team" or "Careers" pages: A large team might imply high coordination overhead (meetings, status updates, internal communication). Consider tools that streamline project updates.
            - "Resources" or "Blog": If they publish content, maybe they manually promote it on social media — could be automated.
            - Any mention of "download this PDF" or "email us for more info" — implies manual follow-up.
            3. Be specific: Instead of vague "improve efficiency", pinpoint exact activities (e.g., "manually transferring contact form data to HubSpot").
            4. The automation hypothesis should be a short, compelling pitch that directly addresses one of the pain points you identified. It should mention Krykos and a concrete benefit (time saved, faster response, etc.).
            5. If you cannot find enough evidence on the site, use common sense for the industry. For a typical small business, assume they handle leads manually unless the site shows otherwise.

            OUTPUT FORMAT (Strict JSON):
            {{
            "company_name": "Extract the exact company name from the website, or use the provided fallback if unclear.",
            "core_business": "In one short sentence, what product or service does this company sell? (e.g., SEO services, roofing installation, legal advice)",
            "operational_pain_points": [
                "Specific manual task 1 (e.g., 'Manually entering contact form submissions into Salesforce')",
                "Specific manual task 2 (e.g., 'Coordinating consultation times via email back-and-forth')",
                "Specific manual task 3 (if applicable, otherwise omit)"
            ],
            "krykos_automation_hypothesis": "A one-sentence pitch that connects one pain point to a Krykos solution. Example: 'We noticed you use a standard contact form. Krykos can deploy an AI agent that instantly qualifies these leads and books meetings directly into your calendar, saving your sales team 10+ hours a week.'"
            }}

            Make sure your output is only valid JSON, with no additional text.
            """
        
        try:
            content_to_analyze = markdown_content[:5000] if markdown_content else "No content"
            
            response = self.ai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Website Content:\n{content_to_analyze}"}
                ],
                response_format={'type': 'json_object'}
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"company_name": fallback_name, "error": str(e)})