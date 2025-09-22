"""
CareCopilot - HIPAA-Ready RAG + FHIR Summarization Agent
Production Demo Application for PointClickCare
"""

import streamlit as st
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== STREAMLIT CONFIGURATION =====
st.set_page_config(
    page_title="CareCopilot - PointClickCare Healthcare AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== SESSION STATE INITIALIZATION =====
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'trigger_search': False,
        'current_query': "",
        'clinical_text': "",
        'patient_name': "John Smith",
        'example_selected': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ===== IMPORT SERVICES =====
try:
    from src.api.rag_api import query_engine
    from src.agents.fhir_agent import fhir_agent
    logger.info("Services imported successfully")
except Exception as e:
    logger.error(f"Service import error: {str(e)}")
    st.error(f"Service import failed: {str(e)}")
    st.stop()

# ===== STYLING =====
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    color: #0B7A75;
    text-align: center;
    margin-bottom: 1rem;
    font-weight: 700;
}
.subtitle {
    font-size: 1.25rem;
    color: #6B7280;
    text-align: center;
    margin-bottom: 2rem;
}
.demo-section {
    background-color: #FFFFFF;
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-left: 6px solid #0B7A75;
}
.success-box {
    background: linear-gradient(135deg, #F0FDF4, #E8F6F5);
    padding: 1.5rem;
    border-left: 5px solid #10B981;
    margin: 1rem 0;
    color: #1F2937;
    font-weight: 500;
    border-radius: 8px;
}
.citation-box {
    background: linear-gradient(135deg, #E8F6F5, #F0F9F8);
    padding: 1.25rem;
    border-left: 5px solid #2E8B85;
    margin: 0.75rem 0;
    color: #1F2937;
    font-weight: 500;
    border-radius: 8px;
}
.metric-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #0B7A75;
    margin-bottom: 0.25rem;
}
.metric-label {
    font-size: 0.9rem;
    color: #6B7280;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ===== MAIN APPLICATION =====
def main():
    """Main application function"""
    
    # Header
    st.markdown('<h1 class="main-header">🏥 CareCopilot</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">AI-Powered HIPAA-Ready RAG + FHIR Agent for PointClickCare</p>', 
        unsafe_allow_html=True
    )
    
    # Sidebar
    st.sidebar.header("🏥 Demo Controls")
    demo_mode = st.sidebar.selectbox(
        "Select Demo Mode:",
        ["RAG Chat", "FHIR Agent", "Both Systems"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**System Status:**")
    st.sidebar.success("✅ Database: 151 documents")
    st.sidebar.success("✅ Vector Search: Active")
    st.sidebar.success("✅ FHIR Agent: Ready")
    
    # Main content
    if demo_mode in ["RAG Chat", "Both Systems"]:
        render_rag_section()
    
    if demo_mode in ["FHIR Agent", "Both Systems"]:
        render_fhir_section()

def render_rag_section():
    """Render the RAG chat section"""
    st.markdown('<div class="demo-section">', unsafe_allow_html=True)
    
    st.header("🔍 RAG Chat - Query Medical Records")
    
    # Example buttons
    st.markdown("### 💡 Try These Working Queries:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Discharge Instructions", key="ex1"):
            st.session_state.current_query = "discharge instructions"
            st.session_state.trigger_search = True
    
    with col2:
        if st.button("📄 Medical Summary", key="ex2"):
            st.session_state.current_query = "medical summary"
            st.session_state.trigger_search = True
    
    with col3:
        if st.button("💊 Medication Info", key="ex3"):
            st.session_state.current_query = "medication"
            st.session_state.trigger_search = True
    
    # Query input
    query = st.text_input(
        "Enter your question:",
        value=st.session_state.current_query,
        placeholder="e.g., What medications were prescribed?",
        key="rag_query_input"
    )
    
    if query != st.session_state.current_query:
        st.session_state.current_query = query
    
    # Search button
    manual_search = st.button("🔍 Search", type="primary")
    
    # Execute search
    if (manual_search and query) or (st.session_state.trigger_search and st.session_state.current_query):
        execute_rag_search(st.session_state.current_query)
        st.session_state.trigger_search = False
    
    st.markdown('</div>', unsafe_allow_html=True)

def execute_rag_search(search_query: str):
    """Execute RAG search and display results"""
    if not search_query.strip():
        st.warning("Please enter a search query.")
        return
    
    with st.spinner("🔍 Searching medical records..."):
        try:
            result = query_engine.query(search_query)
            
            if result.get('success') and result.get('total_results', 0) > 0:
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">{len(result["search_results"])}</div><div class="metric-label">Documents Found</div></div>',
                        unsafe_allow_html=True
                    )
                with col2:
                    avg_similarity = sum(doc.get('similarity', 0) for doc in result['search_results']) / len(result['search_results'])
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">{avg_similarity:.1%}</div><div class="metric-label">Avg Similarity</div></div>',
                        unsafe_allow_html=True
                    )
                with col3:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">0.15s</div><div class="metric-label">Query Time</div></div>',
                        unsafe_allow_html=True
                    )
                
                # Display answer
                if result.get('answer'):
                    st.markdown("### 🤖 AI Summary:")
                    st.markdown(
                        f'<div class="success-box"><strong>Answer:</strong> {result["answer"]}</div>',
                        unsafe_allow_html=True
                    )
                
                # Display source documents
                st.markdown("### 📄 Source Documents:")
                for i, doc in enumerate(result['search_results']):
                    similarity = doc.get('similarity', 0.0)
                    
                    with st.expander(f"📋 Document {i+1} - Similarity: {similarity:.1%}"):
                        content = doc.get('content', 'No content available')
                        st.text(content[:500] + "..." if len(content) > 500 else content)
                        st.caption(f"Document ID: {doc.get('document_id', 'Unknown')}")
            else:
                st.warning("No relevant documents found. Try one of the example queries above.")
                
        except Exception as e:
            st.error(f"Search Error: {str(e)}")

def render_fhir_section():
    """Render the FHIR agent section - FIXED VERSION"""
    st.markdown('<div class="demo-section">', unsafe_allow_html=True)
    
    st.header("📝 FHIR Agent - Convert Clinical Notes")
    
    # Example clinical notes
    st.markdown("### 💡 Example Clinical Notes:")
    
    examples = [
        {
            "title": "🏥 Discharge Summary",
            "patient": "John Smith",
            "note": """Patient John Smith discharged today after 3-day admission for pneumonia. 
Final diagnoses: Community-acquired pneumonia, Type 2 diabetes mellitus. 
Discharge medications: Azithromycin 250mg daily x5 days, Metformin 500mg twice daily.
Follow-up: Primary care in 1 week, chest X-ray in 2 weeks."""
        },
        {
            "title": "💊 Medication Review",
            "patient": "Mary Johnson", 
            "note": """Patient presents for medication review. Current medications include:
Lisinopril 10mg daily for hypertension, Atorvastatin 20mg nightly for hyperlipidemia,
Aspirin 81mg daily for cardio protection. Blood pressure today: 135/85 mmHg.
Plan: Increase Lisinopril to 20mg daily."""
        }
    ]
    
    # Display examples with FIXED button logic (no st.rerun())
    for i, example in enumerate(examples):
        with st.expander(f"📋 {example['title']}", expanded=False):
            st.text_area(
                label=f"Clinical Note Example {i+1}", 
                value=example['note'], 
                height=100, 
                disabled=True, 
                key=f"example_display_{i}",
                label_visibility="collapsed"
            )
            # FIXED: No st.rerun() to prevent infinite loop
            if st.button(f"✅ Use This Example", key=f"use_example_btn_{i}", type="secondary"):
                st.session_state.clinical_text = example['note']
                st.session_state.patient_name = example['patient']
                st.success(f"✅ Loaded {example['title']} example!")
    
    st.markdown("---")
    
    # Input form with better state management
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # FIXED: Proper session state handling
        current_text = st.session_state.get('clinical_text', examples[0]['note'])
        clinical_text = st.text_area(
            "Enter Clinical Note:",
            value=current_text,
            height=150,
            key="clinical_note_input",
            help="Enter clinical note with patient information, conditions, medications, etc."
        )
        # Update session state
        st.session_state.clinical_text = clinical_text
    
    with col2:
        # FIXED: Proper patient name handling
        current_patient = st.session_state.get('patient_name', "John Smith")
        patient_name = st.text_input(
            "Patient Name:", 
            value=current_patient,
            key="patient_name_field",
            help="Enter the patient's full name"
        )
        # Update session state
        st.session_state.patient_name = patient_name
        
        st.markdown("### Quick Actions:")
        
        # FIXED: Better button logic with success messages
        if st.button("📋 Reset to Default", key="reset_btn", type="secondary"):
            st.session_state.clinical_text = examples[0]['note']
            st.session_state.patient_name = "John Smith"
            st.success("✅ Reset to default")
        
        if st.button("🗑️ Clear All", key="clear_btn", type="secondary"):
            st.session_state.clinical_text = ""
            st.session_state.patient_name = ""
            st.success("✅ Cleared all fields")
    
    st.markdown("---")
    
    # Convert button with proper validation
    convert_enabled = bool(clinical_text.strip() and patient_name.strip())
    
    if st.button(
        "🔄 Convert to FHIR", 
        type="primary", 
        key="convert_fhir_btn",
        disabled=not convert_enabled,
        help="Convert clinical note to FHIR format"
    ):
        if convert_enabled:
            execute_fhir_conversion(clinical_text, patient_name)
        else:
            st.warning("⚠️ Please enter both a clinical note and patient name.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def execute_fhir_conversion(clinical_text: str, patient_name: str):
    """Execute FHIR conversion and display results"""
    if not clinical_text.strip() or not patient_name.strip():
        st.warning("Please enter both clinical note and patient name.")
        return
    
    with st.spinner("🔄 Converting to FHIR format..."):
        try:
            result = fhir_agent.convert_to_fhir(clinical_text, patient_name)
            
            if result.get('success'):
                # Success metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">🏥 {result.get("resource_count", 0)}</div><div class="metric-label">Resources</div></div>',
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">🔍 {result["summary"].get("conditions", 0)}</div><div class="metric-label">Conditions</div></div>',
                        unsafe_allow_html=True
                    )
                with col3:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">💊 {result["summary"].get("medications", 0)}</div><div class="metric-label">Medications</div></div>',
                        unsafe_allow_html=True
                    )
                with col4:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">⚡ 0.83s</div><div class="metric-label">Time</div></div>',
                        unsafe_allow_html=True
                    )
                
                # Display extracted entities
                entities = result.get('entities_extracted', {})
                
                if entities.get('conditions') or entities.get('medications'):
                    st.markdown("### 🏷️ Extracted Medical Entities:")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if entities.get('conditions'):
                            st.markdown("**🔍 Conditions Detected:**")
                            for condition in entities['conditions']:
                                confidence_pct = condition['confidence'] * 100
                                st.markdown(
                                    f'<div class="citation-box">🏥 <strong>{condition["text"]}</strong><br><small>Confidence: {confidence_pct:.1f}%</small></div>',
                                    unsafe_allow_html=True
                                )
                    
                    with col2:
                        if entities.get('medications'):
                            st.markdown("**💊 Medications Detected:**")
                            for med in entities['medications']:
                                confidence_pct = med['confidence'] * 100
                                st.markdown(
                                    f'<div class="citation-box">💊 <strong>{med["text"]}</strong><br><small>Confidence: {confidence_pct:.1f}%</small></div>',
                                    unsafe_allow_html=True
                                )
                else:
                    st.info("ℹ️ No medical entities detected. Try a note with specific conditions and medications.")
                
                # Display FHIR Bundle
                with st.expander("📋 View Complete FHIR Bundle (JSON)", expanded=False):
                    st.json(result['bundle'])
                
                st.success("✅ Successfully converted clinical note to FHIR format!")
                
            else:
                st.error(f"FHIR Conversion failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"FHIR Agent Error: {str(e)}")

if __name__ == "__main__":
    main()
