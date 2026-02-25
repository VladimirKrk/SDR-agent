import asyncio
import json
import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from discoverer import LeadDiscoverer
from scout import SDRScout
from identity import IdentityHunter
from writer import EmailDrafter
from database import HistoryDB 

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

RESULTS_FILE = "campaign_results.json"

# --- NEW: ENDPOINT TO LOAD HISTORY ON STARTUP ---
@app.get("/api/history")
async def get_history():
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r") as f:
                data = json.load(f)
                return JSONResponse(content=data)
        except Exception as e:
            return JSONResponse(content=[], status_code=500)
    return JSONResponse(content=[])

# --- EXISTING WEBSOCKET LOGIC ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    discoverer = LeadDiscoverer()
    scout = SDRScout()
    hunter = IdentityHunter()
    drafter = EmailDrafter()
    db = HistoryDB()

    try:
        data = await websocket.receive_text()
        config = json.loads(data)
        niche = config.get("niche")
        target_count = int(config.get("count", 1))
        
        await websocket.send_json({"type": "node_active", "node": "1"})
        await websocket.send_json({"type": "log", "message": f"Scanning for {target_count} targets in: {niche}..."})
        
        leads = discoverer.find_companies(niche, count=target_count)
        
        if not leads:
            await websocket.send_json({"type": "error", "message": "No leads found."})
            return

        await websocket.send_json({"type": "node_done", "node": "1"})
        
        qualified_found = 0

        # Load existing results so we can append to them and save
        existing_results = []
        if os.path.exists(RESULTS_FILE):
            try:
                with open(RESULTS_FILE, "r") as f:
                    existing_results = json.load(f)
            except: pass

        for lead in leads:
            if qualified_found >= target_count:
                break

            if db.exists(lead['url']):
                await websocket.send_json({"type": "log", "message": f"Skipping {lead['url']} (In History)"})
                continue

            await websocket.send_json({"type": "log", "message": f"Processing: {lead['url']}"})
            
            # --- SCOUT ---
            await websocket.send_json({"type": "node_active", "node": "2"})
            site_data = scout.scrape_website(lead['url'])
            
            db.add(lead['url']) # Mark as processed
            
            if not site_data["main_md"]:
                await websocket.send_json({"type": "node_done", "node": "2"})
                continue

            # --- GATEKEEPER ---
            await websocket.send_json({"type": "node_done", "node": "2"})
            await websocket.send_json({"type": "node_active", "node": "3"})
            
            analysis_raw = scout.analyze_business_model(site_data["main_md"], lead['name'])
            profile = json.loads(analysis_raw)
            
            if not profile.get("is_qualified_business", True):
                await websocket.send_json({"type": "log", "message": f"❌ Rejected: {profile.get('company_name')}"})
                await websocket.send_json({"type": "node_error", "node": "3"})
                await asyncio.sleep(0.5) 
                continue
            
            qualified_found += 1 

            # --- HUNTER ---
            await websocket.send_json({"type": "node_done", "node": "3"})
            await websocket.send_json({"type": "node_active", "node": "4"})
            
            combined_text = site_data["main_md"] + "\n" + site_data["about_md"]
            decision_maker = hunter.find_decision_maker(
                profile['company_name'], 
                combined_text, 
                site_data['found_socials']
            )

            # --- WRITER ---
            await websocket.send_json({"type": "node_done", "node": "4"})
            await websocket.send_json({"type": "node_active", "node": "5"})
            
            email_json = drafter.draft_email(
                profile['company_name'],
                decision_maker.get('full_name'),
                profile.get('krykos_automation_hypothesis'),
                ", ".join(profile.get('operational_pain_points', []))
            )
            try:
                email_data = json.loads(email_json)
            except:
                email_data = {"subject": "Error", "body": email_json}

            await websocket.send_json({"type": "node_done", "node": "5"})
            
            # FORMAT RESULT
            result_payload = {
                "company": profile['company_name'],
                "person": decision_maker.get('full_name'),
                "website": lead['url'],
                "email_subject": email_data.get('subject'),
                "email_body": email_data.get('body'),
                "x_url": decision_maker.get('x_url'),
                "linkedin_url": decision_maker.get('linkedin_url'),
                "pain_points": profile.get('operational_pain_points', []),
                "hypothesis": profile.get('krykos_automation_hypothesis')
            }
            
            # --- SAVE TO FILE IMMEDIATELY ---
            existing_results.append(result_payload)
            with open(RESULTS_FILE, "w") as f:
                json.dump(existing_results, f, indent=2)

            # SEND TO UI
            await websocket.send_json({"type": "result", "data": result_payload})
            
            await asyncio.sleep(1)

        await websocket.send_json({"type": "log", "message": "🏁 Mission Complete."})

    except Exception as e:
        print(f"Error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})