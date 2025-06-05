import pandas as pd
import os

# Folder containing CSV files
folder_path = r"Zotero Files"
output_folder = os.path.join(folder_path, "Unique")
os.makedirs(output_folder, exist_ok=True)

# List all CSV files in the folder
csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

# Dictionary to store data from each file
data_frames = {}

# Load each CSV file into a DataFrame
for file in csv_files:
    file_path = os.path.join(folder_path, file)
    try:
        df = pd.read_csv(file_path, usecols=["Author", "Title", "Abstract Note", "File Attachments"], dtype=str)
        df["Source File"] = file  # Track source file
        data_frames[file] = df
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Ensure we have valid data before proceeding
if not data_frames:
    print("No valid CSV files found or no valid data loaded.")
    exit()

# Combine all data to find duplicates
combined_df = pd.concat(data_frames.values(), ignore_index=True)

# Remove duplicate rows based on Author, Title, and Abstract Note
unique_df = combined_df.drop_duplicates(subset=["Abstract Note"], keep="first")

# ["Author", "Title", "Abstract Note"]

# Split back into separate DataFrames
for file in csv_files:
    unique_data = unique_df[unique_df["Source File"] == file].drop(columns=["Source File"])
    
    # Save unique data back to CSV
    output_csv_path = os.path.join(output_folder, f"unique_{file}")
    unique_data.to_csv(output_csv_path, index=False)

    # Save unique File Attachments column to a text file
    output_txt_path = os.path.join(output_folder, f"{file}.txt")
    unique_data["File Attachments"].dropna().drop_duplicates().to_csv(output_txt_path, index=False, header=False)

print("Processing complete. Unique CSV files and text files have been saved.")