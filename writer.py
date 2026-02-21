import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class EmailDrafter:
    def __init__(self):
        self.ai = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"), 
            base_url="https://api.deepseek.com"
        )

    def draft_email(self, company_name, decision_maker, hypothesis, pain_points):
        print(f"[*] Drafter: Crafting high-converting copy for {company_name}...")
        
        name = decision_maker if decision_maker and decision_maker != "Unknown" else "there"
        
        prompt = f"""
        You are an elite B2B Sales Development Representative who writes 'plain English' cold emails.
        Your goal is to start a conversation, NOT close a sale immediately.
    
        
        SUBJECT LINE RULES (CRITICAL):
        1. MAX 5 WORDS.
        2. NO cheesy hooks ("Quick question", "Knock knock").
        3. NO selling in the subject ("Growth", "Sales", "AI").
        4. MUST be relevant to the company or the problem.
        5. Personalized if possible ("{company_name}"). If not, use something neutral but intriguing.

        TONE GUIDE:
        - Conversational, direct, low-pressure.
        - Write like a colleague, not a marketer.
        - Zero corporate fluff. No "unlocking potential" or "revolutionizing".
        
        PROSPECT CONTEXT:
        - Target: {company_name}
        - Name: {name}
        - Observed Friction: {pain_points}
        - Our AI Solution: {hypothesis}
        
        TASK:
        Write a 3-sentence cold email structure and the subject line.
        1. Observation: "I was looking at your site and noticed [specific pain point context]."
        2. Insight/Solution: "We built an AI agent that automates exactly this, saving [benefit]."
        3. Low-Friction Ask: "Mind if I send over a 30-second video demo?"
        
        STRICT RULES:
        1. follow SUBJECT LINE RULES.
        2. NO greetings like "I hope this finds you well" or "My name is...".
        3. NO buzzwords: Avoid "cutting-edge", "game-changer", "transform", "comprehensive".
        4. Sign off: "Best, Krykos Team".
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "subject": "subject line",
            "body": "email body text"
        }}
        """
        
        try:
            response = self.ai.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={'type': 'json_object'},
                temperature=0.6 # Lower temperature for less creative/hallucinated fluff
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"subject": "Error", "body": str(e)})