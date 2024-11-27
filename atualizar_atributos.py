from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Conecta ao MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('DB_NAME')]
collection = db[os.getenv('COLLECTION_NAME')]

def atualizar_atributos():
    inicio = time.time()
    total_processado = 0
    
    try:
        print("Iniciando atualização de atributos...")
        
        # Primeiro, conta quantas palavras precisam ser atualizadas
        total_sem_atributo = collection.count_documents({'atributo': {'$exists': False}})
        print(f"Encontradas {total_sem_atributo} palavras sem atributo")

        # Atualiza todas as palavras que não têm atributo
        result = collection.update_many(
            {'atributo': {'$exists': False}},
            {'$set': {'atributo': 'outros'}}
        )
        
        tempo_total = time.time() - inicio
        
        # Estatísticas finais
        print("\nAtualização concluída!")
        print(f"Total de palavras atualizadas: {result.modified_count}")
        print(f"Tempo total: {tempo_total:.1f} segundos")
        
        # Mostra distribuição atual dos atributos
        print("\nDistribuição de atributos:")
        pipeline = [
            {"$group": {"_id": "$atributo", "count": {"$sum": 1}}}
        ]
        for doc in collection.aggregate(pipeline):
            print(f"- {doc['_id'] or 'sem atributo'}: {doc['count']} palavras")
            
    except Exception as e:
        print(f"Erro ao atualizar atributos: {str(e)}")
    finally:
        client.close()

if __name__ == '__main__':
    print("Iniciando script de atualização...")
    atualizar_atributos() 