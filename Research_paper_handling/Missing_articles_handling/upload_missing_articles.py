import os
import chromadb

# Define paths
original_articles_folder = "Data_Final"
missing_articles_file = "missing_articles.txt"

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="chroma_db")  # Update path if needed
collection = client.get_collection("pdf_documents")  # Update collection name if necessary

# Read missing article filenames
with open(missing_articles_file, "r", encoding="utf-8") as f:
    missing_articles = [line.strip() for line in f.readlines()]

# Function to read article content
def read_article_content(file_path):
    """Reads and returns the content of an article."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

# Upload missing articles to ChromaDB
for article in missing_articles:
    article_path = os.path.join(original_articles_folder, article)
    
    if os.path.exists(article_path):  # Ensure the file exists before processing
        content = read_article_content(article_path)
        if content:
            collection.add(ids=[article], documents=[content])  # Upload to ChromaDB
            print(f"Uploaded: {article}")
        else:
            print(f"Skipping {article} due to read error.")
    else:
        print(f"File not found: {article}")

print("Upload process completed.")
