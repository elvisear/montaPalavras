from flask import Flask, request, jsonify, render_template, url_for
import json
from pathlib import Path
import unicodedata

app = Flask(__name__, static_folder='static')

# Configurações
CACHE_FILE = 'palavra_cache.json'
PALAVRAS_FILE = 'palavras.txt'

def remover_acentos(texto):
    """Remove acentos de um texto"""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn')

# Carrega palavras do arquivo local
def carregar_palavras():
    try:
        with open(PALAVRAS_FILE, 'r', encoding='utf-8') as f:
            palavras_dict = {}
            for linha in f:
                if linha.strip():
                    palavra_original = linha.strip().upper()
                    palavra_sem_acento = remover_acentos(palavra_original)
                    if palavra_sem_acento.isalpha():
                        palavras_dict[palavra_sem_acento] = palavra_original
            return palavras_dict
    except FileNotFoundError:
        print(f"Arquivo {PALAVRAS_FILE} não encontrado!")
        return {}

# Carrega ou cria o cache persistente
def carregar_cache():
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            # Converte a lista do cache para dicionário
            cache_list = json.load(f)
            return {remover_acentos(palavra): palavra for palavra in cache_list}
    except FileNotFoundError:
        return {}

# Salva o cache em arquivo
def salvar_cache(cache_palavras):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        # Salva apenas os valores (palavras originais com acentos)
        json.dump(list(cache_palavras.values()), f)

# Inicializa as palavras
PALAVRAS = carregar_palavras()
CACHE_PALAVRAS = carregar_cache()
CACHE_PALAVRAS.update(PALAVRAS)  # Mantém as palavras originais do arquivo

def palavra_valida(palavra, letras, obrigatoria, tamanho):
    """Função para validar palavras"""
    # Remove acentos da palavra
    palavra_sem_acento = remover_acentos(palavra)
    
    # Validações rápidas primeiro
    if len(palavra_sem_acento) != tamanho:
        return False
    if obrigatoria not in palavra_sem_acento:
        return False
    if not all(letra in letras for letra in palavra_sem_acento):
        return False
    
    # Verifica se a palavra existe no dicionário
    return palavra_sem_acento in CACHE_PALAVRAS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_words():
    try:
        # Obtém e valida os parâmetros
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

        # Filtra palavras do dicionário
        palavras_validas = []
        for palavra_sem_acento, palavra_original in CACHE_PALAVRAS.items():
            if (len(palavra_sem_acento) == tamanho and 
                obrigatoria in palavra_sem_acento and 
                all(letra in letras for letra in palavra_sem_acento)):
                palavras_validas.append(palavra_original)

        return jsonify({
            'results': sorted(palavras_validas),
            'total': len(palavras_validas),
            'dicionario_total': len(CACHE_PALAVRAS)
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
        if palavra_sem_acento in CACHE_PALAVRAS:
            palavra_existente = CACHE_PALAVRAS[palavra_sem_acento]
            return jsonify({'error': f'A palavra "{palavra_existente}" já existe no dicionário'}), 400

        # Adiciona a palavra ao arquivo e ao cache
        with open(PALAVRAS_FILE, 'a', encoding='utf-8') as f:
            f.write(f'\n{palavra_original}')
        
        CACHE_PALAVRAS[palavra_sem_acento] = palavra_original
        salvar_cache(CACHE_PALAVRAS)

        return jsonify({
            'success': True,
            'message': f'Palavra "{palavra_original}" adicionada com sucesso',
            'dicionario_total': len(CACHE_PALAVRAS)
        })

    except Exception as e:
        return jsonify({'error': f'Erro ao adicionar palavra: {str(e)}'}), 500

@app.route('/cache-stats')
def cache_stats():
    return jsonify({
        'dicionario_size': len(CACHE_PALAVRAS)
    })

if __name__ == '__main__':
    # Cria diretório para cache se não existir
    Path(CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    if len(PALAVRAS) == 0:
        print("AVISO: Nenhuma palavra carregada do arquivo palavras.txt!")
    else:
        print(f"Carregadas {len(PALAVRAS)} palavras do dicionário")
    
    app.run(debug=True)
