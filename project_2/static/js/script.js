document.addEventListener('DOMContentLoaded', () => {
    const symptomsContainer = document.getElementById('symptoms-container');
    const symptomSearch = document.getElementById('symptom-search');
    const genderSelect = document.getElementById('gender');
    const femaleOptions = document.getElementById('female-options');
    const recommendBtn = document.getElementById('get-recommendation');
    const resultCard = document.getElementById('result-card');
    const outputContent = document.getElementById('recommendation-output');

    let allSymptoms = [];
    let selectedSymptoms = new Set();

    // Fetch symptoms from backend
    fetch('/get_symptoms')
        .then(res => res.json())
        .then(data => {
            allSymptoms = data;
            renderSymptoms(allSymptoms);
        });

    function renderSymptoms(symptoms) {
        symptomsContainer.innerHTML = '';
        symptoms.forEach(sym => {
            const div = document.createElement('div');
            div.className = `sym-item ${selectedSymptoms.has(sym) ? 'active' : ''}`;
            div.innerHTML = `
                <input type="checkbox" id="sym-${sym}" ${selectedSymptoms.has(sym) ? 'checked' : ''}>
                <label for="sym-${sym}">${sym}</label>
            `;
            div.addEventListener('click', (e) => {
                if (e.target.tagName !== 'INPUT') {
                    const checkbox = div.querySelector('input');
                    checkbox.checked = !checkbox.checked;
                    toggleSymptom(sym, checkbox.checked, div);
                }
            });
            div.querySelector('input').addEventListener('change', (e) => {
                toggleSymptom(sym, e.target.checked, div);
            });
            symptomsContainer.appendChild(div);
        });
    }

    function toggleSymptom(sym, checked, element) {
        if (checked) {
            selectedSymptoms.add(sym);
            element.classList.add('active');
        } else {
            selectedSymptoms.delete(sym);
            element.classList.remove('active');
        }
    }

    symptomSearch.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = allSymptoms.filter(s => s.toLowerCase().includes(term));
        renderSymptoms(filtered);
    });

    genderSelect.addEventListener('change', (e) => {
        if (e.target.value === 'female') {
            femaleOptions.classList.remove('hidden');
        } else {
            femaleOptions.classList.add('hidden');
        }
    });

    recommendBtn.addEventListener('click', () => {
        if (selectedSymptoms.size === 0) {
            alert('Please select at least one symptom.');
            return;
        }

        recommendBtn.textContent = 'Analyzing...';
        recommendBtn.disabled = true;

        const data = {
            symptoms: Array.from(selectedSymptoms).join(', '),
            age: document.getElementById('age').value,
            gender: genderSelect.value,
            pregnancy: document.getElementById('pregnancy').value,
            feeding: document.getElementById('feeding').value,
            duration: document.getElementById('duration').value
        };

        fetch('/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(data => {
            resultCard.classList.remove('hidden');
            outputContent.innerHTML = data.recommendation;
            resultCard.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(err => {
            alert('Error getting recommendation. Please try again.');
            console.error(err);
        })
        .finally(() => {
            recommendBtn.textContent = 'Analyze & Recommend';
            recommendBtn.disabled = false;
        });
    });
});
