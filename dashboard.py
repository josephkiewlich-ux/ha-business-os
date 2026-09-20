import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import json
import requests
import pandas as pd
import google.generativeai as genai
from supabase import create_client, Client

# ==========================================
# 1. SETUP CREDENTIALS
# ==========================================
# Google Gemini Key
GEMINI_API_KEY = "AQ.Ab8RN6I-nXmjfYicfqZa-RbCY79C5wla7r9wMdE84g-gNp0uBA"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-3.6-flash')

# Supabase Cloud Database Credentials
SUPABASE_URL = "https://gdyhsdhowjefjhgrcotm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdkeWhzZGhvd2plZmpoZ3Jjb3RtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4NjE1NzMsImV4cCI6MjEwNTQzNzU3M30.8CATIeBvbe9El3oKbhGgh4gy0FK1wIXgY1HI8nbDOlw"

# Connect to your cloud vault
@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ==========================================
# 2. HUNTING ENGINE
# ==========================================
def hunt_leads(url):
    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = requests.get(jina_url, timeout=20)
        page_text = response.text
    except Exception as e:
        return None, f"❌ Failed to scrape website: {e}"
    
    prompt = f"""
    You are a lead generation assistant for a Home Assistant smart lock business.
    Analyze the following website text and extract any businesses, property managers, or builders you find.
    
    Output the data EXACTLY as a JSON array of objects with the following keys:
    "company_name", "contact_name", "email", "phone", "custom_sales_pitch"

    Website text:
    {page_text[:15000]} 
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        leads = json.loads(response.text)
        return leads, None
    except Exception as e:
        return None, f"❌ AI Error: {e}"

# ==========================================
# 3. VISUAL DASHBOARD
# ==========================================
st.set_page_config(page_title="HA Business OS", page_icon="🔐", layout="wide")

st.title("🔐 Home Assistant Business OS")

tab1, tab2, tab3 = st.tabs(["🎯 AI Lead Hunter", "👥 Client CRM", "💰 Financials"])

# --- TAB 1: LEAD HUNTER ---
with tab1:
    st.markdown("### Find New Clients")
    st.markdown("Enter the website of a local property manager, Airbnb host, or builder.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        target_url = st.text_input("Website URL:", placeholder="https://www.lapmg.com/")
    with col2:
        st.write("")
        st.write("")
        hunt_button = st.button("Hunt for Leads 🚀", use_container_width=True)
        
    if hunt_button and target_url:
        with st.spinner(f"🕵️ Scanning {target_url} and extracting leads..."):
            leads, error = hunt_leads(target_url)
            
            if error:
                st.error(error)
            elif leads:
                st.success(f"✅ Found {len(leads)} potential client(s)!")
                
                # Push directly to Supabase cloud database
                try:
                    supabase.table("leads").insert(leads).execute()
                    st.toast("Saved directly to cloud database!", icon="☁️")
                except Exception as db_err:
                    st.warning(f"Note: Could not save to database: {db_err}")
                
                # Show results in UI
                for lead in leads:
                    with st.container(border=True):
                        st.subheader(f"🏢 {lead.get('company_name')}")
                        st.write(f"**👤 Contact:** {lead.get('contact_name')}")
                        st.write(f"**📞 Phone:** {lead.get('phone')}")
                        st.write(f"**📧 Email:** {lead.get('email')}")
                        st.info(f"**🤖 AI Sales Pitch:** {lead.get('custom_sales_pitch')}")
            else:
                st.warning("No leads found on this page. Try a different URL.")

# --- TAB 2: CLIENT CRM ---
with tab2:
    st.markdown("### Active Leads & Clients (Cloud Vault)")
    
    # Fetch live data straight from Supabase
    try:
        response = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        cloud_leads = response.data
        
        if cloud_leads:
            df = pd.DataFrame(cloud_leads)
            # Reorganize columns for a clean view
            cols_to_show = ["company_name", "contact_name", "phone", "email", "custom_sales_pitch", "created_at"]
            available_cols = [c for c in cols_to_show if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No leads saved in your cloud database yet. Go hunt some in Tab 1!")
    except Exception as e:
        st.error(f"Error fetching from database: {e}")

# --- TAB 3: FINANCIALS ---
with tab3:
    st.markdown("### Financial Command Center")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", "$0.00", "Ready to scale")
    col2.metric("Active Subscriptions", "0", "0")
    col3.metric("Hardware Margin", "0%", "0")