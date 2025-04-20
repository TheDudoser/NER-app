document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы колонок
    const columns = document.querySelectorAll('.drop-column');
    let draggedItem = null;

    // Добавляем обработчики событий для перетаскивания
    columns.forEach(column => {
        column.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('highlight');
        });

        column.addEventListener('dragleave', function() {
            this.classList.remove('highlight');
        });

        column.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('highlight');

            if (draggedItem) {
                this.appendChild(draggedItem);
            }
        });
    });

    // Обработчики для элементов, которые можно перетаскивать
    document.addEventListener('dragstart', function(e) {
        if (e.target.classList.contains('draggable')) {
            draggedItem = e.target;
            setTimeout(() => {
                e.target.style.display = 'none';
            }, 0);
        }
    });

    document.addEventListener('dragend', function(e) {
        if (e.target.classList.contains('draggable')) {
            setTimeout(() => {
                e.target.style.display = 'block';
                draggedItem = null;
            }, 0);
        }
    });

    // Сохранение черновика
    document.getElementById('saveDraftBtn').addEventListener('click', function() {
        const dictionary = getDictionaryData();
        localStorage.setItem('dictionaryDraft', JSON.stringify(dictionary));
        alert('Черновик сохранен');
    });

    // Экспорт словаря
    document.getElementById('exportDictionaryBtn').addEventListener('click', function() {
    const dictionaryName = document.getElementById('dictionaryName').value.trim();
    if (!dictionaryName) {
        alert('Введите название словаря');
        return;
    }

    const dictionary = getDictionaryData();
    dictionary.name = dictionaryName;

    fetch(`/save-dictionary/${dictionary.file_id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dictionary)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Словарь успешно сохранен');
            // Можно перенаправить на другую страницу или очистить форму
        } else {
            alert('Ошибка при сохранении словаря: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка');
    });
});

    // Загрузка черновика при наличии
    const draft = localStorage.getItem('dictionaryDraft');
    if (draft) {
        loadDictionaryData(JSON.parse(draft));
    }

    // Функция для получения данных словаря
    function getDictionaryData() {
        return {
            file_id: document.body.dataset.fileId,
            terms: Array.from(document.getElementById('terms-column').children)
                .map(el => ({
                    id: el.dataset.id,
                    text: el.textContent.split('\n')[0], // Берем только текст фразы
                    tfidf: parseFloat(el.dataset.tfidf),
                    type: el.dataset.type
                })),
            synonyms: Array.from(document.getElementById('synonyms-column').children)
                .map(el => ({
                    id: el.dataset.id,
                    text: el.textContent.split('\n')[0],
                    tfidf: parseFloat(el.dataset.tfidf),
                    type: el.dataset.type
                })),
            definitions: Array.from(document.getElementById('definitions-column').children)
                .map(el => ({
                    id: el.dataset.id,
                    text: el.textContent.split('\n')[0],
                    tfidf: parseFloat(el.dataset.tfidf),
                    type: el.dataset.type
                }))
        };
    }

    // Функция для загрузки данных словаря
    function loadDictionaryData(data) {
        clearColumns();

        data.terms.forEach(item => {
            document.getElementById('terms-column').appendChild(createPhraseCard(item));
        });

        data.synonyms.forEach(item => {
            document.getElementById('synonyms-column').appendChild(createPhraseCard(item));
        });

        data.definitions.forEach(item => {
            document.getElementById('definitions-column').appendChild(createPhraseCard(item));
        });
    }

    // Функция для создания карточки фразы
    function createPhraseCard(item) {
        const card = document.createElement('div');
        card.className = 'phrase-card draggable';
        card.draggable = true;
        card.dataset.id = item.id;
        card.textContent = item.text;
        return card;
    }

    // Функция для очистки колонок
    function clearColumns() {
        document.getElementById('terms-column').innerHTML = '';
        document.getElementById('synonyms-column').innerHTML = '';
        document.getElementById('definitions-column').innerHTML = '';
    }
});
