import streamlit as st
import os
import pandas as pd  # Added for better table visualization
from logic import analyze_batch, get_parameter_names, save_comprehensive_pdf, generate_proposal

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="HydroEngine Pro | Water Quality Suite", 
    page_icon="💧", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .report-card { border-left: 5px solid #007bff; padding-left: 15px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Controls")
    if st.button("🗑️ Reset Batch List", type="secondary"):
        st.session_state.batch_list = []
        st.rerun()
    
    st.divider()
    st.info("**HydroEngine Pro** v2.0\nProfessional Civil Engineering Suite for Water Analysis and Design.")

# --- APP HEADER ---
st.title("💧 HydroEngine Pro")
st.caption("Comprehensive Water Quality Analysis & Project Design Wizard")

# --- TABS ---
tab1, tab2 = st.tabs(["📊 Multi-Parameter Analysis", "📝 Project Proposal Wizard"])

# ==========================
# TAB 1: ANALYSIS
# ==========================
with tab1:
    col_input, col_result = st.columns([1, 2], gap="large")
    
    with col_input:
        st.subheader("📥 Input Lab Data")
        
        # Initialize session state
        if 'batch_list' not in st.session_state:
            st.session_state.batch_list = []

        # --- INPUT CONTAINER ---
        with st.container(border=True):
            p_name = st.selectbox("Select Parameter", get_parameter_names(), key="input_param")
            p_val = st.number_input("Lab Result Value", step=0.01, format="%.2f", key="input_val")
            
            if st.button("➕ Add to Batch", type="primary"):
                if any(x['name'] == p_name for x in st.session_state.batch_list):
                    st.warning(f"{p_name} is already in the list.")
                else:
                    st.session_state.batch_list.append({"name": p_name, "value": p_val})
                    st.toast(f"Added {p_name} successfully!")

        # --- BATCH PREVIEW ---
        st.subheader("📋 Current Batch")
        if st.session_state.batch_list:
            # Convert to DataFrame for a cleaner look
            df = pd.DataFrame(st.session_state.batch_list)
            st.table(df)
            
            # Simple list with delete buttons
            for i, item in enumerate(st.session_state.batch_list):
                cols = st.columns([4, 1])
                cols[0].write(f"**{item['name']}**: {item['value']}")
                if cols[1].button("❌", key=f"del_{i}"):
                    st.session_state.batch_list.pop(i)
                    st.rerun()
        else:
            st.info("No parameters added yet. Use the form above.")

    with col_result:
        st.subheader("🔎 Analysis Results")
        
        if not st.session_state.batch_list:
            st.info("Pending data input. Results will appear here after running analysis.")
        
        if st.button("🚀 RUN FULL ANALYSIS", type="primary", use_container_width=True):
            if not st.session_state.batch_list:
                st.error("Cannot run analysis on an empty batch.")
            else:
                gui_text, pdf_data = analyze_batch(st.session_state.batch_list)
                
                # --- RESULTS DISPLAY ---
                for tag, text in gui_text:
                    if tag == "HEADER":
                        st.markdown(f"### {text}")
                    elif tag == "SUBHEADER":
                        st.divider()
                        st.markdown(f"#### {text}")
                    elif tag == "FAIL":
                        st.error(text)
                    elif tag == "PASS":
                        st.success(text)
                    elif tag == "INFO":
                        st.info(text)
                    elif tag == "NORMAL":
                        st.write(text)

                # --- DOWNLOAD SECTION ---
                st.divider()
                pdf_file = save_comprehensive_pdf(pdf_data)
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label="📥 Download Professional Report (PDF)",
                        data=f,
                        file_name="Water_Analysis_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

# ==========================
# TAB 2: PROPOSAL
# ==========================
with tab2:
    st.subheader("🏗️ Project Design & Proposal")
    
    with st.container(border=True):
        with st.form("proposal_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                prop_name = st.text_input("Project Name", placeholder="e.g., Riverside Community Water Project")
                prop_type = st.radio("Community Type", ["City (Geometric)", "Village (Arithmetic)"], horizontal=True)
                prop_pop = st.number_input("Current Population (Po)", min_value=0, step=1000)
            with c2:
                prop_rate = st.slider("Annual Growth Rate (%)", 0.0, 10.0, 2.5)
                prop_years = st.number_input("Design Period (Years)", min_value=1, max_value=100, value=20)
                prop_source = st.selectbox("Water Source", ["River/Stream", "Groundwater (Borehole)", "Rainwater"])
            
            st.markdown("---")
            submitted_prop = st.form_submit_button("🔨 Generate Engineering Proposal")

    if submitted_prop:
        if not prop_name or prop_pop == 0:
            st.error("⚠️ Please provide a Project Name and Population count.")
        else:
            with st.spinner("Calculating engineering requirements..."):
                inputs = {
                    "name": prop_name,
                    "type": prop_type,
                    "pop_current": int(prop_pop),
                    "growth_rate": prop_rate,
                    "source": prop_source,
                    "design_period": int(prop_years)
                }
                
                fname = generate_proposal(inputs)
                
                # Success Dashboard
                st.balloons()
                st.success(f"Proposal for **{prop_name}** is ready!")
                
                col_left, col_right = st.columns(2)
                with col_left:
                    st.metric("Future Population", f"{int(prop_pop * (1 + prop_rate/100)**prop_years):,}")
                
                with open(fname, "rb") as f:
                    st.download_button(
                        label="📥 Download Proposal PDF",
                        data=f,
                        file_name=f"Proposal_{prop_name}.pdf",
                        mime="application/pdf"
                    )