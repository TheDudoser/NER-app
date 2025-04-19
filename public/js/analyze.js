async function analyzeText() {
    const textInput = document.getElementById('textInput');
    const fileInput = document.getElementById('fileInput');
    const resultsCard = document.getElementById('resultsCard');
    const loadingSpinner = document.getElementById('loadingSpinner');

    let content = textInput.value.trim();
    const file = fileInput.files[0];

    if (!content && !file) {
        alert('Пожалуйста, введите текст или загрузите файл');
        return;
    }

    // Показываем индикатор загрузки
    loadingSpinner.style.display = 'block';
    resultsCard.style.display = 'none';

    try {
        const formData = new FormData();
        if (content) {
            formData.append('text', content);
        }
        if (file) {
            formData.append('file', file);
        }

        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при анализе текста: ' + error.message);
    } finally {
        loadingSpinner.style.display = 'none';
        resultsCard.style.display = 'block';
    }
}

function displayResults(data) {
    document.getElementById('totalPhrases').textContent = data.total_phrases;
    document.getElementById('uniquePatterns').textContent = data.unique_patterns;

    const tbody = document.getElementById('resultsBody');
    tbody.innerHTML = '';

    if (data.phrases && data.phrases.length > 0) {
        data.phrases.forEach(phrase => {
            const row = document.createElement('tr');
            row.innerHTML = `
                        <td><span class="phrase-type ${phrase.color}">${phrase.pattern_type}</span></td>
                        <td>${phrase.pattern_description}</td>
                        <td>${phrase.phrase}</td>
                        <td>${phrase.tfidf_score.toFixed(3)}</td>
                    `;
            tbody.appendChild(row);
        });
    } else {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" class="text-center text-muted">Не найдено подходящих словосочетаний</td>';
        tbody.appendChild(row);
    }
}

function clearText() {
    document.getElementById('textInput').value = '';
    document.getElementById('fileInput').value = '';
    document.getElementById('resultsCard').style.display = 'none';
}

function exportToJson() {
    const resultsBody = document.getElementById('resultsBody');
    const rows = resultsBody.querySelectorAll('tr');

    if (rows.length === 0 || (rows.length === 1 && rows[0].querySelector('td').colSpan === 4)) {
        alert('Нет данных для экспорта');
        return;
    }

    const data = Array.from(rows).map(row => {
        const cells = row.querySelectorAll('td');
        return {
            type: cells[0].textContent,
            description: cells[1].textContent,
            phrase: cells[2].textContent,
            tfidf: cells[3].textContent
        };
    });

    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'phrase_analysis_results.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Обработка загрузки файла
document.getElementById('fileInput').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        document.getElementById('textInput').value = e.target.result;
    };
    reader.readAsText(file);
});