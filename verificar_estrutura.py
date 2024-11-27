from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Conecta ao MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('DB_NAME')]
collection = db[os.getenv('COLLECTION_NAME')]

# Pega um documento de exemplo
exemplo = collection.find_one()
if exemplo:
    print("Estrutura do documento:")
    for campo, valor in exemplo.items():
        print(f"{campo}: {valor}")
else:
    print("Nenhum documento encontrado na coleção")

# Mostra total de documentos
total = collection.count_documents({})
print(f"\nTotal de documentos: {total}")

client.close() 