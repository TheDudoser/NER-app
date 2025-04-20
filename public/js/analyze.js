function clearText() {
    document.getElementById('textInput').value = '';
    document.getElementById('fileInput').value = '';
    document.getElementById('resultsCard').style.display = 'none';
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
});
