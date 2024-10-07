const API_BASE_URL = 'http://localhost:8000/api/v1';

// Ethics Evaluation
document.getElementById('ethics-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const decision = document.getElementById('decision').value;
    try {
        const response = await fetch(`${API_BASE_URL}/ethics/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ decision }),
        });
        const result = await response.json();
        displayEthicsResult(result);
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while evaluating ethics.');
    }
});

function displayEthicsResult(result) {
    const resultDiv = document.getElementById('ethics-result');
    resultDiv.innerHTML = `
        <h3>Ethics Evaluation Result</h3>
        <p><strong>Decision Score:</strong> ${result.decision_score}</p>
        <p><strong>Explanation:</strong> ${result.explanation}</p>
        <p><strong>Concerns:</strong></p>
        <ul>
            ${result.concerns.map(concern => `<li>${concern}</li>`).join('')}
        </ul>
        <p><strong>Improvement Suggestions:</strong></p>
        <ul>
            ${result.improvement_suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
        </ul>
    `;
}

// Knowledge Base Search
document.getElementById('search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = document.getElementById('search-query').value;
    try {
        const response = await fetch(`${API_BASE_URL}/knowledge/search?query=${encodeURIComponent(query)}`);
        const results = await response.json();
        displayKnowledgeResults(results);
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while searching the knowledge base.');
    }
});

function displayKnowledgeResults(results) {
    const resultsDiv = document.getElementById('knowledge-results');
    if (results.length === 0) {
        resultsDiv.innerHTML = '<p>No results found.</p>';
        return;
    }
    resultsDiv.innerHTML = results.map(entry => `
        <div class="knowledge-entry">
            <h3>${entry.title}</h3>
            <p>${entry.content}</p>
            <p><strong>Tags:</strong> ${entry.tags.join(', ')}</p>
            <p><strong>Author:</strong> ${entry.author_id}</p>
            <p><strong>Created:</strong> ${new Date(entry.created_at).toLocaleString()}</p>
        </div>
    `).join('');
}

// Add Knowledge Entry
document.getElementById('add-knowledge-btn').addEventListener('click', () => {
    document.getElementById('add-knowledge-form').style.display = 'block';
});

document.getElementById('knowledge-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('title').value;
    const content = document.getElementById('content').value;
    const tags = document.getElementById('tags').value.split(',').map(tag => tag.trim());
    const entry = {
        title,
        content,
        tags,
        author_id: 'user_123' // Replace with actual user ID when authentication is implemented
    };
    try {
        const response = await fetch(`${API_BASE_URL}/knowledge/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(entry),
        });
        const result = await response.json();
        alert('Knowledge entry added successfully!');
        document.getElementById('knowledge-form').reset();
        document.getElementById('add-knowledge-form').style.display = 'none';
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while adding the knowledge entry.');
    }
});