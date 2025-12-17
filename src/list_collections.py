from chromadb import PersistentClient

client = PersistentClient(path="../chroma_db")

print("Collections:")
print(client.list_collections())
