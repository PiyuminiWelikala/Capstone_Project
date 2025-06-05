import os
import streamlit as st
import chromadb
from chromadb.config import Settings
import PyPDF2
import pandas as pd
import csv  # Import the csv module
import openai

try:
    from config import api_key
    openai.api_key = api_key
except ImportError:
    st.error("Error: config.py not found or api_key not defined.")
    exit(1)  # Exit the script if the API key is not found

# Initialize ChromaDB with persistent storage
def initialize_chromadb():
    client = chromadb.Client(Settings(persist_directory="./chroma_db", is_persistent=True))  # Make storage persistent
    collection_name = "pdf_documents"
    try:
        collection = client.get_collection(name=collection_name)
    except chromadb.errors.InvalidCollectionException:
        collection = client.create_collection(name=collection_name)
    return client, collection

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        st.error(f"Error processing {pdf_path}: {e}")
    return text

# Process PDFs in the selected directory
def process_pdfs(data_dir, collection):
    total_added = 0
    for filename in os.listdir(data_dir):
        if filename.endswith(".pdf"):
            filepath = os.path.join(data_dir, filename)
            extracted_text = extract_text_from_pdf(filepath)
            if extracted_text:
                collection.add(
                    documents=[extracted_text],
                    metadatas=[{"filename": filename}],
                    ids=[filename]
                )
                print(f"PDF '{filename}' has been added to ChromaDB.")
                total_added += 1
    return total_added

# Remove duplicate documents
def remove_duplicates(client, collection_name):
    collection = client.get_collection(name=collection_name)
    results = collection.get()
    
    documents = results['documents']
    metadatas = results['metadatas']
    ids = results['ids']

    unique_documents = []
    unique_metadatas = []
    unique_ids = []
    
    seen_documents = set()
    for doc, metadata, doc_id in zip(documents, metadatas, ids):
        if doc not in seen_documents:
            unique_documents.append(doc)
            unique_metadatas.append(metadata)
            unique_ids.append(doc_id)
            seen_documents.add(doc)

    # Delete the existing collection
    client.delete_collection(name=collection_name)

    # Create a new collection with unique documents
    collection = client.create_collection(name=collection_name)
    collection.add(documents=unique_documents, metadatas=unique_metadatas, ids=unique_ids)

    return len(unique_documents)

# Exclude documents based on multiple criteria
def exclude_documents(client, collection_name, exclusion_criteria_list):
    collection = client.get_collection(name=collection_name)
    results = collection.get()
    
    documents = results['documents']
    metadatas = results['metadatas']
    ids = results['ids']

    filtered_documents = []
    filtered_metadatas = []
    filtered_ids = []

    exclusion_criteria_list = [criteria.strip().lower() for criteria in exclusion_criteria_list.split(',')]

    for doc, metadata, doc_id in zip(documents, metadatas, ids):
        # Check if doc is not None before applying the filter
        if doc and not any(criteria in doc.lower() for criteria in exclusion_criteria_list):  # Case-insensitive filtering
            filtered_documents.append(doc)
            filtered_metadatas.append(metadata)
            filtered_ids.append(doc_id)

    # Delete the existing collection
    client.delete_collection(name=collection_name)
    collection = client.create_collection(name=collection_name)

    # Prevent adding empty lists
    if filtered_documents:
        collection.add(documents=filtered_documents, metadatas=filtered_metadatas, ids=filtered_ids)
        return len(filtered_documents)
    else:
        st.warning("All documents were filtered out based on the exclusion criteria. No documents remain in the collection.")
        return 0
    
# Export ids to CSV
def export_ids_to_csv(collection):
    results = collection.get()
    ids = results['ids']

    # Specify the CSV file path
    csv_file_path = 'ids.csv'

    # Write the IDs to the CSV file
    try:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID'])  # Write the header row
            for id_value in ids:
                writer.writerow([id_value])
        st.success(f"IDs successfully exported to {csv_file_path}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Ask a question to the OpenAI API and retrieve relevant documents
def ask_question(collection, question):
    try:
        results = collection.query(query_texts=[question], n_results=10)

        # Fetch documents, metadata, and IDs
        relevant_documents = results['documents'][0]
        ids = results['ids'][0]

        context = "\n\n".join(relevant_documents)

        messages = [
            {
                "role": "system",
                "content": f"""
                You are an intelligent assistant tasked with retrieving and ranking documents based on their relevance to a given question.
                ###
                Instructions:
                - Analyze the provided context and extract relevant details.
                - The source to answer the questions is only what is provided in results = collection.query.
                - Do not use external information to answer the questions.
                - Return results in a structured table sorted by relevance.
                - The table should have three columns: "File Name/ID", "Title", and "Reason for Relevance".
                - The "File Name/ID" column should contain the filename or ID of the document from ids.
                - The "Title" column should be the title of the relevant document.
                - The "Reason for Relevance" should be a concise explanation of why the document is relevant.
                ###
                Context:
                {context}
                """
            },
            {"role": "user", "content": question},
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1500,
            temperature=0.5,
            n=1,
            stop=None,
        )

        answer = response.choices[0].message['content'].strip()

        # Return the answer with the relevant document info and file names
        return answer

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Streamlit UI
def main():
    st.title("Optimizing Systematic Review with OpenAI")
    st.write("Enter a directory containing PDFs to extract text and store in ChromaDB.")

    # User inputs the directory path
    data_dir = st.text_input("Enter the directory path:", "")

    if st.button("Process PDFs"):
        if not os.path.isdir(data_dir):
            st.error("Invalid directory. Please enter a valid directory path.")
        else:
            client, collection = initialize_chromadb()
            total_added = process_pdfs(data_dir, collection)
            st.success(f"Successfully added {total_added} documents to the collection.")
            st.write(f"Total documents in collection: {collection.count()}")

    # Initialize ChromaDB client
    client, collection = initialize_chromadb()

    # Fetch all document IDs from ChromaDB
    results = collection.get()
    ids = results['ids']

    # Display stored document IDs in a scrollable table
    st.subheader("Stored Documents in ChromaDB")
    if ids:
        df = pd.DataFrame({"Document ID": ids})  # Convert list to DataFrame
        st.dataframe(df, height=300)  # Scrollable table with fixed height
    else:
        st.write("No documents found in the database.")

    # Remove Duplicates Button
    if st.button("Remove Duplicates"):
        unique_count = remove_duplicates(client, "pdf_documents")
        st.success(f"Successfully removed duplicates. Number of unique documents: {unique_count}")

    # Exclusion Criteria Section (First)
    st.subheader("Exclusion Criteria")
    exclusion_criteria = st.text_input("Enter exclusion keywords or phrases (comma-separated):")

    if st.button("Apply Exclusion Criteria"):
        if exclusion_criteria.strip():
            remaining_count = exclude_documents(client, "pdf_documents", exclusion_criteria)
            st.success(f"Successfully filtered documents. Remaining documents: {remaining_count}")
        else:
            st.error("Please enter valid exclusion keywords or phrases.")

    # Inclusion Criteria Section (Second)
    st.subheader("Inclusion Criteria")
    question = st.text_input("Enter your question to filter documents:")

    if st.button("Apply Inclusion Criteria"):
        if question:
            answer = ask_question(collection, question)
            if answer:
                st.subheader("Relevant Documents")
                st.markdown(answer)
        else:
            st.error("Please enter a question for inclusion criteria.")

if __name__ == "__main__":
    main()