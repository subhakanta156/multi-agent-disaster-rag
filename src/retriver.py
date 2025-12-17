import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb import PersistentClient

load_dotenv()

class DocumentRetriever:
    def __init__(self, persist_dir="../chroma_db"):
        # OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # NEW Chroma Client
        self.chroma_client = PersistentClient(path=persist_dir)

        # Load collection
        self.collection = self.chroma_client.get_collection(
            name="pdf_documents",
            embedding_function=None
        )

    def embed(self, text):
        resp = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return resp.data[0].embedding

    def get_top_k(self, query, k=5):
        query_embedding = self.embed(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        final = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            final.append({
                "content": doc,
                "file": meta.get("filename"),
                "page": meta.get("page_number"),
                "distance": dist
            })

        return final


# TEST BLOCK
if __name__ == "__main__":
    retriever = DocumentRetriever()

    query = "What are the “Principles of the Disaster Management Policy” according to the Orissa Government?"
    print(f"\n🔍 Query: {query}\n")

    results = retriever.get_top_k(query, k=5)

    print("📌 Top 5 Retrievals:\n")

    for i, r in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"File: {r['file']}, Page: {r['page']}")
        print(f"Text: {r['content'][:300]}...")
        print("-" * 50)
