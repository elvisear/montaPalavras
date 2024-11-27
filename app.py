from flask import Flask, request, jsonify, render_template, url_for
import unicodedata
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from bson.objectid import ObjectId

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__, static_folder='static')

# Configurações MongoDB
MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('DB_NAME', 'palavras_db')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'palavras')

# Conecta ao MongoDB
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

VERSION = "1.0.1"  # Atualize isso a cada mudança significativa

def remover_acentos(texto):
    """Remove acentos de um texto"""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn')

def carregar_palavras_iniciais():
    """Carrega palavras iniciais se o banco estiver vazio"""
    if collection.count_documents({}) == 0:
        try:
            caminho_arquivo = os.path.join(os.path.dirname(__file__), 'palavras.txt')
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                palavras = []
                for linha in f:
                    if linha.strip():
                        palavra_original = linha.strip().upper()
                        palavra_sem_acento = remover_acentos(palavra_original)
                        if palavra_sem_acento.isalpha():
                            palavras.append({
                                'original': palavra_original,
                                'sem_acento': palavra_sem_acento
                            })
                if palavras:
                    collection.insert_many(palavras)
        except FileNotFoundError:
            print("Arquivo palavras.txt não encontrado")

# Carrega palavras iniciais se necessário
carregar_palavras_iniciais()

def palavra_existe(palavra_sem_acento):
    """Verifica se uma palavra existe no banco"""
    return collection.find_one({'sem_acento': palavra_sem_acento}) is not None

def palavra_valida(palavra, letras, obrigatoria, tamanho):
    """Função para validar palavras"""
    palavra_sem_acento = remover_acentos(palavra)
    
    # Validações rápidas primeiro
    if len(palavra_sem_acento) != tamanho:
        return False
    if obrigatoria not in palavra_sem_acento:
        return False
    if not all(letra in letras for letra in palavra_sem_acento):
        return False
    
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_words():
    try:
        # Obtém e valida os parâmetros (sem acentos para comparação)
        obrigatoria = remover_acentos(request.form['obrigatoria'].upper())
        letras = set(remover_acentos(request.form['letras'].upper()).replace(' ', '').split(',') + [obrigatoria])
        tamanho = int(request.form['tamanho'])

        # Validações básicas
        if not obrigatoria or len(obrigatoria) != 1:
            return jsonify({'error': 'Letra obrigatória inválida'}), 400
        if not letras:
            return jsonify({'error': 'Letras permitidas inválidas'}), 400
        if tamanho <= 0 or tamanho > 10:
            return jsonify({'error': 'Tamanho inválido (máximo 10)'}), 400

        # Primeiro, busca todas as palavras do tamanho correto
        palavras = list(collection.find({
            'sem_acento': {
                '$regex': f'^[{"".join(letras)}]{{{tamanho}}}$'
            }
        }))
        
        # Depois filtra para garantir que contém a letra obrigatória e usa apenas as letras permitidas
        palavras_validas = []
        for palavra in palavras:
            palavra_sem_acento = palavra['sem_acento']
            if (obrigatoria in palavra_sem_acento and 
                all(letra in letras for letra in palavra_sem_acento)):
                palavras_validas.append(palavra['original'])

        total_palavras = collection.count_documents({})

        return jsonify({
            'results': sorted(palavras_validas),
            'total': len(palavras_validas),
            'dicionario_total': total_palavras
        })

    except Exception as e:
        return jsonify({'error': f'Erro ao processar: {str(e)}'}), 500

@app.route('/adicionar-palavra', methods=['POST'])
def adicionar_palavra():
    try:
        palavra_original = request.json['palavra'].strip().upper()
        palavra_sem_acento = remover_acentos(palavra_original)
        
        # Valida se é uma palavra válida (apenas letras)
        if not palavra_sem_acento.isalpha():
            return jsonify({'error': 'Palavra deve conter apenas letras'}), 400

        # Verifica se a palavra já existe
        palavra_existente = collection.find_one({'sem_acento': palavra_sem_acento})
        if palavra_existente:
            return jsonify({'error': f'A palavra "{palavra_existente["original"]}" já existe no dicionário'}), 400

        # Adiciona a palavra ao MongoDB
        collection.insert_one({
            'original': palavra_original,
            'sem_acento': palavra_sem_acento
        })

        total_palavras = collection.count_documents({})

        return jsonify({
            'success': True,
            'message': f'Palavra "{palavra_original}" adicionada com sucesso',
            'dicionario_total': total_palavras
        })

    except Exception as e:
        return jsonify({'error': f'Erro ao adicionar palavra: {str(e)}'}), 500

@app.route('/cache-stats')
def cache_stats():
    total_palavras = collection.count_documents({})
    return jsonify({
        'dicionario_size': total_palavras
    })

@app.route('/version')
def get_version():
    return jsonify({
        'version': VERSION,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/palavras', methods=['GET'])
def listar_palavras():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search', '').upper()
        atributo = request.args.get('atributo', '')
        tamanho = request.args.get('tamanho', '')
        
        # Construir query
        query = {}
        if search:
            query['$or'] = [
                {'original': {'$regex': search, '$options': 'i'}},
                {'sem_acento': {'$regex': remover_acentos(search), '$options': 'i'}}
            ]
        
        if atributo:
            query['atributo'] = atributo
            
        if tamanho:
            query['$expr'] = {'$eq': [{'$strLenCP': '$original'}, int(tamanho)]}
        
        # Buscar total de documentos
        total = collection.count_documents(query)
        
        # Buscar palavras com paginação
        palavras = list(collection.find(query)
                       .sort('original', 1)
                       .skip((page - 1) * per_page)
                       .limit(per_page))
        
        # Converte ObjectId para string
        for palavra in palavras:
            palavra['_id'] = str(palavra['_id'])
        
        return jsonify({
            'palavras': palavras,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        print(f"Erro ao listar palavras: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/palavras/<id>', methods=['DELETE'])
def deletar_palavra(id):
    try:
        result = collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count:
            return jsonify({'success': True})
        return jsonify({'error': 'Palavra não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/palavras/<id>', methods=['PUT'])
def atualizar_palavra(id):
    try:
        data = request.json
        palavra_original = data['palavra'].strip().upper()
        palavra_sem_acento = remover_acentos(palavra_original)
        
        # Verifica se já existe outra palavra igual
        existente = collection.find_one({
            'sem_acento': palavra_sem_acento,
            '_id': {'$ne': ObjectId(id)}
        })
        if existente:
            return jsonify({'error': 'Palavra já existe'}), 400
            
        result = collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'original': palavra_original,
                'sem_acento': palavra_sem_acento
            }}
        )
        
        if result.modified_count:
            return jsonify({'success': True})
        return jsonify({'error': 'Palavra não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/palavras/<id>/atributo', methods=['PUT'])
def atualizar_atributo(id):
    try:
        data = request.json
        atributo = data['atributo']
        
        # Valida o atributo
        atributos_validos = ['verbo', 'nome', 'cidade', 'outros']
        if atributo not in atributos_validos:
            return jsonify({'error': 'Atributo inválido'}), 400
            
        result = collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'atributo': atributo}}
        )
        
        if result.modified_count:
            return jsonify({'success': True})
        return jsonify({'error': 'Palavra não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
