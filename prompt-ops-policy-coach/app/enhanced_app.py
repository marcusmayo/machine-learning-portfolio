"""
Policy Coach Pro - Enhanced Version with REAL LLM Integration (Complete Fixed Version)
Production-ready Q&A system with multiple prompt frameworks and OpenAI integration
"""

import streamlit as st
import json
import numpy as np
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple
import hashlib

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    # Try to import OpenAI (NEW v1.0+ format)
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    st.warning("OpenAI not installed. Install with: pip install openai")

st.set_page_config(page_title="Policy Coach Pro", page_icon="🤖", layout="wide")
st.title("🤖 Policy Coach Pro - Enterprise RAG System")
st.markdown("*Advanced Q&A with Multiple Prompt Frameworks & Real LLM Integration*")

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0
if 'cache' not in st.session_state:
    st.session_state.cache = {}

# OpenAI Configuration (NEW v1.0+ format)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None

if OPENAI_API_KEY and OPENAI_AVAILABLE:
    try:
        # Create OpenAI client (NEW way)
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        st.sidebar.success("🔗 OpenAI client initialized successfully!")
    except Exception as e:
        st.sidebar.error(f"Failed to initialize OpenAI client: {e}")

# Load data
@st.cache_data
def load_index():
    try:
        with open('index/faiss/chunks.json', 'r') as f:
            chunks = json.load(f)
        embeddings = np.load('index/faiss/embeddings.npy')
        with open('index/faiss/vocabulary.json', 'r') as f:
            vocabulary = json.load(f)
        return chunks, embeddings, vocabulary
    except Exception as e:
        st.error(f"Error loading index: {str(e)}")
        return None, None, None

# Prompt Templates - REAL FRAMEWORK PROMPTS
PROMPT_FRAMEWORKS = {
    "CRAFT Framework": {
        "name": "CRAFT Framework",
        "description": "Context, Role, Action, Format, Tone - Structured professional response",
        "system_prompt": """You are a Policy Compliance Advisor using the CRAFT framework.

Context: You answer employee questions about company policies using provided documentation.
Role: Senior Compliance Officer with deep policy knowledge.
Action: Provide clear, accurate answers with proper citations.
Format: Structure your response with clear sections and bullet points when helpful.
Tone: Professional, authoritative, but approachable.

Always cite your sources and be explicit about what the policy states.""",
        "user_template": """Question: {question}

Policy Information:
{context}

Please answer using the CRAFT framework approach: be structured, professional, and cite sources clearly."""
    },
    
    "CRISPE Framework": {
        "name": "CRISPE Framework", 
        "description": "Capacity, Role, Insight, Statement, Personality - Empathetic approach",
        "system_prompt": """You are a helpful HR Policy Assistant using the CRISPE framework.

Capacity: You have access to complete company policy documentation.
Role: Supportive HR advisor who understands employee needs.
Insight: Employees need clear, practical guidance they can act on.
Statement: Provide direct answers with context.
Personality: Warm, helpful, and understanding while remaining accurate.

Focus on being empathetic while providing precise policy information.""",
        "user_template": """I need help understanding this policy question: {question}

Here's the relevant policy information:
{context}

Please help me understand what this means for my situation, keeping in mind I want to follow company policy correctly."""
    },
    
    "Chain of Thought": {
        "name": "Chain of Thought",
        "description": "Step-by-step reasoning approach",
        "system_prompt": """You are a Policy Analyst who thinks through problems step-by-step.

Always break down your reasoning process clearly:
1. First, understand what the employee is asking
2. Identify which policies apply
3. Analyze the policy language carefully
4. Consider any exceptions or special cases
5. Provide a clear conclusion

Show your thinking process so employees can understand how you reached your answer.""",
        "user_template": """Let me think through this policy question step by step: {question}

Policy Documentation:
{context}

Please walk me through your reasoning process to answer this question."""
    },
    
    "Constitutional AI": {
        "name": "Constitutional AI",
        "description": "Principles-based with self-checking",
        "system_prompt": """You are a Policy Guide that follows constitutional AI principles.

Core Principles:
- Always be helpful and accurate
- Be transparent about limitations
- Admit when information is unclear
- Encourage employees to seek clarification when needed
- Never guess or make up policy details

Self-check your responses to ensure they meet these principles.""",
        "user_template": """Policy Question: {question}

Available Information:
{context}

Please provide guidance following constitutional AI principles: be helpful, accurate, and transparent about any limitations."""
    },
    
    "ReAct (Reasoning + Acting)": {
        "name": "ReAct Framework",
        "description": "Combines reasoning with action-oriented guidance",
        "system_prompt": """You are an Action-Oriented Policy Advisor using ReAct methodology.

For each question:
1. THINK: Reason about what policy applies
2. ACT: Provide specific actionable guidance
3. OBSERVE: Note what additional information might be needed

Focus on giving employees clear next steps they can take.""",
        "user_template": """Employee Question: {question}

Policy Information:
{context}

Using ReAct methodology, please provide reasoning AND specific actions the employee should take."""
    }
}

def search_chunks(query: str, chunks: List[Dict], embeddings: np.ndarray, 
                 vocabulary: List[str], top_k: int = 3) -> List[Dict]:
    """Search for relevant chunks using embeddings"""
    try:
        word_to_idx = {w: i for i, w in enumerate(vocabulary)}
        query_vec = np.zeros(len(vocabulary))
        
        for word in query.lower().split():
            if word in word_to_idx:
                query_vec[word_to_idx[word]] = 1
        
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec = query_vec / norm
        
        similarities = embeddings.dot(query_vec)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append({
                    'text': chunks[idx]['text'],
                    'source': chunks[idx]['source'],
                    'score': float(similarities[idx])
                })
        return results
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []

def get_openai_response(question: str, context: str, framework: str, model: str = "gpt-4o-mini") -> Tuple[str, float]:
    """Get response from OpenAI using the NEW v1.0+ API format"""
    if not openai_client:
        return None, 0.0
    
    try:
        framework_config = PROMPT_FRAMEWORKS[framework]
        
        # Format the user message with context
        user_message = framework_config["user_template"].format(
            question=question,
            context=context
        )
        
        # Make OpenAI API call (NEW v1.0+ format)
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": framework_config["system_prompt"]},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        # Calculate cost (rough estimate for gpt-4o-mini)
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        # Updated pricing for gpt-4o-mini (as of 2024)
        input_cost = prompt_tokens * 0.00015 / 1000   # $0.15 per 1K tokens
        output_cost = completion_tokens * 0.0006 / 1000  # $0.60 per 1K tokens
        total_cost = input_cost + output_cost
        
        return answer, total_cost
        
    except Exception as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return None, 0.0

def get_mock_response(question: str, context: str, framework: str) -> str:
    """Generate framework-specific mock responses"""
    q_lower = question.lower()
    
    # Determine base information based on question content
    if "gym" in q_lower or "fitness" in q_lower:
        base_facts = {
            "answer": "Gym memberships are NOT reimbursable",
            "exception": "May be covered if part of wellness program",
            "source": "Expense Policy"
        }
    elif "vacation" in q_lower or "days off" in q_lower or "pto" in q_lower:
        base_facts = {
            "answer": "10 days (Year 1-2), 15 days (Year 3-5), 20 days (Year 6+)",
            "exception": "2 weeks advance notice required",
            "source": "Vacation Policy"
        }
    elif "remote" in q_lower or "work from home" in q_lower or "wfh" in q_lower:
        base_facts = {
            "answer": "2 days per week standard, full remote needs director approval",
            "exception": "Must have 90+ days tenure",
            "source": "Remote Work Policy"
        }
    elif "meal" in q_lower or "expense" in q_lower:
        base_facts = {
            "answer": "Breakfast $15, Lunch $25, Dinner $40 daily limits",
            "exception": "Receipts required for expenses over $25",
            "source": "Expense Policy"
        }
    else:
        base_facts = {
            "answer": "Please refer to policy documents for guidance",
            "exception": "Contact HR for specific situations",
            "source": "Policy Documents"
        }
    
    # Format response based on selected framework
    if framework == "CRAFT Framework":
        return f"""**CRAFT Framework Response**

**Context:** Company policy inquiry regarding employee benefits/expenses
**Role:** Policy Compliance Advisor
**Action:** Providing definitive policy interpretation
**Format:** Structured response with clear sections
**Tone:** Professional and authoritative

**ANSWER:** {base_facts['answer']}

**IMPORTANT EXCEPTION:** {base_facts['exception']}

**POLICY SOURCE:** {base_facts['source']}
**COMPLIANCE STATUS:** This interpretation aligns with current company policies
**NEXT STEPS:** Review full policy document for additional details"""
    
    elif framework == "CRISPE Framework":
        return f"""**CRISPE Framework Response**

Hi there! I understand you need clarity on this policy - I'm here to help! 😊

**Here's what I found:** {base_facts['answer']}

**Important to know:** {base_facts['exception']}

**What this means for you:**
- The policy is designed to be fair and consistent
- There are specific guidelines to follow
- I want to make sure you have everything you need

**My recommendation:** Check with your manager if you have specific circumstances, and always feel free to reach out to HR with questions!

**Source:** {base_facts['source']}
**Remember:** We're here to support you in following policies correctly! 🎯"""
    
    elif framework == "Chain of Thought":
        return f"""**Chain of Thought Analysis**

Let me work through this step-by-step:

**Step 1: Understanding Your Question**
You're asking about: {question}

**Step 2: Policy Identification**
This falls under: {base_facts['source']}

**Step 3: Policy Analysis**
The core policy states: {base_facts['answer']}

**Step 4: Exception Analysis**
However, there's an important consideration: {base_facts['exception']}

**Step 5: Practical Application**
In your specific case, this means the standard rule applies unless you meet the exception criteria.

**Step 6: Final Determination**
Based on this reasoning chain: {base_facts['answer']}

**Logical Path:** Question → Policy → Rules → Exceptions → Application → Conclusion
**Confidence Level:** High (based on explicit policy language)"""
    
    elif framework == "Constitutional AI":
        return f"""**Constitutional AI Response**

**Being Helpful:** I want to give you accurate information: {base_facts['answer']}

**Being Honest:** I should mention: {base_facts['exception']}

**Being Transparent:** My information comes from: {base_facts['source']}

**Acknowledging Limitations:** While this covers the general policy, your specific situation might have nuances I can't account for.

**Encouraging Verification:** I recommend:
- Double-checking the full policy document
- Discussing with your manager for context
- Contacting HR for official confirmation

**Principle Check:** ✅ Helpful ✅ Honest ✅ Transparent ✅ Encouraging proper verification"""
    
    elif framework == "ReAct (Reasoning + Acting)":
        return f"""**ReAct Framework Response**

**THINK:** You're asking about policy rules. Let me reason through this...
The policy clearly states: {base_facts['answer']}

**ACT:** Here's what you should do:
1. **Immediate Action:** {base_facts['answer']} applies to your situation
2. **Check Exception:** Verify if this applies: {base_facts['exception']}
3. **Document Review:** Read the full {base_facts['source']} for details
4. **Manager Discussion:** Talk to your manager about your specific case
5. **HR Consultation:** Get official confirmation if needed

**OBSERVE:** What additional information might help?
- Your specific tenure/situation
- Any special programs you're enrolled in
- Recent policy updates

**Next Action Items:**
- [ ] Review full policy document
- [ ] Prepare questions for manager
- [ ] Schedule HR consultation if needed

**Action-Oriented Summary:** Start with the standard rule, check for exceptions, then verify with appropriate people."""
    
    else:
        return f"{base_facts['answer']}\n\nNote: {base_facts['exception']}\n\nSource: {base_facts['source']}"

# Load data
chunks, embeddings, vocabulary = load_index()

if chunks is None:
    st.error("Please run `python src/build_index_ultra_simple.py` first!")
    st.stop()

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key Status
    st.subheader("🔑 API Configuration")
    if OPENAI_API_KEY and OPENAI_AVAILABLE and openai_client:
        st.success(f"✅ OpenAI API Key configured")
        st.info(f"Key: {OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}")
        use_real_llm = st.checkbox("Use Real OpenAI LLM", value=True)
    else:
        st.warning("⚠️ No OpenAI API Key found or client failed to initialize")
        st.info("Add OPENAI_API_KEY to .env file for real LLM responses")
        use_real_llm = False
    
    # Model Selection
    if use_real_llm:
        model_name = st.selectbox(
            "OpenAI Model",
            ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"],
            help="gpt-4o-mini is cheapest"
        )
    else:
        st.info("Using Mock LLM (no API calls)")
        model_name = "mock-llm"
    
    # Framework Selection - THIS IS KEY!
    st.subheader("🧠 Prompt Framework")
    selected_framework = st.selectbox(
        "Select Framework",
        list(PROMPT_FRAMEWORKS.keys()),
        help="Different frameworks will produce different response styles"
    )
    
    # Show framework description
    st.info(f"📝 {PROMPT_FRAMEWORKS[selected_framework]['description']}")
    
    # Search Settings
    st.subheader("🔍 Search Settings")
    top_k = st.slider("Number of source chunks", 1, 5, 3)
    
    # Metrics Display
    st.subheader("📊 Session Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", 3)
        st.metric("Chunks", len(chunks))
    with col2:
        st.metric("Queries", len(st.session_state.query_history))
        st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")
    
    # Sample Questions
    st.subheader("💡 Try These Questions")
    sample_questions = [
        "Can I expense my gym membership?",
        "How many vacation days do I get?",
        "What's the remote work policy?",
        "What are meal expense limits?",
        "Do I need approval for hotel bookings?",
        "Home office equipment allowance?"
    ]
    
    for q in sample_questions:
        if st.button(q, key=f"sample_{q}"):
            st.session_state.question = q

# Main Content Area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎯 Ask Your Policy Question")
    
    # Question Input
    question = st.text_area(
        "Enter your question:",
        value=st.session_state.get('question', ''),
        height=120,
        placeholder="Example: Can I expense my gym membership?",
        help="Ask any question about company policies"
    )
    
    # Search and Answer Button
    if st.button("🔍 Get Answer", type="primary", use_container_width=True):
        if question:
            # Search for relevant chunks
            with st.spinner("🔍 Searching policy documents..."):
                search_results = search_chunks(question, chunks, embeddings, vocabulary, top_k)
            
            if search_results:
                # Prepare context
                context = "\n\n".join([f"[{r['source']}]: {r['text']}" for r in search_results])
                
                # Generate response
                start_time = time.time()
                
                if use_real_llm and openai_client:
                    with st.spinner(f"🤖 Generating answer using {selected_framework} with OpenAI..."):
                        answer, cost = get_openai_response(question, context, selected_framework, model_name)
                        response_time = time.time() - start_time
                        
                        if answer is None:
                            st.error("Failed to get OpenAI response, using mock instead")
                            answer = get_mock_response(question, context, selected_framework)
                            cost = 0.0
                else:
                    with st.spinner(f"🎭 Generating mock answer using {selected_framework}..."):
                        answer = get_mock_response(question, context, selected_framework)
                        cost = 0.0
                        response_time = time.time() - start_time
                
                # Update session state
                st.session_state.total_cost += cost
                st.session_state.query_history.append({
                    'question': question,
                    'framework': selected_framework,
                    'model': model_name,
                    'cost': cost,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Display Results
                st.markdown("### 📝 Answer")
                st.success(answer)
                
                # Performance Metrics
                st.markdown("### 📊 Response Metrics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Response Time", f"{response_time:.2f}s")
                with col2:
                    st.metric("Sources Found", len(search_results))
                with col3:
                    st.metric("Query Cost", f"${cost:.4f}")
                with col4:
                    st.metric("Model Used", model_name)
                
                # Framework Used Indicator
                st.info(f"🧠 Generated using: **{selected_framework}**")
                
                # Source Documents
                st.markdown("### 📚 Source Documents")
                for i, result in enumerate(search_results, 1):
                    with st.expander(f"Source {i}: {result['source']} (Relevance: {result['score']:.3f})"):
                        st.text(result['text'])
                        
            else:
                st.warning("No relevant policy documents found. Try rephrasing your question.")
        else:
            st.warning("Please enter a question!")

with col2:
    st.header("📈 System Dashboard")
    
    # Framework Comparison - COMPLETE VERSION
    with st.expander("🔄 Framework Comparison", expanded=True):
        st.markdown("**Test the same question with different frameworks!**")
        st.markdown("""
        **Available Frameworks:**
        
        🏗️ **CRAFT Framework**
        • Context, Role, Action, Format, Tone
        • Structured, professional responses with clear sections
        • Best for: Official policy interpretations, compliance guidance
        
        🤝 **CRISPE Framework**  
        • Capacity, Role, Insight, Statement, Personality
        • Empathetic, user-focused approach with warmth
        • Best for: Employee support, personal situations
        
        🧠 **Chain of Thought**
        • Step-by-step reasoning and analysis
        • Shows thinking process transparently  
        • Best for: Complex policy questions, detailed explanations
        
        ⚖️ **Constitutional AI**
        • Transparent, principle-based responses
        • Self-checking with clear limitations
        • Best for: Ethical considerations, uncertain situations
        
        🎯 **ReAct (Reasoning + Acting)**
        • Action-oriented with clear next steps
        • Combines reasoning with practical guidance
        • Best for: Implementation questions, "what should I do?"
        
        💡 **Pro Tip:** Try asking the same question with different frameworks to see how AI reasoning styles affect the response quality and format!
        """)
    
    # Recent Queries - FIXED VERSION
    with st.expander("📜 Query History"):
        try:
            if 'query_history' in st.session_state and st.session_state.query_history:
                # Show the most recent 5 queries
                recent_queries = st.session_state.query_history[-5:] if len(st.session_state.query_history) > 5 else st.session_state.query_history
                
                for i, query_data in enumerate(reversed(recent_queries)):
                    # Safely access query data with defaults
                    question = query_data.get('question', 'Unknown question')[:40]
                    framework = query_data.get('framework', 'Unknown framework')
                    cost = query_data.get('cost', 0.0)
                    timestamp = query_data.get('timestamp', 'Unknown time')
                    
                    # Display the query
                    st.markdown(f"**Q{len(recent_queries)-i}:** {question}...")
                    st.caption(f"{framework} • ${cost:.4f} • {timestamp[:10]}")
                    
                    if i < len(recent_queries) - 1:  # Add separator except for last item
                        st.divider()
            else:
                st.info("No queries yet - ask your first question!")
        except Exception as e:
            st.error(f"Error loading query history: {str(e)}")
            st.info("Query history will be available after your first question.")
    
    # Export Functionality - FIXED VERSION  
    with st.expander("💾 Export Data"):
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export Query History", key="export_history"):
                    if 'query_history' in st.session_state and st.session_state.query_history:
                        history_json = json.dumps(st.session_state.query_history, indent=2)
                        st.download_button(
                            "📥 Download JSON",
                            data=history_json,
                            file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key="download_json"
                        )
                    else:
                        st.warning("No query history to export.")
            
            with col2:
                if st.button("Clear All Data", key="clear_all"):
                    st.session_state.query_history = []
                    st.session_state.total_cost = 0.0
                    st.session_state.cache = {}
                    st.success("✅ All data cleared!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error in export functionality: {str(e)}")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"💰 Session Cost: ${st.session_state.total_cost:.4f}")
with col2:
    st.caption(f"🔄 Framework: {selected_framework}")
with col3:
    st.caption(f"🤖 Model: {model_name}")

# Debug Information (only show if there are errors)
if st.checkbox("🔧 Show Debug Info", value=False):
    st.subheader("Debug Information")
    st.json({
        "openai_available": OPENAI_AVAILABLE,
        "api_key_present": bool(OPENAI_API_KEY),
        "openai_client_ready": bool(openai_client),
        "chunks_loaded": len(chunks) if chunks else 0,
        "use_real_llm": use_real_llm if 'use_real_llm' in locals() else False,
        "selected_framework": selected_framework,
        "session_state_keys": list(st.session_state.keys())
    })
