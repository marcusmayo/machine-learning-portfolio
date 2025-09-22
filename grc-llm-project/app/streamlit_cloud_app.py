import streamlit as st
import time
import os

# Mock responses for demo purposes (since full model may not load on free tier)
DEMO_RESPONSES = {
    "Which SOC 2 control covers password requirements?": {
        "answer": "SOC 2 CC6.1 covers password requirements. This control requires organizations to implement logical access security measures, including password policies that enforce complexity, minimum length, and regular rotation. The control ensures that passwords are sufficiently complex to prevent unauthorized access to the system.",
        "time": 2.3
    },
    "What does ISO 27001 say about access reviews?": {
        "answer": "ISO 27001 A.9.2.5 requires regular reviews of user access rights. Organizations must conduct periodic reviews to ensure that access rights remain appropriate and aligned with business needs. The standard recommends formal access reviews at planned intervals and whenever there are significant changes to employment or responsibilities.",
        "time": 1.8
    },
    "Do we need encryption at rest for HIPAA?": {
        "answer": "Yes, HIPAA requires protecting ePHI through appropriate technical safeguards. While encryption at rest is addressable rather than required, it's considered a standard implementation. The Security Rule allows covered entities to implement alternative measures only if they can document that encryption is not reasonable and appropriate for their environment.",
        "time": 2.1
    },
    "What backup requirements does ISO 27001 specify?": {
        "answer": "ISO 27001 A.12.3.1 requires organizations to implement backup procedures for information and software. The standard mandates regular backup of data, testing of backup media, and documented recovery procedures. Backups should be stored securely and tested periodically to ensure data integrity and availability.",
        "time": 1.9
    }
}

@st.cache_data
def get_demo_response(question):
    """Get demo response for common compliance questions"""
    # Check for exact matches first
    if question in DEMO_RESPONSES:
        return DEMO_RESPONSES[question]
    
    # Check for partial matches
    for demo_q, response in DEMO_RESPONSES.items():
        if any(word.lower() in question.lower() for word in demo_q.split() if len(word) > 3):
            return response
    
    # Default response for other questions
    return {
        "answer": "This is a demo version running on Streamlit Cloud. The full model provides detailed compliance guidance for SOC 2, ISO 27001, and HIPAA frameworks. For complete functionality, please run the local version with the full fine-tuned model.",
        "time": 1.5
    }

def main():
    st.set_page_config(
        page_title="GRC Compliance LLM - Demo",
        page_icon="🛡️",
        layout="centered"
    )
    
    # Header
    st.title("🛡️ GRC Compliance Chatbot")
    st.markdown("**SOC 2 • ISO 27001 • HIPAA Compliance Assistant**")
    
    # Demo notice
    st.info("📌 **Demo Version**: This is a lightweight demo running on Streamlit Cloud. The full fine-tuned model is available in the GitHub repository.")
    
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # Sidebar
    with st.sidebar:
        st.header("About This Demo")
        st.markdown("""
        **Full Project Features:**
        - Fine-tuned TinyLlama 1.1B model
        - LoRA adapters for compliance
        - AWS SageMaker deployment
        - Custom compliance dataset
        
        **Tech Stack:**
        - Python, Transformers, PyTorch
        - Streamlit, AWS, Docker
        - LoRA fine-tuning, QLoRA
        """)
        
        st.header("Example Questions")
        examples = list(DEMO_RESPONSES.keys())
        
        for example in examples:
            if st.button(example, key=f"example_{hash(example)}", use_container_width=True):
                st.session_state.current_question = example
                st.rerun()
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.conversation_history = []
            st.rerun()
    
    # Chat interface
    st.markdown("---")
    
    # Display conversation history
    if st.session_state.conversation_history:
        for i, (q, a, response_time) in enumerate(st.session_state.conversation_history):
            with st.container():
                st.markdown(f"**You:** {q}")
            with st.container():
                st.markdown(f"**Assistant:** {a}")
                st.caption(f"*Response time: {response_time:.1f}s*")
                st.markdown("---")
    
    # Question input
    question = st.text_area(
        "Ask your compliance question:",
        value=st.session_state.get('current_question', ''),
        height=100,
        placeholder="e.g., Which SOC 2 control covers password management?",
        key="question_input"
    )
    
    # Submit button
    if st.button("📤 Send", type="primary", use_container_width=True):
        if question.strip():
            with st.spinner("Analyzing compliance requirements..."):
                time.sleep(1)  # Simulate processing
                response = get_demo_response(question)
                
                # Add to conversation history
                st.session_state.conversation_history.append((
                    question, 
                    response["answer"], 
                    response["time"]
                ))
                
                # Clear current question
                st.session_state.current_question = ""
                
                st.rerun()
        else:
            st.warning("Please enter a compliance question")
    
    # Footer
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**[View Full Project](https://github.com/marcusmayo/machine-learning-portfolio/tree/main/grc-llm-project)**")
    with col2:
        st.markdown("**[Download Model](https://github.com/marcusmayo/machine-learning-portfolio/blob/main/grc-llm-project/download_model.py)**")

if __name__ == "__main__":
    main()
