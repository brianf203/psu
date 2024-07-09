# Brian Fang
# July 8, 2024
# OAI Test Case Generation

import os
import psycopg2
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from gemini import Gemini

load_dotenv()
DB_URL = os.getenv('DB_URL')
DB_KEY = os.getenv('DB_KEY')
supabase: Client = create_client(DB_URL, DB_KEY)
conn = psycopg2.connect(
    dbname='postgres',
    user=os.getenv('USER'),
    password=os.getenv('PASS'),
    host=os.getenv('HOST'),
    port=os.getenv('PORT')
cursor = conn.cursor()

model = SentenceTransformer('all-MiniLM-L6-v2')

cookies = {os.getenv('COOKIES')}
genai = Gemini(cookies=cookies)

def chunk_code(code: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = text_splitter.split_text(code)
    return chunks

def explain_and_embed(chunk: str) -> Tuple[str, List[float]]:
    prompt = f"Keep response short and concise with key details: Does this code relate to test case generation? 
    If so, what parameters does it cover? If not, just say No and nothing more.: {chunk}"
    response = genai.generate_content(prompt)
    explanation_text = response.text
    embedding = model.encode(explanation_text).tolist()
    return explanation_text, embedding

def embed_query(query: str) -> List[float]:
    return model.encode(query).tolist()

def process_codebase(codebase_path: str):
    for root, _, files in os.walk(codebase_path):
        for file in files:
            if file.endswith('.txt'):
                with open(os.path.join(root, file), 'r') as f:
                    code = f.read()
                chunks = chunk_code(code)
                for chunk in chunks:
                    explanation_text, embedding = explain_and_embed(chunk)
                    print(f"Explanation Text: {explanation_text}")
                    cursor.execute(
                        "INSERT INTO code_file (file_name, file_path, file_code, file_code_embedding) VALUES (%s, %s, %s, %s)",
                        (file, os.path.join(root, file), chunk, embedding)
                    )
                    conn.commit()

def match_code(query_embedding: List[float], similarity_threshold: float = 0.99683636948) -> List[Tuple]:
    cursor.execute("""
        SELECT id, file_code, file_name, file_path, 1 - (euclidean_distance(file_code_embedding, %s) / 384) as similarity
        FROM code_file
        WHERE 1 - (euclidean_distance(file_code_embedding, %s) / 384) > %s
        ORDER BY similarity DESC
    """, (query_embedding, query_embedding, similarity_threshold))
    return cursor.fetchall()

def main():
    codebase_path = "./codebase"
    process_codebase(codebase_path)

    query = "Yes, this code relates to test case generation"
    query_embedding = embed_query(query)
    matches = match_code(query_embedding)
    combined_matches = " ".join([match[1] for match in matches])

    with open("./codebase/existingtests.txt", 'r') as f:
        existing_tests_code = f.read()

    final_query = f"Generate test cases in OAI 5G that cover more of the range of existing parameters, 
    or use new parameters. Give me these new test cases in the same format as the existing test cases. 
    Existing test cases: {existing_tests_code}\nSource code with all parameters: {combined_matches}"
    response = genai.generate_content(prompt=final_query)
    print("Generated test cases:", response.text)

if __name__ == "__main__":
    main()

cursor.close()
conn.close()
