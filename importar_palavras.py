from pymongo import MongoClient
import unicodedata
from dotenv import load_dotenv
import os
import time

# Carrega variáveis de ambiente
load_dotenv()

def remover_acentos(texto):
    """Remove acentos de um texto"""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn')

def importar_palavras():
    # Conecta ao MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('DB_NAME')]
    collection = db[os.getenv('COLLECTION_NAME')]
    
    # Configurações
    BATCH_SIZE = 1000  # Tamanho do lote para inserção
    inicio = time.time()
    
    try:
        # Primeiro, vamos criar um set de palavras existentes para consulta rápida
        print("Carregando palavras existentes...")
        palavras_existentes = {doc['sem_acento'] for doc in collection.find({}, {'sem_acento': 1})}
        print(f"Encontradas {len(palavras_existentes)} palavras no banco")

        # Lê o arquivo palavreado.txt
        palavras = []
        total_processado = 0
        total_adicionado = 0
        
        print("\nProcessando arquivo...")
        with open('palavreado.txt', 'r', encoding='utf-8') as f:
            for linha in f:
                total_processado += 1
                
                if linha.strip():
                    palavra_original = linha.strip().upper()
                    palavra_sem_acento = remover_acentos(palavra_original)
                    
                    if palavra_sem_acento.isalpha() and palavra_sem_acento not in palavras_existentes:
                        palavras.append({
                            'original': palavra_original,
                            'sem_acento': palavra_sem_acento
                        })
                        total_adicionado += 1
                
                # Insere em lotes
                if len(palavras) >= BATCH_SIZE:
                    if palavras:  # Verifica se há palavras para inserir
                        collection.insert_many(palavras)
                        print(f"Lote de {len(palavras)} palavras inserido")
                    palavras = []
                    
                # Feedback a cada 5000 palavras
                if total_processado % 5000 == 0:
                    tempo_decorrido = time.time() - inicio
                    print(f"Processadas {total_processado} palavras... "
                          f"({total_adicionado} novas) "
                          f"Tempo: {tempo_decorrido:.1f}s")
        
        # Insere as palavras restantes
        if palavras:
            collection.insert_many(palavras)
            print(f"Lote final de {len(palavras)} palavras inserido")
        
        # Estatísticas finais
        tempo_total = time.time() - inicio
        print("\nImportação concluída!")
        print(f"Total processado: {total_processado}")
        print(f"Novas palavras: {total_adicionado}")
        print(f"Tempo total: {tempo_total:.1f} segundos")
        print(f"Total no banco: {collection.count_documents({})}")
            
    except FileNotFoundError:
        print("Arquivo palavreado.txt não encontrado")
    except Exception as e:
        print(f"Erro ao importar palavras: {str(e)}")
    finally:
        client.close()

if __name__ == '__main__':
    print("Iniciando importação...")
    importar_palavras() 