import os
import chromadb

# Define the folder path where original articles are stored
original_articles_folder = "Data_Final"

# Function to get the list of original articles from the folder
def get_original_articles(folder_path):
    """Returns a list of article filenames from the given folder."""
    return set(os.listdir(folder_path))  # Get all filenames

# Fetch uploaded articles from ChromaDB
def get_uploaded_articles(collection_name="pdf_documents"):
    """Retrieves document IDs from ChromaDB."""
    client = chromadb.PersistentClient(path="chroma_db")  # Update path if needed
    collection = client.get_collection(collection_name)
    uploaded_ids = collection.get()["ids"]  # Extract stored document IDs
    return set(uploaded_ids)

# Identify missing articles
def find_missing_articles(original_set, uploaded_set):
    """Finds articles that were not uploaded to ChromaDB."""
    return original_set - uploaded_set

if __name__ == "__main__":
    original_articles = get_original_articles(original_articles_folder)
    
    uploaded_articles = get_uploaded_articles()
    
    missing_articles = find_missing_articles(original_articles, uploaded_articles)
    
    # Save or print the missing articles
    missing_file = "missing_articles.txt"
    with open(missing_file, "w", encoding="utf-8") as f:
        for article in missing_articles:
            f.write(article + "\n")

    print(f"Missing articles saved to {missing_file}")