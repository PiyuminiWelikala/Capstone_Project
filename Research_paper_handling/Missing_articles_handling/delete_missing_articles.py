import os

# Define paths
original_articles_folder = "Data_Final"
missing_articles_file = "missing_articles.txt"

# Read missing article filenames
with open(missing_articles_file, "r", encoding="utf-8") as f:
    missing_articles = [line.strip() for line in f.readlines()]

# Delete files
for article in missing_articles:
    article_path = os.path.join(original_articles_folder, article)
    
    if os.path.exists(article_path):
        try:
            os.remove(article_path)
            print(f"✅ Deleted: {article}")
        except Exception as e:
            print(f"❌ Error deleting {article}: {e}")
    else:
        print(f"⚠️ File not found: {article}")

print("🎯 Deletion process completed.")