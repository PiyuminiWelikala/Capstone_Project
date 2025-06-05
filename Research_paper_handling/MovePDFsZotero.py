import shutil
import os

# Path to the text file containing the list of PDF paths
txt_file_path = r"Research_paper_handling/list_ref.txt"  # Change this to the correct path


# Destination folder where PDFs will be copied
destination_folder = r"Research_paper_handling/Research_papers"  # Change to your desired path

# Ensure the destination folder exists
os.makedirs(destination_folder, exist_ok=True)

# Read the file paths from the text file
with open(txt_file_path, "r", encoding="utf-8") as file:
    pdf_files = [line.strip() for line in file if line.strip()]  # Remove empty lines

# Copy each PDF to the destination folder with "EBSCOhost_" prefix
for pdf in pdf_files:
    if os.path.isfile(pdf):  # Check if the file exists
        file_name = os.path.basename(pdf)  # Extract the original file name
        new_file_name = f"PubMed_{file_name}"  # Add the prefix
        new_file_path = os.path.join(destination_folder, new_file_name)  # New file path
        shutil.copy(pdf, new_file_path)  # Copy with new name
        print(f"Copied: {pdf} -> {new_file_path}")
    else:
        print(f"File not found: {pdf}")

print("Copying process completed.")
