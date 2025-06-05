import os
import streamlit as st
import chromadb
import PyPDF2
from litellm import completion
from dotenv import load_dotenv

# Set environment variables. Uncomment this if you want to set them directly.
os.environ["HUGGINGFACE_TOKEN"] = '********'
os.environ["GEMINI_API_KEY"] = '*********'
os.environ['LITELLM_LOG'] = 'DEBUG'

# Retrieve environment variables
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection_name = "pdf_collection"
collection = client.get_or_create_collection(collection_name)

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        st.error(f"Error processing {pdf_file.name}: {e}")
    return text.strip() if text else ""

st.title("Systematic Review using Gemini")

# Stage 1: Upload PDFs and Extract Text
st.header("1. Upload PDFs & Extract Text")
uploaded_files = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=["pdf"])

if uploaded_files:
    for pdf in uploaded_files:
        extracted_text = extract_text_from_pdf(pdf)
        if extracted_text:
            collection.add(documents=[extracted_text], metadatas=[{"filename": pdf.name}], ids=[pdf.name])
            st.success(f"Added: {pdf.name}")
        else:
            st.warning(f"Skipping empty PDF: {pdf.name}")
    st.write(f"Total documents in ChromaDB: {collection.count()}")

# Stage 2: Remove Duplicates
st.header("2. Remove Duplicates")
if st.button("Deduplicate Documents"):
    results = collection.get()
    seen_documents = set()
    unique_documents, unique_metadatas, unique_ids = [], [], []
    for doc, metadata, doc_id in zip(results['documents'], results['metadatas'], results['ids']):
        if doc not in seen_documents:
            unique_documents.append(doc)
            unique_metadatas.append(metadata)
            unique_ids.append(doc_id)
            seen_documents.add(doc)
    client.delete_collection(collection_name)
    collection = client.create_collection(collection_name)
    collection.add(documents=unique_documents, metadatas=unique_metadatas, ids=unique_ids)
    st.success(f"Duplicates removed. Remaining documents: {collection.count()}")

# Stage 3: Exclusion Criteria
st.header("3. Exclude Documents by Keywords")
exclusion_keywords = st.text_input("Enter exclusion keywords separated by commas (case-insensitive)")

if st.button("Apply Exclusion") and exclusion_keywords:
    exclusion_keywords = [keyword.strip().lower() for keyword in exclusion_keywords.split(',')]
    results = collection.get()
    filtered_documents, filtered_metadatas, filtered_ids = [], [], []
    for doc, metadata, doc_id in zip(results['documents'], results['metadatas'], results['ids']):
        if not any(keyword in doc.lower() for keyword in exclusion_keywords):
            filtered_documents.append(doc)
            filtered_metadatas.append(metadata)
            filtered_ids.append(doc_id)
    client.delete_collection(collection_name)
    collection = client.create_collection(collection_name)
    collection.add(documents=filtered_documents, metadatas=filtered_metadatas, ids=filtered_ids)
    st.success(f"Documents after exclusion: {collection.count()}")

# Stage 4: Query Documents using Gemini
st.header("4. Ask a Question")
question = st.text_input("Enter your question")
if st.button("Search in Documents") and question:
    try:
        results = collection.query(query_texts=[question])
        relevant_docs = results['documents'][0]
        ids = results['ids'][0]
        context = "\n\n".join(relevant_docs)
        prompt = f"""
        You are an AI assistant performing a systematic literature review.
        ###
        Task:
        - Analyze the given context and extract relevant insights.
        - Use only the provided Context for answering questions—external knowledge is not allowed.
        - Present the results in a structured table ranked by relevance.
        - The table should contain three columns: "File Name/ID", "Title", and "Reason for Relevance".
        - The "File Name/ID" should correspond to the document ID.
        - The "Title" should be the title of the document.
        - The "Reason for Relevance" should briefly explain why the document is relevant.
        ###
        Context:
        {context}

        Document IDs: {ids}

        Question: {question}

        Output the answer in a structured table format:
        """
        response = completion(
            model="gemini/gemini-1.5-flash",
            messages=[{"role": "user", "content": prompt}],
            api_key=GEMINI_API_KEY
        )
        answer = response['choices'][0]['message']['content'].strip()
        st.write(answer)
    except Exception as e:
        st.error(f"Error: {e}")
