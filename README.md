# Optimizing Systematic Review Processes with AI

## Project Overview

This capstone project leverages AI to optimize the process of conducting systematic literature reviews. Using Retrieval-Augmented Generation (RAG), we built an automated pipeline to identify and extract relevant studies from over 800 research papers focused on combining music and reminiscence therapy for improving the well-being of elderly individuals.

We collected data from four major academic databases, applied exclusion filters, and used vector-based storage (ChromaDB) for efficient retrieval. Three large language models (LLMs)—OpenAI, Gemini, and Ollama—were then evaluated on their ability to select the most relevant articles based on a predefined research question.

The OpenAI model achieved the highest accuracy (88%), followed closely by Gemini (87%) and Ollama (80%). This AI-driven approach significantly reduced manual workload, improved review consistency, and demonstrated strong potential for supporting evidence-based decision-making in healthcare research.

This project highlights how AI can streamline research processes and support human expertise in generating impactful insights for real-world applications.

## Project Poster

![Poster](Documentation/Poster.png)

### Methodology

1. Data Collection
We retrieved a total of 808 full-text academic articles from 4 academic databases using structured queries tailored to each database.

2. Preprocessing
Duplicates were removed, and texts were extracted from PDFs using PyPDF2. Cleaned documents were stored in ChromaDB, a vector database used for semantic retrieval.

3. Filtering
    * Exclusion Phase: Removed papers based on irrelevant medical conditions (e.g., HIV, cancer), incorrect target group (e.g., youth), or study type mismatches.
    * Inclusion Phase: Applied LLMs to identify papers focusing on both music and reminiscence therapy in elderly populations.

4. Model Evaluation
Each LLM (OpenAI, Gemini, Ollama) was queried using the same prompt. Their selections were manually verified, and accuracy was calculated based on relevance to the research question.

### RAG Architecture

The system uses a Retrieval-Augmented Generation (RAG) framework, which consists of:

* Vectorized Document Storage: All cleaned articles are embedded and stored in ChromaDB for efficient semantic search.

* Query Engine: When a user poses a research question, the system retrieves the most relevant documents from the database in real time.

* LLM Integration: The retrieved content is passed to an LLM (e.g., GPT-4o-mini) to generate a contextually accurate and source-backed response.

* Output Structuring: Results are returned as a ranked table containing document ID, title, and a reason for relevance.

This architecture allows the model to generate grounded, accurate, and traceable answers, unlike standalone LLMs that rely solely on pretraining.

#### Context of Project Files

* LLM_OpenAI.py, LLM_Ollama.py, LLM_Gemini.py contains the individual code for using OpenAI, Gemini and LLama3 as large language models to conduct systematic literature reviws.
* Research_paper_handling folder contains codes related to the identifying downloaded research papers, removing duplicates, moving them to one location to easily process the articles and identifying missing articles.
* Approach_2 folder contains the another code can be used for the process of conducting systematic literature review on research paper using Open AI.

#### Acknowledgements

This project was developed as part of the Data Analytics Capstone at Langara College.
Special thanks to Monica Nguyen for her exceptional guidance and to Michael Lo for his insightful contributions.

Project Contributors:
* Sandaru Welikala
* Mario Palomino Viero
* Rachel Mendonsa
* Komalpreet Brar

