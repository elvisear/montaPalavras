let currentPage = 1;
let totalPages = 1;
let currentSearch = '';
let perPage = 50;
let currentAtributo = '';
let currentTamanho = '';
let selectedIds = new Set();

async function loadPalavras() {
    try {
        const queryParams = new URLSearchParams({
            page: currentPage,
            per_page: perPage,
            search: currentSearch,
            atributo: currentAtributo,
            tamanho: currentTamanho
        });

        const response = await fetch(`/api/palavras?${queryParams}`);
        const data = await response.json();
        
        if (data.error) throw new Error(data.error);
        
        renderTable(data.palavras);
        updatePagination(data);
        updateTotalInfo(data.total);
    } catch (error) {
        console.error('Erro ao carregar palavras:', error);
        alert('Erro ao carregar palavras');
    }
}

function renderTable(palavras) {
    const tbody = document.getElementById('palavrasTable');
    tbody.innerHTML = palavras.map(palavra => `
        <tr class="${selectedIds.has(palavra._id) ? 'row-selected' : ''}">
            <td class="checkbox-column">
                <input type="checkbox" 
                       data-id="${palavra._id}" 
                       ${selectedIds.has(palavra._id) ? 'checked' : ''}>
            </td>
            <td>${palavra.original}</td>
            <td>${palavra.sem_acento}</td>
            <td>${palavra.original.length}</td>
            <td>
                <select class="atributo-select" data-id="${palavra._id}" data-atual="${palavra.atributo || 'outros'}">
                    <option value="verbo" ${(palavra.atributo || 'outros') === 'verbo' ? 'selected' : ''}>Verbo</option>
                    <option value="nome" ${(palavra.atributo || 'outros') === 'nome' ? 'selected' : ''}>Nome</option>
                    <option value="cidade" ${(palavra.atributo || 'outros') === 'cidade' ? 'selected' : ''}>Cidade</option>
                    <option value="outros" ${(palavra.atributo || 'outros') === 'outros' ? 'selected' : ''}>Outros</option>
                </select>
            </td>
            <td class="action-buttons">
                <button class="btn-edit" onclick="editPalavra('${palavra._id}', '${palavra.original}')" title="Editar palavra">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-delete" onclick="deletePalavra('${palavra._id}')" title="Excluir palavra">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </td>
        </tr>
    `).join('');

    // Adiciona listeners para os checkboxes
    document.querySelectorAll('input[type="checkbox"][data-id]').forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });

    // Atualiza o estado do selectAll
    updateSelectAllState();
}

function updatePagination(data) {
    totalPages = data.total_pages;
    document.getElementById('pageInfo').textContent = `Página ${data.page} de ${totalPages}`;
    document.getElementById('prevPage').disabled = data.page <= 1;
    document.getElementById('nextPage').disabled = data.page >= totalPages;
}

function updateTotalInfo(total) {
    document.getElementById('totalInfo').textContent = `Total: ${total} palavras`;
}

async function deletePalavra(id) {
    if (!confirm('Tem certeza que deseja excluir esta palavra?')) return;
    
    try {
        const response = await fetch(`/api/palavras/${id}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.error) throw new Error(data.error);
        
        loadPalavras();
    } catch (error) {
        console.error('Erro ao deletar palavra:', error);
        alert('Erro ao deletar palavra');
    }
}

// Configuração do modal de edição
const editModal = document.getElementById('editModal');
const editPalavraInput = document.getElementById('editPalavra');
let currentEditId = null;

function editPalavra(id, palavra) {
    currentEditId = id;
    editPalavraInput.value = palavra;
    editModal.classList.add('show');
    editPalavraInput.focus();
}

async function salvarEdicao() {
    if (!currentEditId) return;
    
    try {
        const response = await fetch(`/api/palavras/${currentEditId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                palavra: editPalavraInput.value
            })
        });
        
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        
        editModal.classList.remove('show');
        loadPalavras();
    } catch (error) {
        console.error('Erro ao atualizar palavra:', error);
        alert('Erro ao atualizar palavra');
    }
}

async function atualizarAtributo(id, atributo) {
    try {
        const response = await fetch(`/api/palavras/${id}/atributo`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ atributo })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Erro ao atualizar atributo');
        }
    } catch (error) {
        console.error('Erro ao atualizar atributo:', error);
        alert('Erro ao atualizar atributo');
    }
}

// Event Listeners
document.getElementById('searchButton').addEventListener('click', () => {
    currentSearch = document.getElementById('searchInput').value;
    currentAtributo = document.getElementById('atributoFilter').value;
    currentTamanho = document.getElementById('tamanhoFilter').value;
    currentPage = 1;
    loadPalavras();
});

document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        currentSearch = e.target.value;
        currentAtributo = document.getElementById('atributoFilter').value;
        currentTamanho = document.getElementById('tamanhoFilter').value;
        currentPage = 1;
        loadPalavras();
    }
});

document.getElementById('perPage').addEventListener('change', (e) => {
    perPage = parseInt(e.target.value);
    currentPage = 1;
    loadPalavras();
});

document.getElementById('prevPage').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadPalavras();
    }
});

document.getElementById('nextPage').addEventListener('click', () => {
    if (currentPage < totalPages) {
        currentPage++;
        loadPalavras();
    }
});

document.getElementById('salvarEdicao').addEventListener('click', salvarEdicao);

document.querySelector('.close-button').addEventListener('click', () => {
    editModal.classList.remove('show');
});

document.getElementById('atributoFilter').addEventListener('change', (e) => {
    currentAtributo = e.target.value;
    currentPage = 1;
    loadPalavras();
});

// Adicione estas novas funções
function handleCheckboxChange(e) {
    const id = e.target.dataset.id;
    const row = e.target.closest('tr');
    
    if (e.target.checked) {
        selectedIds.add(id);
        row.classList.add('row-selected');
    } else {
        selectedIds.delete(id);
        row.classList.remove('row-selected');
    }
    
    updateDeleteButton();
    updateSelectAllState();
}

function updateDeleteButton() {
    const deleteButton = document.getElementById('deleteSelected');
    if (!deleteButton) return; // Verifica se o botão existe

    if (selectedIds.size > 0) {
        deleteButton.classList.add('active');
        deleteButton.disabled = false;
        deleteButton.textContent = `Excluir Selecionados (${selectedIds.size})`;
    } else {
        deleteButton.classList.remove('active');
        deleteButton.disabled = true;
        deleteButton.textContent = 'Excluir Selecionados (0)';
    }
}

function updateSelectAllState() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('input[type="checkbox"][data-id]');
    
    selectAllCheckbox.checked = checkboxes.length > 0 && 
                               Array.from(checkboxes).every(cb => cb.checked);
}

async function deleteSelectedPalavras() {
    if (!selectedIds.size) return;

    try {
        if (!confirm(`Deseja excluir ${selectedIds.size} palavra(s)?`)) {
            return;
        }

        const errors = [];
        for (const id of selectedIds) {
            try {
                const response = await fetch(`/api/palavras/${id}`, { 
                    method: 'DELETE'
                });
                
                if (!response.ok) {
                    const data = await response.json();
                    errors.push(`Erro ao excluir ID ${id}: ${data.error}`);
                }
            } catch (err) {
                errors.push(`Erro ao excluir ID ${id}: ${err.message}`);
            }
        }

        if (errors.length > 0) {
            console.error('Erros durante a exclusão:', errors);
            alert(`Alguns itens não puderam ser excluídos.\nVerifique o console para mais detalhes.`);
        }

        selectedIds.clear();
        updateDeleteButton();
        loadPalavras();
        
    } catch (error) {
        console.error('Erro ao excluir palavras:', error);
        alert('Erro ao excluir palavras selecionadas');
    }
}

// Adicione estes event listeners
document.getElementById('selectAll').addEventListener('change', e => {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][data-id]');
    
    // Para cada checkbox na página
    checkboxes.forEach(cb => {
        // Atualiza o estado do checkbox
        cb.checked = e.target.checked;
        
        // Pega o ID da palavra
        const id = cb.dataset.id;
        const row = cb.closest('tr');
        
        // Atualiza o Set de IDs selecionados e a classe da linha
        if (e.target.checked) {
            selectedIds.add(id);
            row.classList.add('row-selected');
        } else {
            selectedIds.delete(id);
            row.classList.remove('row-selected');
        }
    });
    
    // Atualiza o botão de excluir
    updateDeleteButton();
});

document.getElementById('deleteSelected').addEventListener('click', deleteSelectedPalavras);

// Carrega palavras inicialmente
loadPalavras(); 