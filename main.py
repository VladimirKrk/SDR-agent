import json
import time
import re
from scout import SDRScout

def apply_strict_privacy_mask(profile, target_index):
    """
    Completely anonymizes the profile. 
    Replaces real names with 'Target-ID' and redacts them from text blocks.
    """
    # 1. Generate a generic ID (Target-A, Target-B...)
    generic_id = f"Target-{chr(65 + target_index)}"
    real_name = profile.get('company_name', '')
    
    masked = profile.copy()
    
    # 2. Complete redact Name and URL
    masked['company_name'] = generic_id
    masked['source_url'] = "https://[REDACTED].com/"

    # 3. Deep Redaction: Find real_name inside ALL text fields and replace it
    if real_name and len(real_name) > 2:
        # Create a case-insensitive regex for the company name
        # We also catch common variations (like "Socialfly" vs "Socialfly NY")
        name_parts = real_name.split()
        main_name = name_parts[0] if name_parts else real_name
        
        pattern = re.compile(re.escape(main_name), re.IGNORECASE)

        for key, value in masked.items():
            if isinstance(value, str):
                masked[key] = pattern.sub(generic_id, value)
            elif isinstance(value, list):
                masked[key] = [pattern.sub(generic_id, item) if isinstance(item, str) else item for item in value]

    return masked

def main():
    print("--- KRYKOS SDR SCOUT v1.1 [Strict Privacy Mode] ---")
    
    scout = SDRScout()
    
    target_urls = [
        "https://www.socialflyny.com/",          
        "https://www.theagencyre.com/region/miami"
    ]
    
    for index, url in enumerate(target_urls):
        print(f"\n" + "-"*50)
        print(f"[*] Analyzing target...")
        
        raw_content = scout.scrape_website(url)
        if not raw_content or "Error" in raw_content:
            continue

        analysis_raw = scout.analyze_business_model(raw_content)
        
        try:
            profile = json.loads(analysis_raw)
            profile['source_url'] = url
            
            # APPLY STRICT MASK
            masked_profile = apply_strict_privacy_mask(profile, index)
            
            print("\n[+] ANALYTICAL REPORT (FULLY ANONYMIZED):")
            print(json.dumps(masked_profile, indent=2))
            
        except Exception as e:
            print(f"[!] Analysis failed.")

        time.sleep(1)

if __name__ == "__main__":
    main()