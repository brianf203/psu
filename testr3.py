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
cookies = {"_ga": "GA1.1.204182567.1719957647", "SEARCH_SAMESITE": "CgQIxJsB", "SID": "g.a000lQiodC6bdPiZMQEITQTwJmuxGL2rQ5R3-VLsyJpiEBw0FsPOB8PuPUpXUDvVzrDBxNCaaAACgYKAc0SARUSFQHGX2MiWB-uXsGKe6n6ci92haQTwBoVAUF8yKpqFPJ53o17D1-nnyKf0KNQ0076", "__Secure-1PSID": "g.a000lQiodC6bdPiZMQEITQTwJmuxGL2rQ5R3-VLsyJpiEBw0FsPOZC8ZWAackE8LkEgT4VJHyQACgYKAY8SARUSFQHGX2MifFnAiPoQjyAdY_pLJdSymBoVAUF8yKol_vXzVvnPfFn2VkEtsdau0076", "__Secure-3PSID": "g.a000lQiodC6bdPiZMQEITQTwJmuxGL2rQ5R3-VLsyJpiEBw0FsPOetPioPFT7E0L4YKH2pXvOgACgYKAZESARUSFQHGX2MiTlqBbib9k9mMjmiTKhqZTRoVAUF8yKpGnMLBdiNwiz-Ev7zDI7O_0076", "HSID": "Az2CLFfOD_yaFum01", "SSID": "AHjRWVcvfWMnhSygp", "APISID": "V2grI5K2p11XfE4v/ACera5_Rf1LHcoqwP", "SAPISID": "YA0hyPeNMphhT3gz/ALSTCfnFTwXl0apbU", "__Secure-1PAPISID": "YA0hyPeNMphhT3gz/ALSTCfnFTwXl0apbU", "__Secure-3PAPISID": "YA0hyPeNMphhT3gz/ALSTCfnFTwXl0apbU", "AEC": "AVYB7cpTpFZjY0LjD2NTqSGNzEPtScps1VIaRc2WHJu3_ejmfCxZHSw9T2A", "NID": "515", "_ga_WC57KJ50ZZ": "GS1.1.1720242349.5.1.1720242389.0.0.0", "__Secure-1PSIDTS": "sidts-CjEB4E2dkf1wWWpGzCIMB9H6zg5n4HnvEzQWTX71x7me0zgVatDdFl8d30du1Ro-y5KZEAA", "__Secure-3PSIDTS": "sidts-CjEB4E2dkf1wWWpGzCIMB9H6zg5n4HnvEzQWTX71x7me0zgVatDdFl8d30du1Ro-y5KZEAA", "SIDCC": "AKEyXzUJv8mWQmasEuHIMQ07WdAq-oWSuhJtkKTYq1-IyFTtgwAxal5b712nwaH7M1nsafZbKA", "__Secure-1PSIDCC": "AKEyXzU7pNWK1lVjYgJacSyGZduy59GTqr7toMHipY09hlzZsxAjCyfX-pGOgeM4kl4MYizHfQE", "__Secure-3PSIDCC": "AKEyXzXAxlV_2XGT6pg2iLgGxVWvJVql4SHxdlMd9XVFjo6okjIP_c44wK6W0Kzr28xCVnRCHqI"}
genai = Gemini(cookies=cookies)

def chunk_code(code: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = text_splitter.split_text(code)
    return chunks

def explain_and_embed(chunk: str) -> Tuple[str, List[float]]:
    prompt = f"Keep response short and concise with key details: Does this code relate to test case generation? If so, what parameters does it cover? If not, just say no.: {chunk}"
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
                    cursor.execute(
                        "INSERT INTO code_file (file_name, file_path, file_explanation, file_explanation_embedding) VALUES (%s, %s, %s, %s)",
                        (file, os.path.join(root, file), explanation_text, Json(embedding))
                    )
                    conn.commit()

def extract_parameters(existing_tests_code: str) -> List[str]:
    prompt = f"Extract all parameters covered by the following test cases: {existing_tests_code}"
    response = genai.generate_content(prompt)
    parameters = response.text.split(",")  # Assuming the response is comma-separated
    return [param.strip() for param in parameters]

def match_code(query_embedding: List[float], similarity_threshold: float = 0.75) -> List[Tuple]:
    cursor.execute("""
        SELECT id, file_explanation, file_name, file_path,
        1 - (file_explanation_embedding <=> %s) as similarity
        FROM code_file
        WHERE 1 - (file_explanation_embedding <=> %s) > %s
        ORDER BY similarity DESC
    """, (Json(query_embedding), Json(query_embedding), similarity_threshold))
    return cursor.fetchall()

def main():
    codebase_path = "./codebase"
    process_codebase(codebase_path)

    with open("./input.txt", 'r') as f:
        existing_tests_code = f.read()
    
    parameters = extract_parameters(existing_tests_code)
    
    covered_chunks = []
    uncovered_chunks = []
    
    for param in parameters:
        query = f"This code includes parameter {param}"
        query_embedding = embed_query(query)
        matches = match_code(query_embedding)
        
        for match in matches:
            if match not in covered_chunks:
                covered_chunks.append(match)
        
    for match in match_code(embed_query("This code relates to test case generation")):
        if match not in covered_chunks:
            uncovered_chunks.append(match)
    
    covered_code = " ".join([match[1] for match in covered_chunks])
    uncovered_code = " ".join([match[1] for match in uncovered_chunks])
    
    third_query = f"Generate unit test cases in OAI 5G that covers more of the range of each parameter in {covered_code}"
    fourth_query = f"Generate unit test cases in OAI 5G not covered by these existing test cases, repeat parameters are okay but include new/unused parameters {uncovered_code}"
    
    if len(embed_query(third_query)) > 32000 or len(embed_query(fourth_query)) > 32000:
        print("Error: Query exceeds token limit.")
    else:
        third_response = genai
        fourth_response = genai.generate_content(prompt=fourth_query)
        print("Third query response:", third_response.text)
        print("Fourth query response:", fourth_response.text)

if __name__ == "__main__":
    main()

cursor.close()
conn.close()
