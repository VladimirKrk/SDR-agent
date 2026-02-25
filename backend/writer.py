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
        You are an elite B2B Copywriter. 
        Your task is to write a cold email that looks like it was sent by a busy consultant, not a marketing bot.
        
        PROSPECT CONTEXT:
        Target: {company_name}
        Name: {name}
        Pain Points: {pain_points}
        Hypothesis: {hypothesis}
        
        ----------------------------------
        STEP 1: GENERATE SUBJECT LINE
        The subject line must be catchy, professional, and relevant. 
        Choose one of these formulas and fill in the brackets:
        
        1. "{company_name} + [Process]" (e.g. "HMG Creative onboarding")
        2. "question re: [Pain Point]" (e.g. "question re: scheduling")
        3. "idea for {company_name}" (Simple, high open rate)
        4. "[Pain Point] at {company_name}" (e.g. "lead response at HMG")
        
        RULES FOR SUBJECT:
        - All lowercase (looks more personal/internal).
        - Max 4 words.
        - NO generic words like "Opportunity", "Partnership", "Services".
        ----------------------------------
        
        STEP 2: SELECT BODY TEMPLATE

        INSTRUCTIONS:
        1. Analyze the "Identified Pain Points".
        2. Choose ONE template that fits best. You can adapt the email body to better match the pain points.
        3. Fill in any placeholders (like {{name}}), but skip them entirely if there is no context.
        4. Do NOT change the core structure or tone. 
    
        [Template A - If Pain is Manual Data/Forms]
        Hi {name},
        
        Noticed you're capturing leads via the site but likely handling the CRM entry manually.
        
        We built an agent that automates that handoff entirely—no human data entry needed.
        
        Mind if I send over a 30-second video showing how it works?
        
        Best,
        Krykos Team

        [Template B - If Pain is Scheduling/Speed]
        Hi {name},
        
        I was testing your inquiry flow and noticed there’s no instant booking option. In your industry, speed usually dictates conversion.
        
        We deploy 24/7 AI agents that qualify and book these leads instantly, so you stop losing deals to lag time.
        
        Open to seeing a quick demo?
        
        Best,
        Krykos Team

        [Template C - If Pain is Hiring/General Scaling]
        Hi {name},
        
        I've been following {company_name} and noticed the team is growing.
        
        Usually, at this stage, operational drag (admin, triage, scheduling) starts eating into strategy time. We build custom "AI Employees" to take that grunt work off your plate.
        
        Would you be opposed to seeing how we helped a similar agency automate this?
        
        Best,
        Krykos Team
        
        ----------------------------------
        FINAL OUTPUT FORMAT (JSON ONLY):
        {{
            "subject": "insert generated subject here",
            "body": "insert selected body here"
        }}
        """
        
        try:
            response = self.ai.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={'type': 'json_object'},
                temperature=0.6 # Increased slightly to allow Subject Line variety
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"subject": "Error", "body": str(e)})