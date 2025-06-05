import streamlit as st
import fitz  # PyMuPDF
import openai
import re
import logging
import hashlib

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('log.txt')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# OPENAI API KEY
if "api_key_set" not in st.session_state:
    try:
        with open('open_ai_secret_token.txt', 'r') as file:
            open_api_token = file.read().strip()
        openai.api_key = open_api_token
        st.session_state["api_key_set"] = True
        logger.info("OpenAI API key successfully set.")
    except Exception as e:
        logger.error(f"Error setting OpenAI API key: {e}")
        st.error(f"❌ Error setting OpenAI API key: {e}")

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_file):
    try:
        logger.info(f"Extracting text from: {pdf_file.name}")

        # Open the PDF file directly from the uploaded stream
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        extracted_text = ""

        for page in doc:
            blocks = page.get_text("blocks")
            sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))  # Sort by Y, then X position

            for block in sorted_blocks:
                extracted_text += block[4] + "\n"  # The actual text content

        return extracted_text.strip() if extracted_text.strip() else "No extractable text found."

    except Exception as e:
        logger.error(f"Error extracting text from {pdf_file.name}: {e}")
        st.error(f"❌ Error extracting text from {pdf_file.name}: {e}")
        return ""

# Function to check for duplicate PDFs based on text content
def is_duplicate(text, seen_texts):
    """ Check if extracted text is a duplicate using a hash. """
    text_hash = hashlib.md5(text.encode()).hexdigest()
    if text_hash in seen_texts:
        return True
    seen_texts.add(text_hash)
    return False

# Function to call OpenAI once per unique paper
def process_paper_with_openai(text, criteria):
    try:
        logger.info("Calling OpenAI for title, abstract, and inclusion evaluation...")
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system", 
                "content": "You are an AI assistant that extracts title and abstract from research papers and evaluates inclusion criteria."
            }, {
                "role": "user", 
                "content": f"Extract the title and abstract from the following research paper text. Then, analyze the full text to determine whether the paper meets the inclusion criteria.\n\n"
                           f"Paper Text:\n{text}\n\n"
                           f"Inclusion Criteria: {criteria}\n\n"
                           f"Format your response as:\n"
                           f"Title: <title>\n"
                           f"Abstract: <abstract>\n"
                           f"Decision: <Include/Exclude>\n"
                           f"Reason: <brief reason>"
            }]
        )
        content = response["choices"][0]["message"]["content"]

        # Extract information
        title_match = re.search(r"(?i)Title:\s*(.+)", content)
        abstract_match = re.search(r"(?i)Abstract:\s*(.+)", content, re.DOTALL)
        decision_match = re.search(r"(?i)Decision:\s*(Include|Exclude)", content)
        reason_match = re.search(r"(?i)Reason:\s*(.+)", content, re.DOTALL)

        title = title_match.group(1).strip() if title_match else "Title not found"
        abstract = abstract_match.group(1).strip() if abstract_match else "Abstract not found"
        decision = decision_match.group(1) if decision_match else "Error"
        reason = reason_match.group(1).strip() if reason_match else "No reason provided"

        logger.info(f"OpenAI processed paper: {title}")
        return title, abstract, decision, reason

    except Exception as e:
        logger.error(f"Error processing paper with OpenAI: {e}")
        st.error(f"❌ Error processing paper with OpenAI: {e}")
        return "Title not found", "Abstract not found", "Error", "Could not process the paper."

# Streamlit UI
st.title("📄 Research Paper Evaluator")
st.sidebar.header("Upload PDF Files")
uploaded_files = st.sidebar.file_uploader("Upload multiple research papers", type=["pdf"], accept_multiple_files=True)
criteria = st.text_area("📝 Enter Inclusion Criteria", "The study must involve human subjects and analyze the impact of physical activity on cardiovascular health.")

if st.button("Process Papers"):
    if not uploaded_files:
        st.warning("⚠️ Please upload at least one PDF file.")
    else:
        results = []
        seen_texts = set()  # Track unique PDF contents

        for pdf_file in uploaded_files:
            text = extract_text_from_pdf(pdf_file)

            if is_duplicate(text, seen_texts):
                st.warning(f"⚠️ Duplicate detected: {pdf_file.name} was skipped.")
                logger.info(f"Duplicate detected and skipped: {pdf_file.name}")
                continue  # Skip duplicate PDFs

            title, abstract, decision, reason = process_paper_with_openai(text, criteria)
            results.append({"Filename": pdf_file.name, "Title": title, "Decision": decision, "Reason": reason})
        
        logger.info("Processing complete!")
        st.success("✅ Processing Complete!")
        st.write("### 📊 Results:")
        st.dataframe(results)
