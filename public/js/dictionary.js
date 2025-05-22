document.addEventListener('DOMContentLoaded', function () {
    // Получаем элементы колонок
    const columns = document.querySelectorAll('.drop-column');
    let draggedItem = null;
    let globalConnections = [];

    // Выбор порога if-idf
    const range = document.getElementById('tfidfRange');
    const number = document.getElementById('tfidfValue');

    let prevSelectedTerm = null;
    let selectedTerm = null;
    let selectedNonTerms = [];

    // Добавляем обработчики событий для перетаскивания
    columns.forEach(column => {
        column.addEventListener('dragover', function (e) {
            e.preventDefault();
            this.classList.add('highlight');
        });

        column.addEventListener('dragleave', function () {
            this.classList.remove('highlight');
        });

        column.addEventListener('drop', function (e) {
            e.preventDefault();
            this.classList.remove('highlight');
            // Вставка не всегда в конец, а туда, куда перетаскиваем
            if (draggedItem) {
                let afterElement = null;
                const mouseY = e.clientY;
                const cards = Array.from(this.querySelectorAll('.phrase-card:not([style*="display: none"])'));
                for (let card of cards) {
                    const rect = card.getBoundingClientRect();
                    if (mouseY < rect.top + rect.height / 2) {
                        afterElement = card;
                        break;
                    }
                }
                if (afterElement) {
                    this.insertBefore(draggedItem, afterElement);
                } else {
                    this.appendChild(draggedItem);
                }

                // Включаем showConnectedMode, если элемент перемещен не в phrases-column
                if (this.id !== 'phrases-column') {
                    showConnectedMode(draggedItem);
                } else {
                    draggedItem.classList.remove('connected');
                }
            }
        });
    });

    function showConnectedMode(card) {
        if (card.parentElement.id === 'terms-column') {
            prevSelectedTerm = selectedTerm;
            if (selectedTerm !== null) {
                prevSelectedTerm.classList.remove('connected');
            }
            selectedTerm = card;
            selectedTerm.classList.add('connected');
        } else {
            selectedNonTerms.push(card);
            card.classList.add('connected');
        }

        if (selectedTerm && card !== selectedTerm) {
            createConnection(selectedTerm, card);
            selectedNonTerms = [];
            // prevSelectedTerm = null;
        } else if (selectedNonTerms.length > 0 && selectedTerm === card && prevSelectedTerm === null) {
            for (let nonTerm of selectedNonTerms) {
                createConnection(card, nonTerm);
            }
        }

        // 3. Отображаем только карточки, связанные с новым термином,
        //    остальные скрываем в ненужных колонках (кроме phrases-column)
        document.querySelectorAll('.drop-column:not(#phrases-column):not(#terms-column) .phrase-card')
            .forEach(_ => {
                globalConnections.forEach(conn => {
                    const isLinked = conn.fromElement === selectedTerm;
                    conn.toElement.style.display = isLinked ? 'block' : 'none';

                    if (isLinked) {
                        conn.fromElement.classList.add('connected');
                    } else {
                        conn.fromElement.classList.remove('connected');
                    }
                });
            });
    }

    // Вешаем обработчик клика на все термы
    document.getElementById('terms-column')
        .addEventListener('click', event => {
            const card = event.target.closest('.phrase-card');
            if (!card) return;
            showConnectedMode(card);
        });

    // Обработчики для элементов, которые можно перетаскивать
    document.addEventListener('dragstart', function (e) {
        if (e.target.classList.contains('draggable')) {
            draggedItem = e.target;

            const connectionsToRemove = globalConnections.filter(conn =>
                conn.from === draggedItem.dataset.id || conn.to === draggedItem.dataset.id
            );

            // Удаляем соединения и обновляем статус connected
            connectionsToRemove.forEach(conn => {
                // Проверяем оставшиеся связи для fromElement
                const hasOtherFrom = globalConnections.some(c =>
                    c.from === conn.fromElement.dataset.id && c !== conn
                );
                if (!hasOtherFrom) conn.fromElement.classList.remove('connected');

                // Проверяем оставшиеся связи для toElement
                const hasOtherTo = globalConnections.some(c =>
                    c.to === conn.toElement.dataset.id && c !== conn
                );
                if (!hasOtherTo) conn.toElement.classList.remove('connected');
            });

            // Фильтруем массив соединений
            globalConnections = globalConnections.filter(conn =>
                !(conn.from === draggedItem.dataset.id || conn.to === draggedItem.dataset.id)
            );

            setTimeout(() => e.target.style.display = 'none', 0);
        }
    });

    document.addEventListener('dragend', function (e) {
        if (e.target.classList.contains('draggable')) {
            setTimeout(() => {
                e.target.style.display = 'block';
                draggedItem = null;
            }, 0);
        }
    });

    // Функция для создания соединения
    function createConnection(fromElement, toElement) {
        // Проверяем, что элементы в разных колонках
        const fromColumn = fromElement.closest('.drop-column');
        const toColumn = toElement.closest('.drop-column');

        if (fromColumn === toColumn) {
            alert('Можно связывать только элементы из разных колонок');
            return;
        }

        // Проверяем, что ни один из элементов не в колонке phrases-column
        if (fromColumn.id === 'phrases-column' || toColumn.id === 'phrases-column') {
            alert('Элементы из этой колонки нельзя связывать с другими элементами');
            return;
        }

        // Проверяем, нет ли уже такого соединения
        const existingConnection = globalConnections.find(conn =>
            (conn.from === fromElement.dataset.id && conn.to === toElement.dataset.id) ||
            (conn.from === toElement.dataset.id && conn.to === fromElement.dataset.id)
        );

        if (existingConnection) {
            alert('Эти элементы уже связаны');
            return;
        }

        // Сохраняем информацию о соединении
        const connection = {
            from: fromElement.dataset.id,
            to: toElement.dataset.id,
            fromElement: fromElement,
            toElement: toElement
        };

        globalConnections.push(connection);

        // Добавляем классы для визуального отображения связи
        fromElement.classList.add('connected');
        toElement.classList.add('connected');
    }

    // Функция для получения данных словаря
    function getDictionaryData() {
        let fileId = document.getElementById('file_id')?.textContent;

        // Общая функция для обработки элементов колонок
        const processColumn = (elementId, phraseType) =>
            Array.from(document.getElementById(elementId).children)
                .map(el => ({
                    id: el.dataset.id,
                    text: el.textContent.split('\n')[1].trim(),
                    tfidf: parseFloat(el.dataset.tfidf),
                    type: el.dataset.type,
                    hidden: el.dataset.hidden === 'true',
                    phrase_type: phraseType
                }));

        // Собираем все элементы в один массив
        const allItems = [
            ...processColumn('phrases-column', 'phrase'),
            ...processColumn('terms-column', 'term'),
            ...processColumn('synonyms-column', 'synonym'),
            ...processColumn('definitions-column', 'definition')
        ];

        return {
            id: fileId,
            phrases: allItems,
            connections: globalConnections.map(conn => ({
                from_id: conn.from,
                to_id: conn.to
            })),
            tfidf_range: parseFloat(number.value),
            document_text: window.TEXT_CONTENT ?? ''
        };
    }

    // Функция для загрузки данных словаря
    function loadDictionaryData(data) {
        // Обновляем фильтр по tf-idf
        number.value = data.tfidf_range;
        range.value = data.tfidf_range;
        applyTfidfFilter(data.tfidf_range);

        // Восстанавливаем соединения
        if (data.connections) {
            data.connections.forEach(conn => {
                const fromElement = document.querySelector(`.phrase-card[data-id="${conn.from}"]`);
                const toElement = document.querySelector(`.phrase-card[data-id="${conn.to}"]`);

                if (fromElement && toElement) {
                    createConnection(fromElement, toElement);
                }
            });
        }

        const termsCol = document.getElementById('terms-column');
        const lastTerm = termsCol.querySelector('.phrase-card:last-child');
        document.getElementById('terms-column')
        if (lastTerm) {
            showConnectedMode(lastTerm);
        }
    }

    // Экспорт словаря
    document.getElementById('exportDictionaryBtn').addEventListener('click', function () {
        const dictionaryName = document.getElementById('dictionaryName').value.trim();
        if (!dictionaryName) {
            alert('Введите название словаря');
            return;
        }

        const dictionary = getDictionaryData();
        dictionary.name = dictionaryName;

        if (dictionary.id !== undefined) {
            fetch(`/api/dictionary/${dictionary.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dictionary)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        window.location.reload()
                    } else {
                        alert('Ошибка при обновлении словаря: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Произошла ошибка');
                });
        } else {
            fetch(`/api/dictionary`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dictionary)
            })
                .then(response => response.json())
                .then(data => {
                    console.log(data)
                    if (data.success) {
                        alert(data.message);
                        window.location.href = `/dictionary/${data.dictionary_id}/edit`;
                    } else {
                        alert('Ошибка при сохранении словаря: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Произошла ошибка');
                });
        }
    });

    // В начале файла добавим переменную для хранения текущего словаря
    let currentDictionaryId = document.getElementById('file_id')?.textContent || null;

    // Обработчик кнопки "Пополнить словарь"
    document.getElementById('addToDictionaryBtn').addEventListener('click', function () {
        fetch('/api/dictionaries')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Фильтруем текущий словарь из списка (если мы в режиме редактирования)
                    const dictionaries = data.data.filter(dict =>
                        !currentDictionaryId || dict.id.toString() !== currentDictionaryId
                    );

                    // Обновляем select в модальном окне
                    const select = document.getElementById('targetDictionarySelect');
                    select.innerHTML = `
                    <option value="" selected disabled>Выберите словарь...</option>
                    ${dictionaries.map(dict =>
                        `<option value="${dict.id}">${dict.name}</option>`
                    ).join('')}
                `;

                    // Показываем модальное окно
                    const modal = new bootstrap.Modal(document.getElementById('addToDictionaryModal'));
                    modal.show();
                } else {
                    alert('Ошибка загрузки списка словарей: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при загрузке словарей');
            });
    });

    // Обработчик подтверждения объединения со словарём
    document.getElementById('confirmAddToDictionaryBtn').addEventListener('click', function () {
        const targetDictionaryId = document.getElementById('targetDictionarySelect').value;
        if (!targetDictionaryId) {
            alert('Выберите словарь для объединения');
            return;
        }

        const currentDictionaryData = getDictionaryData();
        currentDictionaryData.name = 'dict_for_merge';

        fetch(`/api/dictionary/${targetDictionaryId}/merge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentDictionaryData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    window.location.href = `/dictionary/${targetDictionaryId}/edit`;
                } else {
                    alert('Ошибка при пополнении словаря: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка');
            })
            .finally(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('addToDictionaryModal'));
                modal.hide();
            });
    });

    // Проставление связей при редактировании
    if (window.DICTIONARY_DATA) {
        loadDictionaryData(window.DICTIONARY_DATA);
    }

    // Логика работы с порогом ifidf
    range.addEventListener('input', () => {
        number.value = range.value;
        applyTfidfFilter(parseFloat(range.value));
    });

    number.addEventListener('input', () => {
        let val = parseFloat(number.value);
        if (isNaN(val)) val = 0;
        val = Math.min(Math.max(val, 0), 1);
        range.value = val.toFixed(3);
        applyTfidfFilter(val);
    });

    function applyTfidfFilter(threshold) {
        document.querySelectorAll('.phrase-card').forEach(card => {
            const tfidf = parseFloat(card.dataset.tfidf);
            if (tfidf < threshold) {
                card.style.display = 'none';
                card.dataset.hidden = 'true';
            } else {
                card.style.display = 'block';
                card.dataset.hidden = 'false';
            }
        });
    }
});
