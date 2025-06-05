import os
import PyPDF2
import streamlit as st
from sentence_transformers import SentenceTransformer
import chromadb
import ollama  # ✅ Replaced OpenAI with Ollama

# Initialize ChromaDB client
client_chroma = chromadb.PersistentClient(path="chroma_db")
text_embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        st.write(f"Error processing {pdf_path}: {e}")
    return text

def process_text_and_store(folder_path):
    try:
        client_chroma.delete_collection(name="knowledge_base")
    except Exception:
        pass

    collection = client_chroma.create_collection(name="knowledge_base")
    seen_texts = set()
    processed_count = 0
    total_files = 0
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            total_files += 1
            file_path = os.path.join(folder_path, filename)
            extracted_text = extract_text_from_pdf(file_path)
            if extracted_text and extracted_text not in seen_texts:
                seen_texts.add(extracted_text)
                collection.add(
                    documents=[extracted_text],
                    metadatas=[{"source": filename}],
                    ids=[filename]
                )
                processed_count += 1
    
    st.write(f"Total PDFs processed: {total_files}")
    st.write(f"Total unique articles stored: {processed_count}")
    return collection

# Function for exclusion criteria

def filter_articles(collection, exclusion_criteria):
    articles = collection.get()
    filtered_ids = []
    initial_count = len(articles['documents'])
    
    for doc, meta in zip(articles['documents'], articles['metadatas']):
        if any(criterion.lower() in doc.lower() for criterion in exclusion_criteria):
            filtered_ids.append(meta['source'])
    
    if filtered_ids:
        collection.delete(ids=filtered_ids)
    
    remaining_count = collection.count()
    st.write(f"Total unique articles after exclusion: {remaining_count}")
    st.write(f"Excluded articles: {', '.join(filtered_ids) if filtered_ids else 'None'}")
    return collection

# The query for the resarch questions

def semantic_search(query, collection, top_k=7):
    query_embedding = text_embedding_model.encode(query)
    results = collection.query(
        query_embeddings=[query_embedding.tolist()], n_results=top_k
    )
    return results

def generate_response(query, results):
    if not results["documents"]:
        return "No relevant documents found."
    
    sources = [meta["source"] for meta in results["metadatas"][0]]
    context = "\n".join(results["documents"][0])
    prompt = f"Query: {query}\nContext: {context}\nAnswer:"
    os.system("ollama pull llama3")
    
    response = ollama.chat(model="llama3", messages = [
                {
                    "role": "system",
                    "content": f"""
                    You are an intelligent assistant tasked with retrieving and ranking documents based on their relevance to a given question.
                    ###
                    Instructions:
                    - Analyze the provided context and extract relevant details.
                    - The source to anser the questions is only what is is provided in results = collection.query)
                    - Do not use external informaiton to anser the qurstions.
                    - Return results in a structured table sorted by relevance.
                    - The reason should be a concise explanation of why the document is relevant
                    - The table should have three columns: "File Name/ID", "Document Section", and "Reason for Relevance".
                    - The "File Name/ID" column should contain the filename or ID of the document from ids.
                    - The "Document Section" should be the relevant section.
                    - The reason should be a concise explanation of why the document is relevant
                    ###
                    Context:
                    {context}
                    """
                },
                {"role": "user", "content": query},
            ])

    response_text = response['message']['content']
    source_list = "\n".join(f"- {source}" for source in sources)
    
    return f"{response_text}\n\nSources:\n{source_list}"

def main():
    st.title("Systematic Review (Ollama)")
    
    if "collection" not in st.session_state:
        st.session_state["collection"] = None

    folder_path = st.text_input("Enter the folder path containing PDFs:")
    if st.button("Process Folder") and folder_path:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            st.write("Processing documents in the folder...")
            st.session_state["collection"] = process_text_and_store(folder_path)
            st.success("PDF content processed and stored successfully!")
        else:
            st.error("Invalid folder path. Please enter a valid directory.")
    
    if st.session_state["collection"]:
        exclusion_criteria = st.text_area("Enter exclusion criteria (comma-separated):")
        if st.button("Apply Exclusion Criteria") and exclusion_criteria:
            exclusion_list = [crit.strip() for crit in exclusion_criteria.split(",")]
            st.session_state["collection"] = filter_articles(st.session_state["collection"], exclusion_list)
            st.success("Exclusion criteria applied successfully!")
        
        query = st.text_input("Enter your query:")
        if st.button("Execute Query") and query:
            results = semantic_search(query, st.session_state["collection"])
            response = generate_response(query, results)
            st.subheader("Generated Response:")
            st.write(response)

        while True:
            another_question = input("Do you have another query? (yes/no): ")
            if another_question.lower() != 'yes':
                break
        


if __name__ == "__main__":
    main()
