import streamlit as st
import pandas as pd
import json
import time
from discoverer import LeadDiscoverer
from scout import SDRScout
from identity import IdentityHunter
from writer import EmailDrafter # Import the new module


# 1. Page Config
st.set_page_config(page_title="Krykos Mission Control", page_icon="📡", layout="wide")

# 2. CSS
st.markdown("""
<style>
    .big-font { font-size:30px !important; font-weight: bold; color: #00FF94; }
    .stButton>button { width: 100%; background-color: #00FF94; color: black; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #00CC76; color: black; }
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; border-left: 5px solid #00FF94; }
    .log-box { font-family: 'Courier New', monospace; font-size: 14px; color: #00FF94; background: #000; padding: 10px; border-radius: 5px; height: 200px; overflow-y: scroll; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.title("⚙️ Mission Settings")
    niche = st.text_input("Target Niche", placeholder="e.g. Solar in Miami")
    target_count = st.slider("Target Leads", 1, 10, 1) # Variable name matches logic
    start_btn = st.button("🚀 LAUNCH AGENT")
    st.divider()
    st.caption("System Status: 🟢 ONLINE")
    st.caption("Model: Qwen 2.5 (Local)")

# 4. Hero Section
st.markdown('<p class="big-font">📡 KRYKOS INTELLIGENCE HUB</p>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    scanned_metric = st.empty()
    scanned_metric.metric("Sites Scanned", "0")
with col2:
    qualified_metric = st.empty()
    qualified_metric.metric("Qualified Leads", "0")
with col3:
    socials_metric = st.empty()
    socials_metric.metric("Socials Found", "0")
with col4:
    status_metric = st.empty()
    status_metric.metric("Agent Status", "IDLE")

st.divider()

# 5. Session State
if 'results' not in st.session_state:
    st.session_state.results = []
if 'log_history' not in st.session_state:
    st.session_state.log_history = []

log_placeholder = st.empty()
results_placeholder = st.empty() # Placeholder for the table to appear LIVE

def update_log(message):
    st.session_state.log_history.append(f"> {message}")
    recent_logs = "<br>".join(st.session_state.log_history[-10:])
    log_placeholder.markdown(f"<div class='log-box'>{recent_logs}</div>", unsafe_allow_html=True)

# 6. Main Logic
if start_btn and niche:
    # Reset state for new run
    st.session_state.results = []
    st.session_state.log_history = []
    
    discoverer = LeadDiscoverer()
    scout = SDRScout()
    hunter = IdentityHunter()
    drafter = EmailDrafter() 

    status_metric.metric("Agent Status", "HUNTING...", delta_color="off")
    update_log(f"Initializing discovery for: {niche}")
    
    with st.spinner("Scanning the web..."):
        leads = discoverer.find_companies(niche, count=target_count) # Pass target count to discoverer
    
    scanned_count = 0
    qualified_count = 0
    socials_count = 0
    
    for i, lead in enumerate(leads):
        # STRICT STOP CHECK at the start of loop
        if qualified_count >= target_count:
            update_log("Target count reached. Stopping mission.")
            break

        scanned_count += 1
        scanned_metric.metric("Sites Scanned", f"{scanned_count}")
        update_log(f"Auditing target: {lead['url']}")
        
        # Scrape
        site_data = scout.scrape_website(lead['url'])
        if not site_data["main_md"]:
            update_log(f"⚠️ Scraping failed for {lead['url']}")
            continue
            
        # Analyze
        analysis_raw = scout.analyze_business_model(site_data["main_md"], lead['name'])
        
        try:
            profile = json.loads(analysis_raw)
            if not profile.get("is_qualified_business", True):
                update_log(f"❌ Rejected: {profile.get('company_name')}")
                continue
            
            # --- SUCCESS LOGIC ---
            qualified_count += 1
            qualified_metric.metric("Qualified Leads", f"{qualified_count}")
            update_log(f"✅ Qualified: {profile['company_name']}")

            # Hunt Identity
            combined_text = site_data["main_md"] + "\n" + site_data["about_md"]
            decision_maker = hunter.find_decision_maker(
                profile['company_name'], 
                combined_text, 
                site_data['found_socials']
            )
            
            if decision_maker.get('x_url') or decision_maker.get('linkedin_url'):
                socials_count += 1
                socials_metric.metric("Socials Found", f"{socials_count}")

            # DRAFT EMAIL
            update_log(f"✍️ Drafting email for {profile['company_name']}...")
            email_json = drafter.draft_email(
                profile['company_name'],
                decision_maker.get('full_name'),
                profile.get('krykos_automation_hypothesis'),
                ", ".join(profile.get('operational_pain_points', []))
            )
            
            try:
                email_data = json.loads(email_json)
                subject = email_data.get('subject', 'No Subject')
                body = email_data.get('body', 'No Body')
            except:
                subject = "Error"
                body = "Drafting failed"

            # Add to Results Row
            row = {
                "Company": profile['company_name'],
                "Decision Maker": decision_maker.get('full_name', 'Unknown'),
                "Website": lead['url'],
                "X Profile": decision_maker.get('x_url', None),
                "LinkedIn": decision_maker.get('linkedin_url', None),
                "Email Subject": subject, # NEW
                "Email Body": body,       # NEW
                "Hypothesis": profile.get('krykos_automation_hypothesis', ''),
                "Pain Points": ", ".join(profile.get('operational_pain_points', []))
            }
            
            st.session_state.results.append(row)
            
            # SAVE TO JSON IMMEDIATELY (Persistence Fix)
            with open("campaign_results.json", "w") as f:
                json.dump(st.session_state.results, f, indent=2)

            # SHOW TABLE LIVE (UI Fix)
            # We update the dataframe placeholder inside the loop so you see results instantly
            df = pd.DataFrame(st.session_state.results)
            results_placeholder.dataframe(
                df,
                column_config={
                    "Website": st.column_config.LinkColumn("Site", display_text="Visit"),
                    "X Profile": st.column_config.LinkColumn("X.com", display_text="Open X"),
                    "LinkedIn": st.column_config.LinkColumn("LinkedIn", display_text="Open LI"),
                    "Hypothesis": None,
                    "Pain Points": None
                },
                use_container_width=True,
                hide_index=True
            )
            
        except Exception as e:
            update_log(f"Error processing lead: {e}")
        
        time.sleep(1)

    status_metric.metric("Agent Status", "COMPLETE", delta_color="normal")
    update_log("Mission Finished.")

# Display Expanders AFTER the loop (for the final review)
if st.session_state.results:
    st.divider()
    # 8. Detailed Strategy Expanders
    st.subheader("🧠 Deep Analysis & Strategy")
    for lead in st.session_state.results:
        with st.expander(f"Strategy for **{lead['Company']}**"):
            
            # Create Tabs
            tab1, tab2 = st.tabs(["📊 Analysis", "✉️ Email Draft"])
            
            with tab1:
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown(f"**Pain Points:**\n{lead['Pain Points']}")
                with c2:
                    st.info(f"**🤖 Automation Hypothesis:**\n\n{lead['Hypothesis']}")
            
            with tab2:
                st.text_input("Subject:", value=lead['Email Subject'], key=f"sub_{lead['Company']}")
                st.text_area("Body:", value=lead['Email Body'], height=200, key=f"body_{lead['Company']}")
                st.caption("Copy this text into your email client.")

    # CSV Download Button
    df_final = pd.DataFrame(st.session_state.results)
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Full CSV", csv, "krykos_report.csv", "text/csv")