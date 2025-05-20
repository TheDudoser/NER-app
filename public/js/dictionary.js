document.addEventListener('DOMContentLoaded', function () {
    // Получаем элементы колонок
    const columns = document.querySelectorAll('.drop-column');
    let draggedItem = null;
    let connectionMode = false;
    let sourceElement = null;
    let connectionLines = [];

    // Выбор порога if-idf
    const range = document.getElementById('tfidfRange');
    const number = document.getElementById('tfidfValue');

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
                updateAllConnectionLines();
            }
        });
    });

    // Обработчики для элементов, которые можно перетаскивать
    document.addEventListener('dragstart', function (e) {
        if (e.target.classList.contains('draggable')) {
            draggedItem = e.target;

            const connectionsToRemove = connectionLines.filter(conn =>
                conn.from === draggedItem.dataset.id || conn.to === draggedItem.dataset.id
            );

            // Удаляем соединения и обновляем статус connected
            connectionsToRemove.forEach(conn => {
                conn.line.remove();

                // Проверяем оставшиеся связи для fromElement
                const hasOtherFrom = connectionLines.some(c =>
                    c.from === conn.fromElement.dataset.id && c !== conn
                );
                if (!hasOtherFrom) conn.fromElement.classList.remove('connected');

                // Проверяем оставшиеся связи для toElement
                const hasOtherTo = connectionLines.some(c =>
                    c.to === conn.toElement.dataset.id && c !== conn
                );
                if (!hasOtherTo) conn.toElement.classList.remove('connected');
            });

            // Фильтруем массив соединений
            connectionLines = connectionLines.filter(conn =>
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
                updateAllConnectionLines(); // Обновляем оставшиеся соединения
            }, 0);
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

    // Добавляем кнопки соединения к существующим карточкам
    document.querySelectorAll('.phrase-card').forEach(card => {
        addConnectButton(card);
    });

    // Функция для создания кнопки соединения
    function addConnectButton(card) {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        const path1 = document.createElementNS("http://www.w3.org/2000/svg", 'path');
        const path2 = document.createElementNS("http://www.w3.org/2000/svg", 'path');

        svg.classList.add('connect-svg');
        svg.setAttribute('viewbox', '0 0 16 16');
        svg.setAttribute('width', '16px');
        svg.setAttribute('height', '16px');
        svg.setAttribute('fill', 'currentColor');

        path1.setAttribute('d', 'M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16');
        path2.setAttribute('d', 'M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4');

        svg.appendChild(path1);
        svg.appendChild(path2);

        svg.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleConnectionMode(card);
        });
        card.appendChild(svg);
    }

    // Функция для переключения режима соединения
    function toggleConnectionMode(card) {
        if (connectionMode && sourceElement === card) {
            // Выходим из режима соединения
            connectionMode = false;
            // sourceElement.classList.remove('connected');
            sourceElement = null;
            document.body.classList.remove('connection-mode');
        } else if (!connectionMode) {
            // Входим в режим соединения
            connectionMode = true;
            sourceElement = card;
            document.body.classList.add('connection-mode');
            card.classList.add('connected');
        } else {
            // Создаем соединение
            createConnection(sourceElement, card);
            // Выходим из режима соединения
            connectionMode = false;
            // sourceElement.classList.remove('connected');
            sourceElement = null;
            document.body.classList.remove('connection-mode');
        }
    }

    // Функция для создания соединения
    function createConnection(fromElement, toElement) {
        // Проверяем, что элементы в разных колонках
        const fromColumn = fromElement.closest('.drop-column');
        const toColumn = toElement.closest('.drop-column');

        if (fromColumn === toColumn) {
            alert('Можно связывать только элементы из разных колонок');
            return;
        }

        // Проверяем, нет ли уже такого соединения
        const existingConnection = connectionLines.find(conn =>
            (conn.from === fromElement.dataset.id && conn.to === toElement.dataset.id) ||
            (conn.from === toElement.dataset.id && conn.to === fromElement.dataset.id)
        );

        if (existingConnection) {
            alert('Эти элементы уже связаны');
            return;
        }

        // Создаем линию
        const line = document.createElement('div');
        line.className = 'connection-line';
        fromColumn.appendChild(line)

        // Добавляем кнопку удаления
        const deleteBtn = document.createElement('div');
        deleteBtn.className = 'delete-connection';
        deleteBtn.innerHTML = '&times;';
        deleteBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            removeConnection(line);
        });
        line.appendChild(deleteBtn);

        document.querySelector('.connection-container').appendChild(line);

        // Обновляем позицию линии
        updateConnectionLine(line, fromElement, toElement);

        // Сохраняем информацию о соединении
        const connection = {
            from: fromElement.dataset.id,
            to: toElement.dataset.id,
            line: line,
            fromElement: fromElement,
            toElement: toElement
        };

        connectionLines.push(connection);

        // Добавляем классы для визуального отображения связи
        fromElement.classList.add('connected');
        toElement.classList.add('connected');
    }

    // Функция для удаления соединения
    function removeConnection(line) {
        const connectionIndex = connectionLines.findIndex(conn => conn.line === line);
        if (connectionIndex !== -1) {
            const connection = connectionLines[connectionIndex];
            connection.fromElement.classList.remove('connected');
            connection.toElement.classList.remove('connected');
            line.remove();
            connectionLines.splice(connectionIndex, 1);
        }
    }

    function updateConnectionLine(line, fromElement, toElement) {
        const fromRect = fromElement.getBoundingClientRect();
        const toRect = toElement.getBoundingClientRect();
        const containerRect = line.parentElement.getBoundingClientRect();

        // Определяем центр каждого элемента
        const fromCenter = {
            x: (fromRect.left + fromRect.right) / 2 - containerRect.left,
            y: (fromRect.top + fromRect.bottom) / 2 - containerRect.top
        };
        const toCenter = {
            x: (toRect.left + toRect.right) / 2 - containerRect.left,
            y: (toRect.top + toRect.bottom) / 2 - containerRect.top
        };

        // Определяем направление от from к to
        const dx = toCenter.x - fromCenter.x;
        const dy = toCenter.y - fromCenter.y;

        // Вычисляем угол между центрами
        const angle = Math.atan2(dy, dx);

        // Находим точки пересечения линии с границами элементов
        const fromPoint = getIntersectionPoint(fromRect, containerRect, angle);
        const toPoint = getIntersectionPoint(toRect, containerRect, -Math.PI + angle);

        // Вычисляем длину и угол для линии
        const length = Math.sqrt(Math.pow(toPoint.x - fromPoint.x, 2) + Math.pow(toPoint.y - fromPoint.y, 2));
        const lineAngle = Math.atan2(toPoint.y - fromPoint.y, toPoint.x - fromPoint.x) * 180 / Math.PI;

        // Устанавливаем стили линии
        line.style.width = `${length}px`;
        line.style.left = `${fromPoint.x}px`;
        line.style.top = `${fromPoint.y}px`;
        line.style.transform = `rotate(${lineAngle}deg)`;
        line.style.zIndex = '1';
    }

    // Функция для нахождения точки пересечения линии с границей элемента
    function getIntersectionPoint(rect, containerRect, angle) {
        const center = {
            x: (rect.left + rect.right) / 2 - containerRect.left,
            y: (rect.top + rect.bottom) / 2 - containerRect.top
        };

        // Полуширина и полувысота элемента
        const halfWidth = rect.width / 2;
        const halfHeight = rect.height / 2;

        // Вычисляем точку пересечения с границей прямоугольника
        let x, y;

        // Определяем квадрант угла
        const absAngle = Math.abs(angle);
        const tanAngle = Math.tan(absAngle);

        // Вычисляем точку пересечения в зависимости от угла
        if (absAngle <= Math.PI / 4 || absAngle > 3 * Math.PI / 4) {
            // Пересекаем правую или левую границу
            const signX = Math.cos(angle) > 0 ? 1 : -1;
            x = center.x + signX * halfWidth;
            y = center.y + signX * halfWidth * tanAngle * (Math.sin(angle) > 0 ? 1 : -1);

            // Проверяем, не выходит ли y за границы
            if (y > center.y + halfHeight) {
                y = center.y + halfHeight;
                x = center.x + (y - center.y) / tanAngle;
            } else if (y < center.y - halfHeight) {
                y = center.y - halfHeight;
                x = center.x - (y - center.y) / tanAngle;
            }
        } else {
            // Пересекаем верхнюю или нижнюю границу
            const signY = Math.sin(angle) > 0 ? 1 : -1;
            y = center.y + signY * halfHeight;
            x = center.x + signY * halfHeight / tanAngle * (Math.cos(angle) > 0 ? 1 : -1);

            // Проверяем, не выходит ли x за границы
            if (x > center.x + halfWidth) {
                x = center.x + halfWidth;
                y = center.y + (x - center.x) * tanAngle;
            } else if (x < center.x - halfWidth) {
                x = center.x - halfWidth;
                y = center.y - (x - center.x) * tanAngle;
            }
        }

        return {x, y};
    }

    // Функция для обновления всех линий
    function updateAllConnectionLines() {
        connectionLines.forEach(conn => {
            if (conn.fromElement && conn.toElement) {
                updateConnectionLine(conn.line, conn.fromElement, conn.toElement);
            }
        });
    }

    // Обработчик клика в режиме соединения
    document.addEventListener('click', function (e) {
        if (!connectionMode || !sourceElement) return;

        const targetCard = e.target.closest('.phrase-card');
        if (targetCard && targetCard !== sourceElement) {
            createConnection(sourceElement, targetCard);
            toggleConnectionMode(sourceElement); // Выходим из режима соединения
        }
    });

    // Обновляем позиции линий при изменении размера окна
    window.addEventListener('resize', function () {
        updateAllConnectionLines();
    });

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
            connections: connectionLines.map(conn => ({
                from_id: conn.from,
                to_id: conn.to
            })),
            tfidf_range: parseFloat(number.value),
            document_text: window.TEXT_CONTENT ?? ''
        };
    }

    // Функция для загрузки данных словаря
    function loadDictionaryData(data) {
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

        // Обновляем фильтр по tf-idf
        number.value = data.tfidf_range;
        range.value = data.tfidf_range;
        applyTfidfFilter(data.tfidf_range);
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

    // Удаление всех связей
    document.getElementById('clearConnectionsBtn').addEventListener('click', function () {
        // Удаляем все линии соединений
        document.querySelectorAll('.connection-line').forEach(line => line.remove());

        // Удаляем класс connected со всех карточек
        document.querySelectorAll('.phrase-card.connected').forEach(card => {
            card.classList.remove('connected');
        });

        // Очищаем массив соединений
        connectionLines = [];
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
        updateAllConnectionLines();
    }
});
