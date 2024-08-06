# Brian Fang
# OAI Test Case Generation
# Final version

import os
import numpy as np
import psycopg2
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from gemini import Gemini

load_dotenv()
# DB_URL = os.getenv('DB_URL')
# DB_KEY = os.getenv('DB_KEY')
# supabase: Client = create_client(DB_URL, DB_KEY)
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres.beyhwcdoclmkssilkrwg',
    password=os.getenv('PASS'),
    host='aws-0-us-west-1.pooler.supabase.com',
    port='6543'
)
cursor = conn.cursor()

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

yes_queries = [
    "Yes",
    "Yes, test case generation"
    "Yes, this code relates to test case generation"
]
no_queries = [
    "No",
    "No, test case generation"
    "No, this code does not relate to test case generation"
]
yes_embeddings = model.encode(yes_queries)
no_embeddings = model.encode(no_queries)

cookies = os.getenv('COOKIES')
genai = Gemini(cookies=cookies)

def chunk_code(code: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = text_splitter.split_text(code)
    return chunks

def explain_and_embed(chunk: str) -> Tuple[str, List[float]]:
    prompt = (f"Keep response short and concise with key details: Does this code relate to test case generation?" 
              f"If so, what parameters does it cover? If not, just say No and nothing more.: {chunk}")
    response = genai.generate_content(prompt)
    explanation_text = response.text
    embedding = model.encode(explanation_text)
    return explanation_text, embedding.tolist()

def embed_query(query: str) -> List[float]:
    return model.encode(query).tolist()

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def compare_with_queries(embedding: List[float]) -> bool:
    max_yes_similarity = max([cosine_similarity(embedding, yes_embed) for yes_embed in yes_embeddings])
    max_no_similarity = max([cosine_similarity(embedding, no_embed) for no_embed in no_embeddings])
    return max_yes_similarity > max_no_similarity

def process_codebase(codebase_path: str):
    for root, _, files in os.walk(codebase_path):
        for file in files:
            if file.endswith('.c'):
                with open(os.path.join(root, file), 'r') as f:
                    code = f.read()
                chunks = chunk_code(code)
                for chunk in chunks:
                    explanation_text, embedding = explain_and_embed(chunk)
                    print(f"Explanation Text: {explanation_text}")
                    if compare_with_queries(embedding):
                        print("PASSED")
                        cursor.execute(
                            "INSERT INTO code_file (file_name, file_path, file_code, file_code_embedding) VALUES (%s, %s, %s, %s)",
                            (file, os.path.join(root, file), chunk, embedding)
                        )
                        conn.commit()

def main():
    codebase_path = "./codebase1"
    process_codebase(codebase_path)
    cursor.execute("SELECT file_code FROM code_file")
    matches = cursor.fetchall()
    combined_matches = " ".join([match[0] for match in matches])
    with open("./codebase1/existingtests.txt", 'r') as f:
        existing_tests_code = f.read()
    final_query = (f"Generate test cases in OAI 5G that cover more of the range of existing parameters, "
                   f"or use new parameters. Give me these new test cases in the same format as the existing test cases. "
                   f"Existing test cases: {existing_tests_code}\nSource code with all parameters: {combined_matches}")
    response = genai.generate_content(prompt=final_query)
    print("Generated test cases:", response.text)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
