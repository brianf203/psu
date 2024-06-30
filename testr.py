import os
import re
import openai
import psycopg2
from psycopg2.extras import Json
from supabase import create_client, Client
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configurations
DB_URL = "your_supabase_db_url"
DB_KEY = "your_supabase_db_key"
openai.api_key = 'your_openai_api_key'

# Initialize Supabase client
supabase: Client = create_client(DB_URL, DB_KEY)

# Connect to PostgreSQL
conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# Chunking function
def chunk_code(code: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = text_splitter.split_text(code)
    return chunks

# LLM explanation function
def explain_code(chunk: str) -> str:
    prompt = f"What does this code do: {chunk} Please include the coding language."
    response = openai.Completion.create(
        engine="davinci-codex",
        prompt=prompt,
        max_tokens=200
    )
    return response.choices[0].text.strip()

# Embedding function
def embed_text(text: str) -> List[float]:
    response = openai.Embedding.create(input=[text], model="text-embedding-ada-002")
    return response['data'][0]['embedding']

# Process and store codebase
def process_codebase(codebase_path: str):
    for root, _, files in os.walk(codebase_path):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    code = f.read()
                chunks = chunk_code(code)
                for chunk in chunks:
                    explanation = explain_code(chunk)
                    embedding = embed_text(explanation)
                    cursor.execute(
                        "INSERT INTO code_file (file_name, file_path, file_explaination, file_explaination_embedding) VALUES (%s, %s, %s, %s)",
                        (file, os.path.join(root, file), explanation, Json(embedding))
                    )
                    conn.commit()

# Similarity function
def match_code(query_embedding: List[float], similarity_threshold: float = 0.75) -> List[Tuple]:
    cursor.execute("""
        SELECT id, file_explaination, file_name, file_path,
        1 - (file_explaination_embedding <=> %s) as similarity
        FROM code_file
        WHERE 1 - (file_explaination_embedding <=> %s) > %s
        ORDER BY similarity DESC
    """, (Json(query_embedding), Json(query_embedding), similarity_threshold))
    return cursor.fetchall()

# Main function
def main():
    # Assume the codebase path is provided
    codebase_path = "path_to_codebase"
    process_codebase(codebase_path)

    # First query: Find all code relating to test parameters
    test_param_query = "Find all code relating to test parameters"
    test_param_embedding = embed_text(test_param_query)
    test_param_matches = match_code(test_param_embedding)

    # Second query: Find all code covered by existing tests
    with open("existing_tests.py", 'r') as f:
        existing_tests_code = f.read()
    existing_tests_query = f"Find all code that is covered by existing tests from {existing_tests_code}"
    existing_tests_embedding = embed_text(existing_tests_query)
    existing_tests_matches = match_code(existing_tests_embedding, similarity_threshold=0.75)

    # Third and fourth queries
    existing_tests_covered_code = " ".join([match[1] for match in existing_tests_matches])
    inverse_existing_tests_covered_code = " ".join([match[1] for match in test_param_matches if match not in existing_tests_matches])

    third_query = f"Generate unit test cases in OAI 5G that covers more of the range of each parameter in {existing_tests_code}\nCode for parameters:\n{existing_tests_covered_code}"
    fourth_query = f"Generate unit test cases in OAI 5G not covered by these existing test cases, repeat parameters are okay but include new/unused parameters {existing_tests_code}\nCode for unused parameters:\n{inverse_existing_tests_covered_code}"

    third_query_embedding = embed_text(third_query)
    fourth_query_embedding = embed_text(fourth_query)

    # Ensure token limit does not exceed 32k
    if len(third_query_embedding) > 32000 or len(fourth_query_embedding) > 32000:
        print("Error: Query exceeds token limit.")
    else:
        # Execute third and fourth queries with LLM
        third_response = openai.Completion.create(engine="davinci-codex", prompt=third_query, max_tokens=200)
        fourth_response = openai.Completion.create(engine="davinci-codex", prompt=fourth_query, max_tokens=200)
        print("Third query response:", third_response.choices[0].text.strip())
        print("Fourth query response:", fourth_response.choices[0].text.strip())

if __name__ == "__main__":
    main()
