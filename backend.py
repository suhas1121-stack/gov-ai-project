from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import ollama
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#DATABASE AND PATH...................
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("services")


class QueryRequest(BaseModel):
    query: str


@app.post("/ask")
async def ask_question(data: QueryRequest):

    query = data.query
    query_lower = query.lower()

    #DETAILS FETCHING........................
    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    if not results["documents"] or not results["documents"][0]:
        return {"answer": "SORRY FOR INCONVENIENCE — SERVICE NOT FOUND"}

    documents = results["documents"][0]
    metadatas = results.get("metadatas", [[]])[0]

    context = documents[0]
    metadata = {}

    # FINDING EXACT SERVICE.....................
    for i in range(len(documents)):
        doc = documents[i]
        raw_meta = metadatas[i] if i < len(metadatas) else {}

        parsed_meta = {}
        if isinstance(raw_meta, dict) and "data" in raw_meta:
            try:
                parsed_meta = json.loads(raw_meta["data"])
            except:
                parsed_meta = {}

        service_name = parsed_meta.get("service_name", "").lower()

        # SMART WORD MATCHING.....................................
        query_words = set(query_lower.split())
        service_words = set(service_name.split())

        if service_words and service_words.intersection(query_words):
            context = doc
            metadata = parsed_meta
            break

    # fallback
    if not metadata:
        raw_meta = metadatas[0] if metadatas else {}
        if isinstance(raw_meta, dict) and "data" in raw_meta:
            try:
                metadata = json.loads(raw_meta["data"])
            except:
                metadata = {}

    # FORM RESPONSE.........................................
    if any(word in query_lower for word in ["form", "application form", "apply form"]):
        if metadata and "forms" in metadata:
            return {
                "type": "form",
                "data": metadata["forms"]
            }
        else:
            return {"answer": "Form not available for this service"}

    #RULE-BASED EXTRACTION..................................
    if "fee" in query_lower:
        if "Fees:" in context:
            answer = context.split("Fees:")[1].split("Application Process:")[0].strip()
            answer = "- " + answer.replace("\n", "\n- ")
            return {"answer": answer}
        else:
            return {"answer": "SORRY FOR INCONVENIENCE — SERVICE NOT FOUND"}

    elif "document" in query_lower:
        if "Documents:" in context:
            answer = context.split("Documents:")[1].split("Fees:")[0].strip()
            return {"answer": answer}
        else:
            return {"answer": "SORRY FOR INCONVENIENCE — SERVICE NOT FOUND"}

    elif "process" in query_lower:
        if "Application Process:" in context:
            answer = context.split("Application Process:")[1].split("Office:")[0].strip()
            return {"answer": answer}
        else:
            return {"answer": "SORRY FOR INCONVENIENCE — SERVICE NOT FOUND"}

    #PROMPT FOR OLLAMA...........................
    prompt = f"""
You are a government services navigator.

STRICT RULES:
- Answer ONLY using the provided context
- DO NOT ignore available information
- Maximum 2 sentences
- No extra explanation
- No reasoning
- If answer not found:
  SORRY FOR INCONVENIENCE — SERVICE NOT FOUND

Context:
{context}

Question:
{query}

Answer:
"""

    # OLLAMA..........................................
    try:
        response = ollama.chat(
            model="phi",
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.0,
                "num_predict": 120,
                "top_p": 0.9
            }
        )

        answer = response["message"]["content"].strip()

    except:
        answer = context[:300] if context else "SORRY FOR INCONVENIENCE — SERVICE NOT FOUND"

    # OUTPUT RESPONSE............................
    stop_phrases = [
        "Rules of the Puzzle",
        "Statement 1",
        "Rule 1",
        "Let’s start",
        "Proof by contradiction"
    ]

    for phrase in stop_phrases:
        if phrase in answer:
            answer = answer.split(phrase)[0].strip()

    return {"answer": answer}
