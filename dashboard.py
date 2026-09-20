# --- TAB 2: CLIENT CRM ---
with tab2:
    st.markdown("### Active Leads & Clients (Cloud Vault)")
    
    try:
        response = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        cloud_leads = response.data
        
        if cloud_leads:
            df = pd.DataFrame(cloud_leads)
            
            # Show the main database table
            cols_to_show = ["company_name", "status", "hardware_installed", "contact_name", "phone"]
            available_cols = [c for c in cols_to_show if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
            
            st.divider()
            
            # 🛠️ THE HARDWARE UPGRADE FORM
            st.markdown("#### 🛠️ Log New Hardware Installation")
            
            # Create a dropdown to select a client
            lead_names = df['company_name'].tolist()
            selected_lead = st.selectbox("Select a Client:", lead_names)
            
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("Status", ["Lead", "Active Client", "Maintenance Mode", "Declined"])
            with col2:
                hardware = st.text_area("Hardware Installed (e.g., 1x HA Green, 4x Yale Assure, 1x Zigbee dongle)")
                
            if st.button("Update Client Record", type="primary"):
                # Push the hardware updates to the cloud!
                supabase.table("leads").update({
                    "status": new_status,
                    "hardware_installed": hardware
                }).eq("company_name", selected_lead).execute()
                
                st.success(f"✅ Hardware logged for {selected_lead}!")
                st.rerun() # This instantly refreshes the page to show the new data
                
        else:
            st.info("No leads saved in your cloud database yet. Go hunt some in Tab 1!")
            
    except Exception as e:
        st.error(f"Error fetching from database: {e}")