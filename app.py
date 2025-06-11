import gradio as gr
import anthropic
import PyPDF2
import docx
import pandas as pd
import re
import os
from datetime import datetime

# Set API key from environment variable for security
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

def extract_text_from_file(file):
    if file is None:
        return ""
    file_extension = file.name.lower().split('.')[-1]
    try:
        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif file_extension in ['docx', 'doc']:
            doc = docx.Document(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        elif file_extension == 'txt':
            content = file.read()
            if isinstance(content, bytes):
                return content.decode('utf-8')
            return content
        else:
            return f"Unsupported file format: {file.name}"
    except Exception as e:
        return f"Error reading {file.name}: {str(e)}"

def get_processed_filenames(existing_data):
    processed_files = set()
    if existing_data is not None and not existing_data.empty and 'File' in existing_data.columns:
        for _, row in existing_data.iterrows():
            filename = str(row['File'])
            clean_filename = re.sub(r'^[🟢🟠🔴⚪] ', '', filename)
            processed_files.add(clean_filename)
    return processed_files

def analyze_single_resume(client, resume_text, job_title, job_responsibilities, filename):
    prompt = f"""You are an expert HR analyst. Please analyze this candidate's resume against the job requirements using a 2-criteria scoring system.

JOB TITLE: {job_title}

JOB ROLES AND RESPONSIBILITIES:
{job_responsibilities}

CANDIDATE RESUME:
{resume_text}

SCORING METHODOLOGY:
Use ONLY these 2 criteria to score the candidate on a 1-10 scale:

1. JOB DESCRIPTION SIMILARITY (65% weight - Max 6.5 points):
   - High Overlap (5.5-6.5 points): 70%+ responsibility match, same industry/domain, strong functional alignment
   - Moderate Overlap (3.5-5.4 points): 40-69% responsibility match, related industry, some transferable skills  
   - Low Overlap (0-3.4 points): <40% responsibility match, different industry, minimal skill alignment

2. DESIGNATION MATCH (35% weight - Max 3.5 points):
   - Exact/Similar Match (2.5-3.5 points): Same title or very similar level
   - Related Match (1.5-2.4 points): Adjacent level or related function
   - Poor Match (0-1.4 points): Unrelated title or major level gap

FINAL DECISION LOGIC:
- Score 8-10: GOOD MATCH
- Score 5-7: CONSIDERABLE MATCH  
- Score 1-4: REJECT

ANALYSIS INSTRUCTIONS:
1. Extract candidate's personal and professional information
2. Identify candidate's CURRENT job title and responsibilities
3. Calculate Job Description Similarity Score (0-6.5 points)
4. Calculate Designation Match Score (0-3.5 points)
5. Add both scores for final rating (1-10)
6. Determine recommendation based on final score

Please provide your analysis in the following EXACT format:

CANDIDATE_NAME: [Extract full name]
EMAIL: [Extract email address]
PHONE: [Extract phone number]
CURRENT_COMPANY: [Extract CURRENT/most recent ongoing company name]
CURRENT_DESIGNATION: [Extract CURRENT/most recent ongoing job title]
TOTAL_EXPERIENCE: [Extract total years of experience]
JOB_DESC_SCORE: [Score for job description similarity: X.X/6.5]
DESIGNATION_SCORE: [Score for designation match: X.X/3.5]
FINAL_SCORE: [Total score: X.X/10]
RECOMMENDATION: [Either "GOOD MATCH" or "CONSIDERABLE MATCH" or "REJECT"]
REASON: [One sentence explaining the scoring and decision]

If any information is not available in the resume, write "Not Available" for that field."""
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis_text = message.content[0].text
        
        candidate_data = {
            "Name": "Not Available", "Email": "Not Available", "Phone": "Not Available",
            "Current Company": "Not Available", "Current Role": "Not Available", "Experience": "Not Available",
            "Job Desc Score": "Not Available", "Designation Score": "Not Available", "Final Score": "Not Available",
            "Result": "Not Available", "Reason": "Not Available", "File": filename
        }
        
        patterns = {
            "Name": r"CANDIDATE_NAME:\s*(.+)", "Email": r"EMAIL:\s*(.+)", "Phone": r"PHONE:\s*(.+)",
            "Current Company": r"CURRENT_COMPANY:\s*(.+)", "Current Role": r"CURRENT_DESIGNATION:\s*(.+)",
            "Experience": r"TOTAL_EXPERIENCE:\s*(.+)", "Job Desc Score": r"JOB_DESC_SCORE:\s*(.+)",
            "Designation Score": r"DESIGNATION_SCORE:\s*(.+)", "Final Score": r"FINAL_SCORE:\s*(.+)",
            "Result": r"RECOMMENDATION:\s*(.+)", "Reason": r"REASON:\s*(.+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                candidate_data[key] = match.group(1).strip()
        
        # Store original data for full view
        original_data = {
            "Current Company": candidate_data["Current Company"],
            "Current Role": candidate_data["Current Role"],
            "Reason": candidate_data["Reason"],
            "File": os.path.basename(filename)
        }
        
        # Don't truncate data - keep original full text for better visibility
        candidate_data["File"] = os.path.basename(filename)
        candidate_data["_original_data"] = original_data
        
        return candidate_data
        
    except Exception as e:
        return {
            "Name": "Error", "Email": "Error", "Phone": "Error", "Current Company": "Error",
            "Current Role": "Error", "Experience": "Error", "Job Desc Score": "Error",
            "Designation Score": "Error", "Final Score": "Error", "Result": "Error",
            "Reason": f"API Error: {str(e)}", "File": filename,
            "_original_data": {"Current Company": "Error", "Current Role": "Error", 
                              "Reason": f"API Error: {str(e)}", "File": filename}
        }

def add_color_indicators_and_delete_buttons(df):
    """Add color indicators to File Name and delete buttons to each row"""
    if df is None or df.empty:
        return df
    
    df_colored = df.copy()
    
    # Add delete column as first column
    delete_buttons = []
    
    for idx, row in df_colored.iterrows():
        recommendation = str(row['Result']).upper()
        filename = str(row['File'])
        
        # Remove existing color indicators first to avoid duplicates
        clean_filename = re.sub(r'^[🟢🟠🔴⚪] ', '', filename)
        
        # Add delete button for this row (just icon, no text)
        delete_buttons.append("🗑️")
        
        # Add color indicators to filename
        if 'GOOD MATCH' in recommendation:
            df_colored.at[idx, 'File'] = f"🟢 {clean_filename}"
        elif 'CONSIDERABLE MATCH' in recommendation:
            df_colored.at[idx, 'File'] = f"🟠 {clean_filename}"
        elif 'REJECT' in recommendation or 'ERROR' in recommendation:
            df_colored.at[idx, 'File'] = f"🔴 {clean_filename}"
        else:
            df_colored.at[idx, 'File'] = f"⚪ {clean_filename}"
    
    # Insert delete column at the beginning
    df_colored.insert(0, 'Del', delete_buttons)
    
    return df_colored

def create_fullscreen_dataframe(df):
    """Create a full-screen version of the dataframe with original text"""
    if df is None or df.empty:
        return pd.DataFrame({"Message": ["No data available"]})
    
    # Remove delete column for fullscreen view
    df_full = df.copy()
    if 'Del' in df_full.columns:
        df_full = df_full.drop('Del', axis=1)
    
    for idx, row in df_full.iterrows():
        if '_original_data' in row and isinstance(row['_original_data'], dict):
            original_data = row['_original_data']
            df_full.at[idx, 'Current Company'] = original_data.get('Current Company', row['Current Company'])
            df_full.at[idx, 'Current Role'] = original_data.get('Current Role', row['Current Role'])
            df_full.at[idx, 'Reason'] = original_data.get('Reason', row['Reason'])
            clean_file = re.sub(r'^[🟢🟠🔴⚪] ', '', str(row['File']))
            original_file = original_data.get('File', clean_file)
            if '🟢' in str(row['File']):
                df_full.at[idx, 'File'] = f"🟢 {original_file}"
            elif '🟠' in str(row['File']):
                df_full.at[idx, 'File'] = f"🟠 {original_file}"
            elif '🔴' in str(row['File']):
                df_full.at[idx, 'File'] = f"🔴 {original_file}"
            else:
                df_full.at[idx, 'File'] = f"⚪ {original_file}"
    
    if '_original_data' in df_full.columns:
        df_full = df_full.drop('_original_data', axis=1)
    
    return df_full

def show_fullscreen_table(df):
    """Show fullscreen table"""
    return create_fullscreen_dataframe(df), gr.update(visible=True)

def hide_fullscreen_table():
    """Hide fullscreen table"""
    return gr.update(visible=False)

def delete_row_by_index(df, row_index):
    """Delete a specific row by index"""
    if df is None or df.empty:
        return df, "No data to delete"
    
    if row_index < 0 or row_index >= len(df):
        return df, "Invalid row selection"
    
    try:
        # Get the filename of the row being deleted for confirmation
        filename = "Unknown"
        if 'File' in df.columns and row_index < len(df):
            filename = str(df.iloc[row_index]['File'])
            filename = re.sub(r'^[🟢🟠🔴⚪] ', '', filename)  # Remove color indicators
        
        # Remove the row
        df_new = df.drop(df.index[row_index]).reset_index(drop=True)
        
        # Re-add delete buttons with correct indices
        if not df_new.empty:
            df_new = add_color_indicators_and_delete_buttons(df_new.drop('Del', axis=1) if 'Del' in df_new.columns else df_new)
        
        return df_new, f"Successfully deleted candidate: {filename}"
    except Exception as e:
        return df, f"Error deleting row: {str(e)}"

def handle_dataframe_select(df, evt: gr.SelectData):
    """Handle dataframe cell selection for delete functionality"""
    if df is None or df.empty:
        return df, ""
    
    row_idx = evt.index[0]  # Get row index
    col_idx = evt.index[1]  # Get column index
    
    # Check if the delete column (first column) was clicked
    if col_idx == 0:  # Delete column
        return delete_row_by_index(df, row_idx)
    else:
        return df, ""  # No action for other columns

def analyze_multiple_resumes(resume_files, job_title, job_responsibilities, existing_data, is_initial_run=True):
    if not CLAUDE_API_KEY:
        error_df = pd.DataFrame({"Error": ["⚠️ API Key not configured. Please set CLAUDE_API_KEY environment variable."]})
        return error_df, None, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), ""
    
    if not resume_files or len(resume_files) == 0:
        return (existing_data if existing_data is not None else pd.DataFrame(), None, gr.update(visible=False), 
                gr.update(visible=not bool(existing_data is not None and not existing_data.empty)), 
                gr.update(visible=bool(existing_data is not None and not existing_data.empty)), "")
    
    if len(resume_files) > 10:
        return (pd.DataFrame({"Error": ["Maximum 10 resume files allowed"]}), None, gr.update(visible=False), 
                gr.update(visible=True), gr.update(visible=False), "")
    
    if not job_title.strip():
        return (pd.DataFrame({"Error": ["Please enter the job title"]}), None, gr.update(visible=False), 
                gr.update(visible=True), gr.update(visible=False), "")
        
    if not job_responsibilities.strip():
        return (pd.DataFrame({"Error": ["Please enter the roles and responsibilities"]}), None, gr.update(visible=False), 
                gr.update(visible=True), gr.update(visible=False), "")
    
    if len(job_responsibilities) > 1000:
        return (pd.DataFrame({"Error": [f"Roles and Responsibilities exceeds 1000 characters. Current: {len(job_responsibilities)} characters"]}), 
                None, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), "")
    
    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    except Exception as e:
        return (pd.DataFrame({"Error": [f"Error initializing Claude API: {str(e)}"]}), None, gr.update(visible=False), 
                gr.update(visible=True), gr.update(visible=False), "")
    
    all_candidates = []
    skipped_files = []
    
    # Handle existing data
    if existing_data is not None and not existing_data.empty:
        existing_clean = existing_data.copy()
        # Remove delete column if it exists
        if 'Del' in existing_clean.columns:
            existing_clean = existing_clean.drop('Del', axis=1)
        
        processed_files = get_processed_filenames(existing_clean)
        
        if 'File' in existing_clean.columns:
            for idx, row in existing_clean.iterrows():
                filename = str(row['File'])
                clean_filename = re.sub(r'^[🟢🟠🔴⚪] ', '', filename)
                existing_clean.at[idx, 'File'] = clean_filename
        
        existing_records = existing_clean.to_dict('records')
        for record in existing_records:
            if '_original_data' in record:
                del record['_original_data']
        all_candidates.extend(existing_records)
    else:
        processed_files = set()
    
    for resume_file in resume_files:
        filename = os.path.basename(resume_file.name) if hasattr(resume_file, 'name') else "unknown_file"
        if filename in processed_files:
            skipped_files.append(filename)
            continue
        resume_text = extract_text_from_file(resume_file)
        if resume_text.startswith("Error") or resume_text.startswith("Unsupported"):
            error_data = {
                "Name": "File Error", "Email": "N/A", "Phone": "N/A", "Current Company": "N/A",
                "Current Role": "N/A", "Experience": "N/A", "Job Desc Score": "N/A", "Designation Score": "N/A",
                "Final Score": "N/A", "Result": "ERROR", "Reason": resume_text,
                "File": filename, "_original_data": {
                    "Current Company": "N/A", "Current Role": "N/A", "Reason": resume_text, "File": filename
                }
            }
            all_candidates.append(error_data)
        else:
            candidate_data = analyze_single_resume(client, resume_text, job_title, job_responsibilities, filename)
            all_candidates.append(candidate_data)
    
    if not all_candidates:
        return (pd.DataFrame({"Message": ["No candidates processed"]}), None, gr.update(visible=False), 
                gr.update(visible=True), gr.update(visible=False), "")
    
    df = pd.DataFrame(all_candidates)
    column_order = ["File", "Name", "Email", "Phone", "Current Company", "Current Role", "Experience", 
                   "Job Desc Score", "Designation Score", "Final Score", "Result", "Reason"]
    
    for col in column_order:
        if col not in df.columns:
            df[col] = "Not Available"
    
    df_display = df[column_order].copy()
    
    # Add color indicators and delete buttons
    df_display = add_color_indicators_and_delete_buttons(df_display)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"resume_analysis_{timestamp}.csv"
    
    # Create clean version for CSV (without delete column and emoji indicators)
    df_for_csv = df_display.copy()
    if 'Del' in df_for_csv.columns:
        df_for_csv = df_for_csv.drop('Del', axis=1)
    for idx, row in df_for_csv.iterrows():
        filename = str(row['File'])
        clean_filename = re.sub(r'^[🟢🟠🔴⚪] ', '', filename)
        df_for_csv.at[idx, 'File'] = clean_filename
    df_for_csv.to_csv(csv_filename, index=False)
    
    upload_section_visible = is_initial_run and df_display.empty
    quick_section_visible = not df_display.empty
    fullscreen_visible = not df_display.empty
    
    status_msg = ""
    if skipped_files:
        status_msg = f"Skipped {len(skipped_files)} duplicate files: {', '.join(skipped_files)}"
    
    return (df_display, csv_filename, gr.update(visible=fullscreen_visible), 
            gr.update(visible=upload_section_visible), gr.update(visible=quick_section_visible), status_msg)

def show_analyze_button(files):
    if files is not None and len(files) > 0:
        return gr.update(visible=True)
    else:
        return gr.update(visible=False)

def update_char_count_and_button(text):
    char_count = len(text) if text else 0
    button_interactive = char_count <= 1000
    if char_count > 1000:
        char_display = f"⚠️ {char_count}/1000 characters (Exceeds limit!)"
    else:
        char_display = f"✅ {char_count}/1000 characters"
    return char_display, gr.update(interactive=button_interactive), gr.update(interactive=button_interactive)

def clear_all():
    return ([], [], "", "", pd.DataFrame(), None, "✅ 0/1000 characters", gr.update(interactive=True), 
            gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), "")

def show_api_status():
    if CLAUDE_API_KEY:
        return "🟢 API Key Configured"
    else:
        return "🔴 API Key Not Configured - Set CLAUDE_API_KEY environment variable"

css = """
.dataframe {
    font-size: 12px !important; 
    max-height: 500px !important; 
    overflow: auto !important;
    width: 100% !important;
}
.dataframe table {
    table-layout: auto !important; 
    width: 100% !important;
    min-width: 1200px !important;
    word-wrap: break-word !important;
    border-collapse: collapse !important;
}
.dataframe th, .dataframe td {
    padding: 6px 8px !important; 
    text-align: left !important; 
    vertical-align: top !important; 
    white-space: nowrap !important; 
    overflow: visible !important; 
    border: 1px solid #ddd !important;
    resize: horizontal !important;
    min-width: 80px !important;
}
.dataframe th {
    background-color: #f8f9fa !important;
    font-weight: bold !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 10 !important;
    cursor: col-resize !important;
}
.dataframe th:nth-child(1), .dataframe td:nth-child(1) { 
    width: 50px !important; 
    min-width: 50px !important; 
    max-width: 50px !important;
    text-align: center !important;
    cursor: pointer !important;
    background-color: #fee2e2 !important;
    color: #dc2626 !important;
    font-weight: bold !important;
    font-size: 16px !important;
}
.dataframe th:nth-child(2), .dataframe td:nth-child(2) { 
    width: 150px !important; 
    min-width: 120px !important; 
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.dataframe th:nth-child(3), .dataframe td:nth-child(3) { 
    width: 120px !important; 
    min-width: 100px !important; 
}
.dataframe th:nth-child(4), .dataframe td:nth-child(4) { 
    width: 150px !important; 
    min-width: 120px !important; 
}
.dataframe th:nth-child(5), .dataframe td:nth-child(5) { 
    width: 120px !important; 
    min-width: 100px !important; 
}
.dataframe th:nth-child(6), .dataframe td:nth-child(6) { 
    width: 180px !important; 
    min-width: 150px !important; 
}
.dataframe th:nth-child(7), .dataframe td:nth-child(7) { 
    width: 180px !important; 
    min-width: 150px !important; 
}
.dataframe th:nth-child(8), .dataframe td:nth-child(8) { 
    width: 100px !important; 
    min-width: 80px !important; 
}
.dataframe th:nth-child(9), .dataframe td:nth-child(9) { 
    width: 80px !important; 
    min-width: 70px !important; 
}
.dataframe th:nth-child(10), .dataframe td:nth-child(10) { 
    width: 80px !important; 
    min-width: 70px !important; 
}
.dataframe th:nth-child(11), .dataframe td:nth-child(11) { 
    width: 80px !important; 
    min-width: 70px !important; 
}
.dataframe th:nth-child(12), .dataframe td:nth-child(12) { 
    width: 120px !important; 
    min-width: 100px !important; 
}
.dataframe th:nth-child(13), .dataframe td:nth-child(13) { 
    width: 300px !important; 
    min-width: 250px !important; 
    max-width: 500px !important;
    white-space: normal !important; 
    word-wrap: break-word !important;
    overflow: visible !important;
}

.dataframe td:nth-child(1):hover {
    background-color: #fecaca !important;
    transform: scale(1.2) !important;
    transition: all 0.2s !important;
}

.dataframe th:hover {
    background-color: #e5e7eb !important;
    cursor: col-resize !important;
}

.fullscreen-table {
    position: fixed !important; 
    top: 0 !important; 
    left: 0 !important; 
    width: 100vw !important; 
    height: 100vh !important; 
    background: white !important; 
    z-index: 9999 !important; 
    padding: 20px !important; 
    box-sizing: border-box !important; 
    overflow: auto !important;
}
.fullscreen-table .dataframe {
    max-height: calc(100vh - 100px) !important; 
    font-size: 13px !important; 
    overflow: auto !important;
    width: 100% !important;
}
.fullscreen-table .dataframe table {
    table-layout: auto !important;
    width: auto !important;
    min-width: 100% !important;
}
.fullscreen-table .dataframe th, 
.fullscreen-table .dataframe td {
    white-space: nowrap !important; 
    overflow: visible !important; 
    max-width: none !important; 
    padding: 8px 12px !important;
    min-width: auto !important;
}
.fullscreen-table .dataframe th:nth-child(12), 
.fullscreen-table .dataframe td:nth-child(12) {
    min-width: 600px !important;
    max-width: none !important;
    white-space: normal !important;
    word-wrap: break-word !important;
}

.fullscreen-header {
    display: flex !important; 
    justify-content: space-between !important; 
    align-items: center !important; 
    margin-bottom: 20px !important; 
    padding-bottom: 10px !important; 
    border-bottom: 2px solid #e5e7eb !important;
}
.close-fullscreen-btn {
    background: #ef4444 !important; 
    color: white !important; 
    border: none !important; 
    padding: 8px 16px !important; 
    border-radius: 6px !important; 
    cursor: pointer !important; 
    font-weight: bold !important;
}
.fullscreen-btn {
    background: #3b82f6 !important; 
    color: white !important; 
    border: none !important; 
    padding: 4px 8px !important; 
    border-radius: 4px !important; 
    cursor: pointer !important; 
    font-size: 12px !important; 
    margin-left: 10px !important;
}
.quick-analysis-section {
    border: 1px solid #d1d5db !important; 
    border-radius: 8px !important; 
    padding: 16px !important; 
    margin: 10px 0 !important; 
    background-color: #f8fafc !important;
}
.analyze-more-btn {
    background: #10b981 !important; 
    color: white !important; 
    border: 2px solid #059669 !important; 
    padding: 8px 16px !important; 
    border-radius: 6px !important; 
    cursor: pointer !important; 
    font-weight: bold !important; 
    font-size: 14px !important; 
    transition: all 0.2s !important;
}
.analyze-more-btn:hover {
    background: #059669 !important; 
    border-color: #047857 !important;
}
.api-status {
    padding: 8px; 
    border-radius: 4px; 
    margin-bottom: 10px; 
    text-align: center; 
    font-weight: bold;
}
.status-message {
    padding: 8px; 
    border-radius: 4px; 
    margin: 10px 0; 
    background-color: #f0f9ff; 
    border: 1px solid #0ea5e9; 
    color: #0369a1;
}
"""

def create_interface():
    with gr.Blocks(title="Resume Analysis Tool - Advanced Scoring System", css=css) as interface:
        gr.Markdown("# 📋 Resume Analysis Tool - Advanced Scoring System")
        gr.Markdown("Upload resumes and define job requirements for structured analysis with detailed scoring")
        api_status = gr.Markdown(show_api_status(), elem_classes=["api-status"])
        
        with gr.Row():
            with gr.Column():
                with gr.Group() as initial_upload_section:
                    resume_files_input = gr.File(label="Upload Multiple Resumes (PDF, DOCX, TXT) - Max 10 files", 
                                               file_types=[".pdf", ".docx", ".txt"], file_count="multiple")
                
                job_title_input = gr.Textbox(label="Job Title", 
                                           placeholder="e.g., Senior Sales Manager, Marketing Executive, Software Engineer", lines=1)
                
                job_responsibilities_input = gr.Textbox(label="Enter Roles and Responsibilities of the Job (Max 1000 characters)",
                                                      placeholder="Describe the key responsibilities, required skills, industry context, and expectations for this role...",
                                                      lines=8, max_lines=8)
                char_count = gr.Markdown("✅ 0/1000 characters")
                
                with gr.Row():
                    analyze_bulk_btn = gr.Button("🔍 Analyze Multiple Resumes", variant="primary", interactive=bool(CLAUDE_API_KEY))
                
                with gr.Group(visible=False, elem_classes=["quick-analysis-section"]) as quick_analysis_section:
                    gr.Markdown("**⚡ Analyze More Resumes**")
                    additional_resume_input = gr.File(label="Upload More Resumes (Max 10)", file_types=[".pdf", ".docx", ".txt"], file_count="multiple")
                    analyze_more_resumes_btn = gr.Button("Analyze", elem_classes=["analyze-more-btn"], visible=False, interactive=bool(CLAUDE_API_KEY))
                    gr.Markdown("*This section uses the same job requirements as above*")
                
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear All", variant="stop")
                
                gr.Markdown("### 📖 Instructions:")
                gr.Markdown("1. Upload resume files and define job requirements")
                gr.Markdown("2. Describe complete role responsibilities in the text area")
                gr.Markdown("3. Click 'Analyze Multiple Resumes' to start")
                gr.Markdown("4. Use 'Analyze More Resumes' for additional resumes")
                gr.Markdown("5. **Click the 🗑️ icon in any row to delete that candidate**")
                gr.Markdown("6. **Drag column borders to adjust width as needed**")
                gr.Markdown("### 🎯 Scoring System:")
                gr.Markdown("**Job Description Similarity (65%):** Responsibility overlap + Industry match")
                gr.Markdown("**Designation Match (35%):** Title similarity + Level alignment")
                gr.Markdown("**Final Decision:** 8-10=Good Match | 5-7=Considerable | <5=Reject")
                
                if not CLAUDE_API_KEY:
                    gr.Markdown("### ⚠️ Configuration Required:")
                    gr.Markdown("Please set CLAUDE_API_KEY environment variable in your deployment settings.")
            
            with gr.Column():
                with gr.Row():
                    gr.Markdown("### Analysis Results with Detailed Scoring")
                    fullscreen_btn = gr.Button("🔍 Full View", elem_classes=["fullscreen-btn"], visible=False)
                
                results_output = gr.Dataframe(interactive=True, wrap=False)
                
                status_message = gr.Markdown("", elem_classes=["status-message"], visible=False)
                csv_download = gr.File(label="📁 Download Results as CSV", visible=False)
                
                gr.Markdown("### 📊 Export & Legend:")
                gr.Markdown("**Columns:** Job Desc Score (X/6.5) + Designation Score (X/3.5) = Final Score (X/10)")
                gr.Markdown("**Colors:** 🟢 Good Match (8-10) | 🟠 Considerable (5-7) | 🔴 Reject (<5)")
                gr.Markdown("**Download:** Full detailed scoring available in CSV")
                gr.Markdown("**Tip:** Scroll horizontally in the table to see complete Reason text")
                gr.Markdown("**Delete:** Click the 🗑️ icon in the Del column to remove individual candidates")
        
        with gr.Group(visible=False, elem_classes=["fullscreen-table"]) as fullscreen_modal:
            with gr.Row(elem_classes=["fullscreen-header"]):
                gr.Markdown("# 📋 Resume Analysis Results - Full View with Detailed Scoring")
                close_fullscreen_btn = gr.Button("✕ Close", elem_classes=["close-fullscreen-btn"])
            fullscreen_dataframe = gr.Dataframe(interactive=False, wrap=False)
        
        if CLAUDE_API_KEY:
            additional_resume_input.change(fn=show_analyze_button, inputs=[additional_resume_input], outputs=[analyze_more_resumes_btn])
            job_responsibilities_input.change(fn=update_char_count_and_button, inputs=[job_responsibilities_input], 
                                            outputs=[char_count, analyze_bulk_btn, analyze_more_resumes_btn])
            
            analyze_bulk_btn.click(fn=lambda files, title, resp, data: analyze_multiple_resumes(files, title, resp, data, True),
                                 inputs=[resume_files_input, job_title_input, job_responsibilities_input, results_output],
                                 outputs=[results_output, csv_download, fullscreen_btn, initial_upload_section, quick_analysis_section, status_message]
                                ).then(fn=lambda csv_file: gr.update(visible=True) if csv_file else gr.update(visible=False),
                                      inputs=[csv_download], outputs=[csv_download]
                                ).then(fn=lambda msg: gr.update(value=msg, visible=bool(msg)) if msg else gr.update(visible=False),
                                      inputs=[status_message], outputs=[status_message])
            
            analyze_more_resumes_btn.click(fn=lambda files, title, resp, data: analyze_multiple_resumes(files, title, resp, data, False),
                                         inputs=[additional_resume_input, job_title_input, job_responsibilities_input, results_output],
                                         outputs=[results_output, csv_download, fullscreen_btn, initial_upload_section, quick_analysis_section, status_message]
                                        ).then(fn=lambda csv_file: gr.update(visible=True) if csv_file else gr.update(visible=False),
                                              inputs=[csv_download], outputs=[csv_download]
                                        ).then(fn=lambda msg: gr.update(value=msg, visible=bool(msg)) if msg else gr.update(visible=False),
                                              inputs=[status_message], outputs=[status_message])
            
            fullscreen_btn.click(fn=show_fullscreen_table, inputs=[results_output], outputs=[fullscreen_dataframe, fullscreen_modal])
            close_fullscreen_btn.click(fn=hide_fullscreen_table, outputs=[fullscreen_modal])
            
            # Handle cell selection for delete functionality
            results_output.select(fn=handle_dataframe_select, inputs=[results_output], outputs=[results_output, status_message]
                                ).then(fn=lambda msg: gr.update(value=msg, visible=bool(msg)) if msg else gr.update(visible=False),
                                      inputs=[status_message], outputs=[status_message])
        
        clear_btn.click(fn=clear_all, 
                       outputs=[resume_files_input, additional_resume_input, job_title_input, job_responsibilities_input, 
                               results_output, csv_download, char_count, analyze_bulk_btn, analyze_more_resumes_btn, 
                               fullscreen_btn, initial_upload_section, quick_analysis_section, status_message])
    
    return interface

# At the bottom, modify the launch section:
if __name__ == "__main__":
    print("🚀 Starting Resume Analysis Tool...")
    print("📊 API Status:", "✅ Configured" if CLAUDE_API_KEY else "❌ Not Configured")
    interface = create_interface()
    
    # Get port from environment variable (Render provides this)
    port = int(os.getenv("PORT", 7860))
    
    interface.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,  # Set to False for production
        debug=False   # Set to False for production
    )
