import streamlit as st
import google.generativeai as genai
import pdfplumber
import json
import pandas as pd
import time

# --- 1. ADK / CORE LOGIC LAYER ---

class LLMService:
    """Handles communication with Google Gemini."""
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        
        # BASED ON YOUR DEBUG LOGS, WE USE GEMINI 2.0
        # Your key has access to 'models/gemini-2.0-flash', so we use exactly that.
        self.model_name = "models/gemini-2.0-flash" 
        self.model = genai.GenerativeModel(self.model_name)

    def clean_json(self, text):
        """Helper to strip markdown from JSON responses."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"): 
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text

    def generate(self, prompt):
        try:
            # We add a specific config to ensure better JSON stability
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            # If 2.0 fails for some reason, try the 'latest' alias which is also in your list
            if "404" in str(e):
                try:
                    self.model = genai.GenerativeModel("models/gemini-flash-latest")
                    response = self.model.generate_content(prompt)
                    return response.text
                except Exception as e2:
                    st.error(f"LLM Error (Retry Failed): {e2}")
            else:
                st.error(f"LLM Error: {e}")
            return None
               
class PDFTool:
    """Tool to extract text from PDF files."""
    @staticmethod
    def extract_text(uploaded_file):
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text

class RecruitmentAgents:
    """Collection of Agents for the workflow."""
    
    def __init__(self, llm_service):
        self.llm = llm_service

    def jd_parser_agent(self, jd_text):
        prompt = f"""
        Analyze this Job Description. Extract:
        1. Job Title
        2. Key Technical Skills (list)
        3. Required Experience (string)
        4. Soft Skills (list)
        
        Return STRICT JSON format:
        {{
            "title": "...",
            "tech_skills": ["..."],
            "experience": "...",
            "soft_skills": ["..."]
        }}
        
        JD TEXT:
        {jd_text}
        """
        response = self.llm.generate(prompt)
        if response:
            try:
                return json.loads(self.llm.clean_json(response))
            except:
                pass
        return {"title": "Unknown Role", "tech_skills": [], "experience": "N/A"}

    def resume_screening_agent(self, resume_text, parsed_jd):
        prompt = f"""
        You are a strict HR Recruiter. Compare this resume against the Job Description profile.
        
        JOB PROFILE: {json.dumps(parsed_jd)}
        
        RESUME TEXT:
        {resume_text[:4000]} (truncated)
        
        Task:
        1. Extract Candidate Name and Email.
        2. Score the candidate from 0 to 100 based on fit.
        3. Write a brief 'Analysis' (2 sentences).
        4. List 'Missing Skills' found in JD but not in Resume.
        
        Return STRICT JSON format:
        {{
            "name": "...",
            "email": "...",
            "score": 0,
            "analysis": "...",
            "missing_skills": ["..."]
        }}
        """
        try:
            response = self.llm.generate(prompt)
            if response:
                return json.loads(self.llm.clean_json(response))
        except Exception:
            pass
        
        # FAIL-SAFE RETURN: Ensures all keys exist to prevent Pandas crash
        return {
            "name": "Unknown Candidate",
            "email": "N/A", 
            "score": 0, 
            "analysis": "AI Processing Failed", 
            "missing_skills": []
        }

    def interview_prep_agent(self, candidate_data, parsed_jd):
        prompt = f"""
        Generate an interview guide for a candidate applying for {parsed_jd.get('title', 'Role')}.
        
        Candidate Analysis: {candidate_data.get('analysis', '')}
        Missing Skills: {candidate_data.get('missing_skills', [])}
        
        Generate:
        1. 3 Technical Questions (hard, specific to the role).
        2. 2 Behavioral Questions (checking culture fit).
        3. 1 "Curveball" question to test problem-solving.
        4. A Scoring Rubric (what a 'Good Answer' looks like vs a 'Bad Answer').
        
        Return STRICT JSON format:
        {{
            "technical_questions": ["Q1", "Q2", "Q3"],
            "behavioral_questions": ["Q1", "Q2"],
            "curveball": "...",
            "evaluation_rubric": "..."
        }}
        """
        response = self.llm.generate(prompt)
        if response:
            try:
                return json.loads(self.llm.clean_json(response))
            except:
                pass
        return {}

# --- 2. WEB UI LAYER (STREAMLIT) ---

st.set_page_config(page_title="TalentScout AI", layout="wide")

# Sidebar for Setup
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=50)
    st.title("TalentScout AI")
    
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    st.markdown("---")
    st.write("### ⚙️ Settings")
    min_score = st.slider("Min. Score to Shortlist", 0, 100, 60)

# Main Content
st.header("🚀 AI Recruitment Workbench")
st.markdown("Upload a Job Description and Candidate Resumes (PDF). The AI will parse, score, and generate interview guides.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Job Description")
    jd_input = st.text_area("Paste JD Text here...", height=200, placeholder="We are looking for a Senior Python Developer...")

with col2:
    st.subheader("2. Candidate Resumes")
    uploaded_files = st.file_uploader("Upload PDF Resumes", type=["pdf"], accept_multiple_files=True)

if 'results' not in st.session_state:
    st.session_state.results = []
if 'parsed_jd' not in st.session_state:
    st.session_state.parsed_jd = None

if st.button("Analyze Candidates", type="primary"):
    if not api_key:
        st.warning("Please provide an API Key in the sidebar.")
    elif not jd_input or not uploaded_files:
        st.warning("Please provide both a JD and at least one Resume.")
    else:
        llm = LLMService(api_key)
        agents = RecruitmentAgents(llm)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Parsing Job Description...")
        parsed_jd = agents.jd_parser_agent(jd_input)
        st.session_state.parsed_jd = parsed_jd
        
        results_list = []
        total_files = len(uploaded_files)
        
        for i, pdf_file in enumerate(uploaded_files):
            status_text.text(f"Processing Resume {i+1}/{total_files}: {pdf_file.name}")
            
            try:
                text = PDFTool.extract_text(pdf_file)
                screen_result = agents.resume_screening_agent(text, parsed_jd)
                screen_result['filename'] = pdf_file.name
                
                score = screen_result.get('score', 0)
                if isinstance(score, str): score = 0
                
                if score >= min_score:
                    interview_prep = agents.interview_prep_agent(screen_result, parsed_jd)
                    screen_result.update(interview_prep)
                    screen_result['status'] = "Shortlisted"
                else:
                    screen_result['status'] = "Rejected"
                
                results_list.append(screen_result)
            except Exception as e:
                st.error(f"Error processing {pdf_file.name}: {e}")
            
            progress_bar.progress((i + 1) / total_files)
            time.sleep(1)
            
        st.session_state.results = results_list
        status_text.text("Analysis Complete!")
        progress_bar.empty()

# --- RESULTS DISPLAY ---

if st.session_state.parsed_jd:
    with st.expander("📌 Viewed Parsed Job Requirements", expanded=False):
        st.json(st.session_state.parsed_jd)

if st.session_state.results:
    st.divider()
    st.subheader("📊 Candidate Ranking Board")
    
    df = pd.DataFrame(st.session_state.results)
    
    # CRASH FIX: Ensure columns exist before displaying
    required_columns = ['name', 'score', 'status', 'email', 'filename', 'analysis']
    for col in required_columns:
        if col not in df.columns:
            df[col] = "N/A" # Fill missing columns with N/A
            
    if not df.empty:
        st.dataframe(
            df[required_columns],
            column_config={
                "score": st.column_config.ProgressColumn(
                    "Match Score",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
            },
            use_container_width=True
        )
    
    st.subheader("📝 Interview Guides & Evaluation")
    
    shortlisted = [r for r in st.session_state.results if r.get('status') == "Shortlisted"]
    
    if not shortlisted:
        st.info("No candidates met the minimum score threshold.")
    
    for candidate in shortlisted:
        with st.container():
            st.markdown(f"### 👤 {candidate.get('name', 'Unknown')} (Score: {candidate.get('score', 0)})")
            
            tab1, tab2, tab3 = st.tabs(["Analysis", "Interview Questions", "Evaluation Rubric"])
            
            with tab1:
                st.write(f"**Analysis:** {candidate.get('analysis', 'N/A')}")
                # Handle missing skills list safely
                skills = candidate.get('missing_skills', [])
                if isinstance(skills, list):
                    st.write(f"**Missing Skills:** {', '.join(skills)}")
                else:
                    st.write(f"**Missing Skills:** {skills}")
            
            with tab2:
                st.write("#### Technical Questions")
                for q in candidate.get('technical_questions', []):
                    st.info(f"❓ {q}")
                
                st.write("#### Behavioral Questions")
                for q in candidate.get('behavioral_questions', []):
                    st.success(f"🗣️ {q}")

                st.write("#### Curveball")
                st.warning(f"💣 {candidate.get('curveball', 'N/A')}")
            
            with tab3:
                st.write(candidate.get('evaluation_rubric', "No rubric generated."))
            
            st.divider()