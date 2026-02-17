import os
from firecrawl import FirecrawlApp
from openai import OpenAI #is compatible with Ollama's API
from dotenv import load_dotenv

load_dotenv()

class SDRScout:
    def __init__(self):
        # Initialize Firecrawl
        self.firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        
        #  OpenAI usesto local Ollama server
        self.ai = OpenAI(
            api_key=os.getenv("OLLAMA_API_KEY"), 
            base_url=os.getenv("OLLAMA_BASE_URL")
        )
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def scrape_website(self, url: str) -> str:
        """
        Extracts content from the target URL.
        Compatible with firecrawl-py 4.x.
        """
        print(f"[*] Intelligence Gathering: Accessing the site...")
        try:
            scrape_result = self.firecrawl.scrape(url)
            
            if isinstance(scrape_result, dict):
                return scrape_result.get('markdown', scrape_result.get('content', ''))
            
            if hasattr(scrape_result, 'markdown'):
                return scrape_result.markdown
            
            return str(scrape_result)
                
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            print(f"[!] {error_msg}")
            return error_msg

    def analyze_business_model(self, markdown_content: str) -> str:
        #Uses local Ollama LLM to analyze the business.
        print(f"[*] Analysis Engine: Running local model ({self.model})...")
        
        system_prompt = """
        You are a Senior Sales Strategist. Analyze the provided website content to build a prospect profile.
        Identify manual processes that can be automated with AI and how easy it is to achieve.
        
        Return ONLY a valid JSON object with this structure:
        {
          "company_name": "Name",
          "core_services": "Description",
          "target_audience": "Customers",
          "identified_inefficiencies": ["Task 1", "Task 2"],
          "difficulty_to_automate": "easy, medium, hard",
          "krykos_automation_hypothesis": "AI pitch"
        }
        """
        
        try:
            content_to_analyze = markdown_content[:6000] if markdown_content else "No content"
            
            response = self.ai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Website Content:\n{content_to_analyze}"}
                ],
                # Ollama supports JSON mode in recent versions
                response_format={'type': 'json_object'}
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Local AI Analysis error: {str(e)}"