from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Conecta ao MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('DB_NAME')]
collection = db[os.getenv('COLLECTION_NAME')]

# Cria índice para melhor performance
collection.create_index("sem_acento")

# Exemplo de palavras para inserir
palavras_exemplo = [
    {
        "original": "CAFÉ",
        "sem_acento": "CAFE"
    },
    {
        "original": "ÁGUA",
        "sem_acento": "AGUA"
    },
    {
        "original": "PÃO",
        "sem_acento": "PAO"
    }
]

# Insere as palavras
try:
    collection.insert_many(palavras_exemplo)
    print("Palavras de exemplo inseridas com sucesso!")
    
    # Mostra as palavras inseridas
    print("\nPalavras no banco:")
    for palavra in collection.find():
        print(f"Original: {palavra['original']}, Sem acento: {palavra['sem_acento']}")
    
    print(f"\nTotal de palavras: {collection.count_documents({})}")
    
except Exception as e:
    print(f"Erro ao inserir palavras: {str(e)}")
finally:
    client.close() 