import json
import time, os
from discoverer import LeadDiscoverer
from scout import SDRScout
from identity import IdentityHunter

RESULTS_FILE = "campaign_results.json"

def load_existing_results():
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r') as f:
                return json.load(f)
        except: return []
    return []

def save_results(results):
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    print("--- KRYKOS AUTOMATED LEAD HUNTER v2.2 ---")
    
    niche = input("> What niche/location are we hunting today?: ")
    target_count = 3 
    
    discoverer = LeadDiscoverer()
    scout = SDRScout()
    hunter = IdentityHunter()
    
    # Load history
    campaign_history = load_existing_results()
    
    all_potential_leads = discoverer.find_companies(niche)
    qualified_found = 0

    for i, lead in enumerate(all_potential_leads):
        if qualified_found >= target_count: break

        # Skip if already in our file
        if any(res['business']['source_url'] == lead['url'] for res in campaign_history):
            continue

        print(f"\n" + "="*60)
        print(f"[*] Auditing: {lead['url']}")
        
        site_data = scout.scrape_website(lead['url'])
        if not site_data["main_md"]: continue
            
        analysis_raw = scout.analyze_business_model(site_data["main_md"], lead['name'])
        try:
            profile = json.loads(analysis_raw)
            if not profile.get("is_qualified_business", True):
                continue
            
            qualified_found += 1
            profile['source_url'] = lead['url'] # Requirement 1: Add Link to JSON

            # Hunt socials (using footer data + search)
            combined_site_text = site_data["main_md"] + "\n" + site_data["about_md"]
            person_data = hunter.find_decision_maker(profile['company_name'], combined_site_text, site_data['found_socials'])
            
            full_prospect = {
                "business": profile,
                "decision_maker": person_data
            }
            
            # Save persistently
            campaign_history.append(full_prospect)
            save_results(campaign_history)

            print(f"   [✅] LEAD QUALIFIED & SAVED. X: {person_data['x_url']}")
            
        except Exception as e:
            print(f"[!] Error: {e}")
            
        time.sleep(2) 

    print(f"\n🏁 Finished. Total leads in database: {len(campaign_history)}")

if __name__ == "__main__":
    main()