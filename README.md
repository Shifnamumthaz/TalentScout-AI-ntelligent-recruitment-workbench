##🚀 TalentScout AI

TalentScout AI is an intelligent recruitment workbench built with Python and Streamlit. It leverages Google's Gemini 2.0 Flash models to automate the tedious parts of hiring: parsing job descriptions, screening PDF resumes, ranking candidates, and generating tailored interview guides.

##✨ Features

📄 Job Description Analysis: Automatically extracts job titles, required technical skills, soft skills, and experience levels from raw text.
📥 Bulk Resume Parsing: Upload multiple PDF resumes at once. The tool extracts text and analyzes candidates in real-time.
🎯 Smart Scoring: Rates every candidate from 0-100 based on how well they match the specific Job Description.
🔍 Gap Analysis: Identifies exactly which skills a candidate is missing compared to the requirements.
🗣️ Interview Guide Generator: Creates a unique interview script for each shortlisted candidate, including:
Hard Technical Questions (based on the specific role).
Behavioral Questions (Culture fit).
"Curveball" Questions (Problem-solving).
Evaluation Rubric (What a "Good" vs "Bad" answer looks like).
📊 Interactive Dashboard: A sortable, filterable table to rank candidates by score.

##🛠️ Tech Stack

Frontend: Streamlit (Web UI)
AI Model: Google Gemini (gemini-2.0-flash / gemini-pro) via google-generativeai
PDF Processing: pdfplumber
Data Handling: pandas

##⚙️ Prerequisites

Python 3.8+ installed on your system.
A Google Gemini API Key.
Get one here: Google AI Studio

##📦 Installation

```
Clone or Download this project folder.
Open your terminal and navigate to the project folder.
Install dependencies:
bash
pip install -r requirements.txt
```

##🚀 Usage

```
Start the application:
bash
streamlit run app.py
A new tab will open in your web browser (usually http://localhost:8501).
Enter your API Key in the sidebar (left panel).
Paste a Job Description in the left text area.
Upload PDF Resumes in the right file uploader.
```

Click "Analyze Candidates".


