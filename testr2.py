import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json
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
    user='postgres.beyhwcdoclmkssilkrwg', 
    password=os.getenv('PASS'), 
    host='aws-0-us-west-1.pooler.supabase.com', 
    port='6543')

cursor = conn.cursor()

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Gemini client with your credentials
cookies = {"_ga":"GA1.1.204182567.1719957647","SEARCH_SAMESITE":"CgQIxJsB","SID":"g.a000lQiodC6bdPiZMQEITQTwJmuxGL2rQ5R3-VLsyJpiEBw0FsPOB8PuPUpXUDvVzrDBxNCaaAACgYKAc0SARUSFQHGX2MiWB-uXsGKe6n6ci92haQTwBoVAUF8yKpqFPJ53o17D1-nnyKf0KNQ0076","__Secure-1PSID":"g.a000lQiodC6bdPiZMQEITQTwJmuxGL2rQ5R3-VLsyJpiEBw0FsPOZC8ZWAackE8LkEgT4VJHyQACgYKAY8SARUSFQHGX2MifFnAiPoQjyAdY_pLJdSymBoVAUF8yKol_vXzVvnPfFn2VkEtsdau0076","__Secure-3PSID":"g.a000lQiodC6bdPiZMQEITQTwJmuxGL2rQ5R3-VLsyJpiEBw0FsPOetPioPFT7E0L4YKH2pXvOgACgYKAZESARUSFQHGX2MiTlqBbib9k9mMjmiTKhqZTRoVAUF8yKpGnMLBdiNwiz-Ev7zDI7O_0076","HSID":"Az2CLFfOD_yaFum01","SSID":"AHjRWVcvfWMnhSygp","APISID":"V2grI5K2p11XfE4v/ACera5_Rf1LHcoqwP","SAPISID":"YA0hyPeNMphhT3gz/ALSTCfnFTwXl0apbU","__Secure-1PAPISID":"YA0hyPeNMphhT3gz/ALSTCfnFTwXl0apbU","__Secure-3PAPISID":"YA0hyPeNMphhT3gz/ALSTCfnFTwXl0apbU","AEC":"AVYB7cpTpFZjY0LjD2NTqSGNzEPtScps1VIaRc2WHJu3_ejmfCxZHSw9T2A","NID":"515","_ga_WC57KJ50ZZ":"GS1.1.1720242349.5.1.1720242389.0.0.0","__Secure-1PSIDTS":"sidts-CjEB4E2dkf1wWWpGzCIMB9H6zg5n4HnvEzQWTX71x7me0zgVatDdFl8d30du1Ro-y5KZEAA","__Secure-3PSIDTS":"sidts-CjEB4E2dkf1wWWpGzCIMB9H6zg5n4HnvEzQWTX71x7me0zgVatDdFl8d30du1Ro-y5KZEAA","SIDCC":"AKEyXzUJv8mWQmasEuHIMQ07WdAq-oWSuhJtkKTYq1-IyFTtgwAxal5b712nwaH7M1nsafZbKA","__Secure-1PSIDCC":"AKEyXzU7pNWK1lVjYgJacSyGZduy59GTqr7toMHipY09hlzZsxAjCyfX-pGOgeM4kl4MYizHfQE","__Secure-3PSIDCC":"AKEyXzXAxlV_2XGT6pg2iLgGxVWvJVql4SHxdlMd9XVFjo6okjIP_c44wK6W0Kzr28xCVnRCHqI"}
genai = Gemini(cookies=cookies)

def chunk_code(code: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = text_splitter.split_text(code)
    return chunks

def explain_and_embed(chunk: str) -> Tuple[str, List[float]]:
    prompt = f"Keep response short and concise with key details: Does this code relate to test case generation? If so, what parameters does it cover? If not, just say no. {chunk}"
    response = genai.generate_content(prompt)
    explanation_text = response.text.strip()
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
                    explanation, embedding = explain_and_embed(chunk)
                    cursor.execute(
                        "INSERT INTO code_file (file_name, file_path, file_explanation, file_explanation_embedding) VALUES (%s, %s, %s, %s)",
                        (file, os.path.join(root, file), explanation, Json(embedding))
                    )
                    conn.commit()

def match_code(query_embedding: List[float], similarity_threshold: float = 0.75) -> List[Tuple]:
    cursor.execute("""
        SELECT id, file_explanation, file_name, file_path,
        1 - (file_explanation_embedding <=> %s) as similarity
        FROM code_file
        WHERE 1 - (file_explanation_embedding <=> %s) > %s
        ORDER BY similarity DESC
    """, (Json(query_embedding), Json(query_embedding), similarity_threshold))
    return cursor.fetchall()

def find_relevant_code_chunks():
    cursor.execute("SELECT id, file_explanation, file_name, file_path FROM code_file WHERE file_explanation LIKE '%test case generation%'")
    return cursor.fetchall()

def find_covered_code_chunks(existing_tests_code: str):
    existing_tests_params = extract_parameters(existing_tests_code)
    relevant_chunks = find_relevant_code_chunks()
    covered_chunks = []
    for chunk in relevant_chunks:
        if any(param in chunk[1] for param in existing_tests_params):
            covered_chunks.append(chunk)
    return covered_chunks

def main():
    codebase_path = "./codebase"
    process_codebase(codebase_path)

    test_param_query = "Find all code relating to test parameters"
    test_param_embedding = embed_query(test_param_query)
    test_param_matches = match_code(test_param_embedding)

    with open("./input.txt", 'r') as f:
        existing_tests_code = f.read()
    existing_tests_query = f"Find all code that is covered by existing tests from {existing_tests_code}"
    existing_tests_embedding = embed_query(existing_tests_query)
    existing_tests_matches = match_code(existing_tests_embedding, similarity_threshold=0.75)

    existing_tests_covered_code = " ".join([match[1] for match in existing_tests_matches])
    inverse_existing_tests_covered_code = " ".join([match[1] for match in test_param_matches if match not in existing_tests_matches])

    third_query = f"Generate unit test cases in OAI 5G that covers more of the range of each parameter in {existing_tests_code}, code for parameters {existing_tests_covered_code}"
    fourth_query = f"Generate unit test cases in OAI 5G not covered by these existing test cases, repeat parameters are okay but include new/unused parameters {existing_tests_code}, code for unused parameters {inverse_existing_tests_covered_code}"

    third_query_embedding = embed_query(third_query)
    fourth_query_embedding = embed_query(fourth_query)

    if len(third_query_embedding) > 32000 or len(fourth_query_embedding) > 32000:
        print("Error: Query exceeds token limit.")
    else:
        third_response = genai.generate_content(prompt=third_query)
        fourth_response = genai.generate_content(prompt=fourth_query)
        print("Third query response:", third_response.text)
        print("Fourth query response:", fourth_response.text)

if __name__ == "__main__":
    main()

cursor.close()
conn.close()
