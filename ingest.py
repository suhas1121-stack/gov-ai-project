import json
import chromadb

def convert_to_text(service):
    return f"""
Service Name: {service['service_name']}

Description:
{service['description']}

Documents:
- """ + "\n- ".join(service.get("documents", [])) + f"""

Fees:
{service.get('fee', '')}

Application Process:
- """ + "\n- ".join(service.get("apply_online_steps", [])) + f"""

Office:
{service.get('office', '')}

Processing Time:
{service.get('processing_time', '')}
"""

client = chromadb.PersistentClient(path="./chroma_db")

# DELETE OLD
try:
    client.delete_collection("services")
except:
    pass

collection = client.get_or_create_collection("services")


with open("services.json", "r", encoding="utf-8") as f:
    services = json.load(f)

services = [
    s for s in services
    if "service_name" in s and s["service_name"].strip() != ""
]
documents = []
metadatas = []
ids = []

for i, service in enumerate(services):
    text = convert_to_text(service)

    documents.append(text)

    metadatas.append({
        "data": json.dumps(service)   # 🔥 KEY FIX
    })

    ids.append(str(i))



collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("✅ Data successfully ingested!")
