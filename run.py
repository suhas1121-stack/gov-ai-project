import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nltk.download('stopwords')
nltk.download('wordnet')

with open("services.json", "r", encoding="utf-8") as f:
    services = json.load(f)


stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(w) for w in tokens if w not in stop_words]
    return " ".join(tokens)

corpus = [
    clean_text(service["service_name"] + " " + service["description"])
    for service in services
]

vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(corpus)

def detect_intent(query):
    query = query.lower()

    if any(word in query for word in ["all", "complete", "full", "details", "everything"]):
        return "all"
    elif any(word in query for word in ["document", "documents", "papers", "required"]):
        return "documents"
    elif any(word in query for word in ["apply", "process", "procedure", "steps"]):
        return "apply"
    elif any(word in query for word in ["fee", "fees", "cost", "charges"]):
        return "fee"
    elif any(word in query for word in ["office", "where", "location"]):
        return "office"
    elif any(word in query for word in ["time", "days", "processing"]):
        return "time"
    else:
        return "general"

last_service = None


print("Welcome to the Government Services Assistant.")
print("You can ask about any government service.")
print("After selecting a service, you can ask about fees, documents, process, etc.")
print("Type 'exit' to quit.\n")


while True:
    query = input("How can I help you? ")

    if query.lower() == "exit":
        print("Thank you for using the Government Services Assistant. Goodbye.")
        break

    intent = detect_intent(query)

    if intent in ["documents", "apply", "fee", "office", "time", "all"] and last_service:
        service = last_service

    else:
       
        matched = False
        for s in services:
            if s["service_name"].lower() in query.lower():
                service = s
                last_service = s
                matched = True
                break

        if not matched:
           
            query_vec = vectorizer.transform([clean_text(query)])
            similarity = cosine_similarity(query_vec, tfidf_matrix)
            best_match = similarity.argmax()

            if similarity[0][best_match] < 0.2:
                print("I couldn't clearly identify the service. Please mention the service name.")
                continue

            service = services[best_match]
            last_service = service

    print(f"\nService: {service.get('service_name', 'Unknown Service')}")

    if intent == "documents":
        print("\nRequired Documents:")
        for doc in service.get("documents", []):
            print("-", doc)

    elif intent == "apply":
        print("\nApplication Steps:")
        for step in service.get("apply_online_steps", []):
            print("-", step)

    elif intent == "fee":
        print("\nThe fee for this service is:", service.get("fee", "Not available"))

    elif intent == "office":
        print("\nOffice Information:", service.get("office", "Not available"))

    elif intent == "time":
        print("\nProcessing Time:", service.get("processing_time", "Not available"))

    elif intent == "all":
        print("\nComplete Details:")

        print("\nRequired Documents:")
        for doc in service.get("documents", []):
            print("-", doc)

        print("\nApplication Steps:")
        for step in service.get("apply_online_steps", []):
            print("-", step)

        print("\nFee:", service.get("fee", "Not available"))
        print("Office Information:", service.get("office", "Not available"))
        print("Processing Time:", service.get("processing_time", "Not available"))

    else:
        print("\nService Overview:")
        print(service.get("description", "Description not available."))

        print("\nYou can now ask about:")
        print("- Documents")
        print("- Fees")
        print("- Application process")
        print("- Office details")
        print("- Processing time")
