import streamlit as st
import os
import sys
import base64

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")
TRAE_LOGO_PATH = os.path.join(ASSETS_DIR, "Trae_AI_logo.jpg")

# Add src to python path if needed
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    import pandas as pd
    from src.pdf_handler import PDFHandler
except Exception as e:
    st.error(f"Critical Error importing modules: {e}")
    st.error("Please ensure requirements.txt is installed correctly.")
    st.stop()

st.set_page_config(
    page_title="QUXAT DCX - AI PDF Modifier",
    page_icon=LOGO_PATH,
    layout="wide"
)

# Main Landing Page
if os.path.exists(LOGO_PATH):
    col_l1, col_l2, col_l3 = st.columns([1.5, 1, 1.5])
    with col_l2:
        st.image(LOGO_PATH, use_container_width=True)

# Custom Styling for Title
st.markdown("""
    <style>
    .title-container {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #3f4079; /* QuXAT Dark Purple */
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -1px;
    }
    .subtitle {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #64748B; /* Slate Grey */
        font-size: 1.5rem;
        font-weight: 400;
        margin-top: 0.5rem;
    }
    .highlight {
        color: #ec008c; /* QuXAT Magenta */
    }
    </style>
    <div class="title-container">
        <div class="main-title">QUXAT <span class="highlight">DCX</span></div>
        <div class="subtitle">AI-Powered PDF Modifier</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("##### Upload a PDF, detect dates, modifiable details (Issue, Version, Amends, Doc No etc.) review them and modify them - with batch change functionality.")

# Key Features
with st.expander("ℹ️ About QUXAT DCX & Key Features", expanded=False):
    st.markdown(
        """
        **QUXAT DCX - AI PDF Modifier** is a powerful tool designed to streamline document updates for hospitals and organizations.
        
        ### 🔑 Key Features:
        
        **1. 📅 Smart Date Detection**
        - Automatically scans your PDF to find dates in various formats.
        - Allows individual or batch updates of dates while preserving the original **font, size, and color**.
        
        **2. 🏥 Global Text Replacement**
        - Update critical document details across **all pages** instantly.
        - Supports: **Hospital Name, Document No, Issue No, Copy No, Version, and Amends**.
        - Handles precise replacement even with varying spacing.
        
        **3. 🖼️ Logo Management**
        - Replace the header logo on every page of your document with a single upload.
        
        **4. 🔍 Precision & Quality**
        - Uses advanced text analysis to ensure modified text looks native to the document.
        - Includes **Debug Tools** to inspect how the PDF reader "sees" text, ensuring accurate replacements.
        
        ---
        *Built for efficiency and accuracy in document management.*
        """
    )

# Workflow Flowchart
with st.expander("📌 How to Use QuXAT DCX (Workflow)", expanded=True):
    st.graphviz_chart("""
        digraph {
            rankdir=LR;
            node [shape=box, style="filled,rounded", fontname="Arial", fontsize=10];
            
            Start [label="📂 Upload PDF", fillcolor="#e1f5fe"];
            Detect [label="📅 Auto-Detect Modifiable Details", fillcolor="#fff9c4"];
            ModifyDates [label="✏️ Review & Batch Update Details", fillcolor="#fff9c4"];
            Debug [label="🐞 Debug Info\n(Copy Exact Text for Replacements)", fillcolor="#e1bee7"];
            
            subgraph cluster_mods {
                label = "Global Modifications";
                style=dashed;
                color=grey;
                Logo [label="🖼️ Replace Logo", fillcolor="#fce4ec"];
                GlobalText [label="🏥 Update Hospital Name\n📄 Update Doc/Issue/Copy No", fillcolor="#fce4ec"];
            }
            
            Generate [label="⚙️ Apply Changes & Generate PDF", fillcolor="#c8e6c9"];
            Download [label="⬇️ Download Modified PDF", fillcolor="#c8e6c9"];

            Start -> Detect;
            Detect -> ModifyDates;
            Detect -> Debug [style=dotted];
            Debug -> GlobalText [style=dashed, label="Use Text"];
            ModifyDates -> Logo [style=dotted];
            ModifyDates -> GlobalText [style=dotted];
            Logo -> Generate;
            GlobalText -> Generate;
            ModifyDates -> Generate;
            Generate -> Download;
        }
    """)

if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'detected_dates' not in st.session_state:
    st.session_state.detected_dates = []
if 'editor_key' not in st.session_state:
    st.session_state.editor_key = 0

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    
    # Check if it's a new file
    if st.session_state.pdf_bytes != bytes_data:
        st.session_state.pdf_bytes = bytes_data
        st.session_state.file_name = uploaded_file.name
        st.session_state.detected_dates = [] # Reset on new file
        st.session_state.editor_key += 1
        st.success("File uploaded successfully!")

    col1, col2 = st.columns([1, 5])
    with col1:
        detect_btn = st.button("Detect Modifiable Details")
    
    if detect_btn:
        with st.spinner("Detecting Modifiable Details..."):
            handler = PDFHandler()
            try:
                handler.load_pdf(st.session_state.pdf_bytes)
                dates = handler.detect_dates()
                st.session_state.detected_dates = dates
                st.session_state.editor_key += 1
                st.success(f"Detected {len(dates)} modifiable details.")
            except Exception as e:
                st.error(f"Error detecting modifiable details: {e}")
            finally:
                handler.close()

    if st.session_state.detected_dates:
        st.subheader("Review and Modify Dates")
        
        # Debug Info
        with st.expander("Debug Info (View PDF Text)", expanded=False):
            if st.button("Show Text from Page 1"):
                 handler_debug = PDFHandler()
                 try:
                     handler_debug.load_pdf(st.session_state.pdf_bytes)
                     text_content = handler_debug.get_page_text(0)
                     st.text_area("Extracted Text (Page 1)", text_content, height=300)
                 except Exception as e:
                     st.error(f"Error reading text: {e}")
                 finally:
                     handler_debug.close()
        
        # Additional Modifications UI
        with st.expander("Additional Modifications (Logo & Text)", expanded=False):
            st.markdown("### Logo Replacement")
            new_logo = st.file_uploader("Upload New Logo (Image)", type=["png", "jpg", "jpeg"])
            
            st.markdown("### Text Replacements")
            st.info("Enter the EXACT text currently in the PDF (e.g. 'Issue No: 1') and the new text to replace it with.")
            
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                old_hospital_name = st.text_input("Current Hospital Name:", placeholder="e.g. City General Hospital")
            with col_h2:
                new_hospital_name = st.text_input("New Hospital Name:", placeholder="e.g. Metro Health Lab")
                
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                old_doc_no = st.text_input("Current Document No:", placeholder="e.g. Doc No: 123")
            with col_d2:
                new_doc_no = st.text_input("New Document No:", placeholder="e.g. Doc No: 456")
                
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                old_issue_no = st.text_input("Current Issue No:", placeholder="e.g. Issue No: 1")
            with col_i2:
                new_issue_no = st.text_input("New Issue No:", placeholder="e.g. Issue No: 2")
                
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                old_copy_no = st.text_input("Current Copy No:", placeholder="e.g. Copy No: 1")
            with col_c2:
                new_copy_no = st.text_input("New Copy No:", placeholder="e.g. Copy No: 2")

            col_v1, col_v2 = st.columns(2)
            with col_v1:
                old_version = st.text_input("Current Version:", placeholder="e.g. Ver: 1.0")
            with col_v2:
                new_version = st.text_input("New Version:", placeholder="e.g. Ver: 1.1")

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                old_amends = st.text_input("Current Amends:", placeholder="e.g. Amends: 0")
            with col_a2:
                new_amends = st.text_input("New Amends:", placeholder="e.g. Amends: 1")


        # Batch Update UI
        with st.expander("Batch Update Options", expanded=True):
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                batch_date = st.text_input("Enter date to apply to all fields:", placeholder="e.g. 01/01/2025")
            with col_b2:
                # Add vertical spacing to align button
                st.write("") 
                st.write("")
                if st.button("Apply to All"):
                    if batch_date:
                        for d in st.session_state.detected_dates:
                            d['replacement'] = batch_date
                        st.session_state.editor_key += 1
                        st.success(f"Updated all dates to {batch_date}")
                        st.rerun()

        # Create DataFrame for editing
        df = pd.DataFrame(st.session_state.detected_dates)
        
        # Select columns
        display_df = df[['id', 'page', 'context', 'original_text', 'replacement']]
        
        edited_df = st.data_editor(
            display_df,
            column_config={
                "id": st.column_config.NumberColumn(disabled=True),
                "page": st.column_config.NumberColumn(disabled=True),
                "context": st.column_config.TextColumn(disabled=True, width="large"),
                "original_text": st.column_config.TextColumn(disabled=True),
                "replacement": st.column_config.TextColumn("Replacement Detail", required=True)
            },
            hide_index=True,
            width="stretch",
            num_rows="fixed",
            key=f"date_editor_{st.session_state.editor_key}"
        )
        
        if st.button("Apply Changes & Generate PDF"):
            with st.spinner("Processing PDF..."):
                try:
                    # Get updates from edited_df
                    updates = edited_df[['id', 'replacement']].to_dict('records')
                    
                    handler = PDFHandler()
                    handler.load_pdf(st.session_state.pdf_bytes)
                    
                    # We need to manually set the detected_dates on the new handler instance
                    # The handler needs the 'rect' info which is in st.session_state.detected_dates
                    handler.detected_dates = st.session_state.detected_dates
                    
                    # Prepare extra replacements
                    logo_bytes = new_logo.getvalue() if new_logo else None
                    
                    text_replacements = []
                    if old_hospital_name and new_hospital_name:
                        text_replacements.append((old_hospital_name, new_hospital_name))
                    if old_doc_no and new_doc_no:
                        text_replacements.append((old_doc_no, new_doc_no))
                    if old_issue_no and new_issue_no:
                        text_replacements.append((old_issue_no, new_issue_no))
                    if old_copy_no and new_copy_no:
                        text_replacements.append((old_copy_no, new_copy_no))
                    if old_version and new_version:
                        text_replacements.append((old_version, new_version))
                    if old_amends and new_amends:
                        text_replacements.append((old_amends, new_amends))
                    
                    # Apply changes
                    new_pdf_bytes, report = handler.apply_changes(updates, logo_stream=logo_bytes, text_replacements=text_replacements)
                    handler.close()
                    
                    st.success("PDF processed successfully!")
                    
                    # Show report
                    if report:
                        st.markdown("### Replacement Report")
                        for term, count in report.items():
                            if count > 0:
                                st.success(f"Replaced '{term}': {count} occurrences.")
                            else:
                                st.warning(f"Could not find '{term}' in the document. No changes made.")
                                st.info(f"Tip: Copy the exact text from the 'Debug Info' section to ensure matches.")
                    
                    st.download_button(
                        label="Download Modified PDF",
                        data=new_pdf_bytes,
                        file_name=f"modified_{st.session_state.file_name}",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")

st.markdown("---")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

if os.path.exists(TRAE_LOGO_PATH):
    try:
        img_base64 = get_base64_of_bin_file(TRAE_LOGO_PATH)
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 1rem;">
                <div style="font-weight: 700; font-size: 24px; margin-bottom: 15px; color: #2c3e50;">Developed on TRAE AI</div>
                <img src="data:image/jpeg;base64,{img_base64}" style="width: 200px; height: auto; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Error loading logo: {e}")
else:
    st.markdown("<div style='text-align: center; font-weight: bold; font-size: 20px;'>Developed on TRAE AI</div>", unsafe_allow_html=True)
