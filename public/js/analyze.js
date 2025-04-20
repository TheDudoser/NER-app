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

document.getElementById('createDictionaryBtn').addEventListener('click', function() {
    // Показываем индикатор загрузки
    // const spinner = document.querySelector('.loading-spinner');
    // spinner.style.display = 'block';

    // Собираем данные для сохранения
    const analysisData = {
        phrases: Array.from(document.querySelectorAll('#resultsBody tr')).map(row => {
            const cells = row.querySelectorAll('td');
            return {
                phrase: cells[2].textContent,
                pattern_type: cells[0].textContent,
                tfidf_score: parseFloat(cells[3].textContent)
            };
        }),
        total_phrases: parseInt(document.getElementById('totalPhrases').textContent),
        unique_patterns: parseInt(document.getElementById('uniquePatterns').textContent)
    };

    // Отправляем данные на сервер
    fetch('/save-analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(analysisData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Перенаправляем на страницу словаря
            window.location.href = `/create-dictionary/${data.file_id}`;
        } else {
            alert('Ошибка при сохранении анализа');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка');
    })
    // .finally(() => {
    //     spinner.style.display = 'none';
    // });
});
