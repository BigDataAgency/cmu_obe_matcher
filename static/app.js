const API_BASE = '/api/v1';

let allCLOs = [];
let currentAnalysis = null;
let currentCompanyName = null;

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => 
        btn.textContent.includes(tabName === 'add-company' ? 'Add Company' : 
                                 tabName === 'dashboard' ? 'Dashboard' :
                                 tabName === 'companies' ? 'Companies' : 'CLO Reference')
    );
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    if (tabName === 'dashboard') {
        loadDashboard();
    } else if (tabName === 'companies') {
        loadCompanies();
    } else if (tabName === 'clos') {
        loadCLOsReference();
    }
}

async function generateMockData() {
    try {
        const response = await fetch(`${API_BASE}/generate-mock-data`, {
            method: 'POST'
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || `Request failed (${response.status})`);
        }

        await loadCompanies();

        const dashboardTab = document.getElementById('dashboard-tab');
        if (dashboardTab && dashboardTab.classList.contains('active')) {
            await loadDashboard();
        }

        alert('Mock companies generated successfully!');
    } catch (error) {
        alert(`Error generating mock data: ${error.message}`);
    }
}

async function loadCLOs() {
    try {
        const response = await fetch(`${API_BASE}/clos`);
        const data = await response.json();
        allCLOs = data.clos;
    } catch (error) {
        console.error('Error loading CLOs:', error);
    }
}

document.getElementById('company-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const companyName = document.getElementById('company-name').value;
    const requirements = document.getElementById('requirements').value;
    const culture = document.getElementById('culture').value;
    const desiredTraits = document.getElementById('desired-traits').value;
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = '🔄 Analyzing...';
    
    try {
        const response = await fetch(`${API_BASE}/analyze-company`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                company_name: companyName,
                requirements: requirements,
                culture: culture || null,
                desired_traits: desiredTraits || null
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze company');
        }
        
        const data = await response.json();
        currentAnalysis = data;
        displayAnalysisResults(data);
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '🔍 Analyze with AI';
    }
});

function displayAnalysisResults(data) {
    const resultSection = document.getElementById('analysis-result');
    const companyInfo = document.getElementById('company-info');
    const aiReasoning = document.getElementById('ai-reasoning');
    const cloSelection = document.getElementById('clo-selection');
    
    companyInfo.innerHTML = `
        <h4>${data.company_name}</h4>
        <p><strong>Requirements:</strong> ${data.requirements}</p>
        ${data.culture ? `<p><strong>Culture:</strong> ${data.culture}</p>` : ''}
        ${data.desired_traits ? `<p><strong>Desired Traits:</strong> ${data.desired_traits}</p>` : ''}
    `;
    
    aiReasoning.innerHTML = `
        <strong>AI Reasoning:</strong>
        <p>${data.ai_reasoning}</p>
    `;
    
    cloSelection.innerHTML = '';
    allCLOs.forEach(clo => {
        const isSelected = data.ai_suggested_clos.includes(clo.id);
        const cloItem = document.createElement('div');
        cloItem.className = `clo-item ${isSelected ? 'selected' : ''}`;
        cloItem.innerHTML = `
            <div class="clo-item-header">
                <input type="checkbox" id="clo-${clo.id}" ${isSelected ? 'checked' : ''}>
                <span class="clo-item-id">${clo.id}</span>
                <span class="clo-item-name">${clo.name}</span>
            </div>
            <div class="clo-item-desc">${clo.description}</div>
        `;
        
        cloItem.addEventListener('click', (e) => {
            if (e.target.type !== 'checkbox') {
                const checkbox = cloItem.querySelector('input[type="checkbox"]');
                checkbox.checked = !checkbox.checked;
            }
            cloItem.classList.toggle('selected');
        });
        
        cloSelection.appendChild(cloItem);
    });
    
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

async function saveCompany() {
    const selectedCLOs = Array.from(document.querySelectorAll('#clo-selection input[type="checkbox"]:checked'))
        .map(cb => cb.id.replace('clo-', ''));
    
    if (selectedCLOs.length === 0) {
        alert('Please select at least one CLO');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/companies/${currentAnalysis.company_name}/clos`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                selected_clos: selectedCLOs
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save company');
        }
        
        alert('Company saved successfully!');
        resetForm();
        showTab('companies');
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function resetForm() {
    document.getElementById('company-form').reset();
    document.getElementById('analysis-result').style.display = 'none';
    currentAnalysis = null;
}

async function loadCompanies() {
    const loadingDiv = document.getElementById('companies-loading');
    const companiesList = document.getElementById('companies-list');
    
    loadingDiv.style.display = 'block';
    companiesList.innerHTML = '';
    
    try {
        if (allCLOs.length === 0) {
            await loadCLOs();
        }

        const response = await fetch(`${API_BASE}/companies`);
        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || `Request failed (${response.status})`);
        }
        const data = await response.json();
        
        loadingDiv.style.display = 'none';
        
        if (data.companies.length === 0) {
            companiesList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🏢</div>
                    <div class="empty-state-text">No companies added yet. Add your first company!</div>
                </div>
            `;
            return;
        }
        
        data.companies.forEach(company => {
            const companyCard = document.createElement('div');
            companyCard.className = 'company-card';
            
            const cloTags = company.selected_clos.map(cloId => {
                const clo = allCLOs.find(c => c.id === cloId);
                return `<span class="clo-tag">${cloId}: ${clo ? clo.name : 'Unknown'}</span>`;
            }).join('');
            
            companyCard.innerHTML = `
                <h3>${company.company_name}</h3>
                <div class="company-card-details">
                    <p><strong>Requirements:</strong> ${company.requirements.substring(0, 150)}${company.requirements.length > 150 ? '...' : ''}</p>
                    ${company.culture ? `<p><strong>Culture:</strong> ${company.culture.substring(0, 100)}${company.culture.length > 100 ? '...' : ''}</p>` : ''}
                    <p><strong>Selected CLOs (${company.selected_clos.length}):</strong></p>
                    <div class="clo-tags">${cloTags}</div>
                </div>
                <div class="company-actions">
                    <button class="btn-primary" onclick="viewCompanyDetail('${company.company_name}')">View/Edit</button>
                </div>
            `;
            
            companiesList.appendChild(companyCard);
        });
        
    } catch (error) {
        loadingDiv.style.display = 'none';
        companiesList.innerHTML = `<p style="color: red;">Error loading companies: ${error.message}</p>`;
    }
}

async function viewCompanyDetail(companyName) {
    try {
        const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(companyName)}`);
        const company = await response.json();
        
        currentCompanyName = companyName;
        
        document.getElementById('modal-company-name').textContent = company.company_name;
        document.getElementById('modal-company-details').innerHTML = `
            <p><strong>Requirements:</strong> ${company.requirements}</p>
            ${company.culture ? `<p><strong>Culture:</strong> ${company.culture}</p>` : ''}
            ${company.desired_traits ? `<p><strong>Desired Traits:</strong> ${company.desired_traits}</p>` : ''}
            <p><strong>AI Reasoning:</strong> ${company.ai_reasoning}</p>
        `;
        
        const modalCloSelection = document.getElementById('modal-clo-selection');
        modalCloSelection.innerHTML = '';
        
        allCLOs.forEach(clo => {
            const isSelected = company.selected_clos.includes(clo.id);
            const cloItem = document.createElement('div');
            cloItem.className = `clo-item ${isSelected ? 'selected' : ''}`;
            cloItem.innerHTML = `
                <div class="clo-item-header">
                    <input type="checkbox" id="modal-clo-${clo.id}" ${isSelected ? 'checked' : ''}>
                    <span class="clo-item-id">${clo.id}</span>
                    <span class="clo-item-name">${clo.name}</span>
                </div>
                <div class="clo-item-desc">${clo.description}</div>
            `;
            
            cloItem.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox') {
                    const checkbox = cloItem.querySelector('input[type="checkbox"]');
                    checkbox.checked = !checkbox.checked;
                }
                cloItem.classList.toggle('selected');
            });
            
            modalCloSelection.appendChild(cloItem);
        });
        
        document.getElementById('company-detail-modal').classList.add('active');
        
    } catch (error) {
        alert(`Error loading company details: ${error.message}`);
    }
}

async function updateCompanyCLOs() {
    const selectedCLOs = Array.from(document.querySelectorAll('#modal-clo-selection input[type="checkbox"]:checked'))
        .map(cb => cb.id.replace('modal-clo-', ''));
    
    if (selectedCLOs.length === 0) {
        alert('Please select at least one CLO');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(currentCompanyName)}/clos`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                selected_clos: selectedCLOs
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update company CLOs');
        }
        
        alert('Company CLOs updated successfully!');
        closeModal();
        loadCompanies();
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function deleteCompany() {
    if (!confirm(`Are you sure you want to delete ${currentCompanyName}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(currentCompanyName)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete company');
        }
        
        alert('Company deleted successfully!');
        closeModal();
        loadCompanies();
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function closeModal() {
    document.getElementById('company-detail-modal').classList.remove('active');
    currentCompanyName = null;
}

async function loadCLOsReference() {
    const loadingDiv = document.getElementById('clos-loading');
    const closReference = document.getElementById('clos-reference');
    
    loadingDiv.style.display = 'block';
    closReference.innerHTML = '';
    
    try {
        if (allCLOs.length === 0) {
            await loadCLOs();
        }
        
        loadingDiv.style.display = 'none';
        
        const grid = document.createElement('div');
        grid.className = 'clo-reference-grid';
        
        allCLOs.forEach(clo => {
            const item = document.createElement('div');
            item.className = 'clo-reference-item';
            item.innerHTML = `
                <h4>${clo.id}: ${clo.name}</h4>
                <p>${clo.description}</p>
            `;
            grid.appendChild(item);
        });
        
        closReference.appendChild(grid);
        
    } catch (error) {
        loadingDiv.style.display = 'none';
        closReference.innerHTML = `<p style="color: red;">Error loading CLOs: ${error.message}</p>`;
    }
}

window.onclick = function(event) {
    const modal = document.getElementById('company-detail-modal');
    if (event.target === modal) {
        closeModal();
    }
}

loadCLOs();

// Dashboard Charts
let cloFrequencyChart = null;
let topCLOsChart = null;

async function loadDashboard() {
    try {
        const [companiesResponse, closResponse] = await Promise.all([
            fetch(`${API_BASE}/companies`),
            fetch(`${API_BASE}/clos`)
        ]);

        if (!companiesResponse.ok) {
            const text = await companiesResponse.text();
            throw new Error(text || `Request failed (${companiesResponse.status})`);
        }
        if (!closResponse.ok) {
            const text = await closResponse.text();
            throw new Error(text || `Request failed (${closResponse.status})`);
        }
        
        const companiesData = await companiesResponse.json();
        const closData = await closResponse.json();
        
        const companies = companiesData.companies;
        const clos = closData.clos;

        const emptyState = document.getElementById('dashboard-empty');
        if (emptyState) {
            emptyState.style.display = companies.length === 0 ? 'block' : 'none';
        }
        
        if (companies.length === 0) {
            document.getElementById('total-companies').textContent = '0';
            document.getElementById('total-clos-used').textContent = '0';
            document.getElementById('most-popular-clo').textContent = '-';
            document.getElementById('avg-clos-per-company').textContent = '0';

            const heatmapContainer = document.getElementById('heatmap-container');
            if (heatmapContainer) {
                heatmapContainer.innerHTML = '';
            }

            if (cloFrequencyChart) {
                cloFrequencyChart.destroy();
                cloFrequencyChart = null;
            }
            if (topCLOsChart) {
                topCLOsChart.destroy();
                topCLOsChart = null;
            }
            return;
        }
        
        // Calculate statistics
        const cloFrequency = {};
        let totalCLOs = 0;
        
        clos.forEach(clo => {
            cloFrequency[clo.id] = {
                count: 0,
                name: clo.name
            };
        });
        
        companies.forEach(company => {
            company.selected_clos.forEach(cloId => {
                if (cloFrequency[cloId]) {
                    cloFrequency[cloId].count++;
                    totalCLOs++;
                }
            });
        });
        
        const cloFrequencyArray = Object.entries(cloFrequency)
            .map(([id, data]) => ({ id, ...data }))
            .sort((a, b) => b.count - a.count);
        
        const closInUse = cloFrequencyArray.filter(c => c.count > 0).length;
        const mostPopular = cloFrequencyArray[0];
        const avgCLOs = (totalCLOs / companies.length).toFixed(1);
        
        // Update statistics
        document.getElementById('total-companies').textContent = companies.length;
        document.getElementById('total-clos-used').textContent = closInUse;
        document.getElementById('most-popular-clo').textContent = mostPopular.count > 0 ? 
            `${mostPopular.id}: ${mostPopular.name}` : '-';
        document.getElementById('avg-clos-per-company').textContent = avgCLOs;
        
        // Create CLO Frequency Chart
        createCLOFrequencyChart(cloFrequencyArray);
        
        // Create Top 10 CLOs Chart
        createTopCLOsChart(cloFrequencyArray.slice(0, 10));
        
        // Create Heatmap
        createHeatmap(companies, clos);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        const emptyState = document.getElementById('dashboard-empty');
        if (emptyState) {
            emptyState.style.display = 'block';
            emptyState.querySelector('.empty-state-text').textContent = `Error loading dashboard: ${error.message}`;
        }
    }
}

function createCLOFrequencyChart(data) {
    const ctx = document.getElementById('clo-frequency-chart');
    
    if (cloFrequencyChart) {
        cloFrequencyChart.destroy();
    }
    
    cloFrequencyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.id),
            datasets: [{
                label: 'Number of Companies',
                data: data.map(d => d.count),
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            return `${data[index].id}: ${data[index].name}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function createTopCLOsChart(data) {
    const ctx = document.getElementById('top-clos-chart');
    
    if (topCLOsChart) {
        topCLOsChart.destroy();
    }
    
    const filteredData = data.filter(d => d.count > 0);
    
    if (filteredData.length === 0) {
        ctx.parentElement.innerHTML = '<p style="text-align: center; color: #999;">No data available yet</p>';
        return;
    }
    
    topCLOsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: filteredData.map(d => `${d.id}: ${d.name}`),
            datasets: [{
                data: filteredData.map(d => d.count),
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(118, 75, 162, 0.8)',
                    'rgba(237, 100, 166, 0.8)',
                    'rgba(255, 154, 158, 0.8)',
                    'rgba(250, 208, 196, 0.8)',
                    'rgba(155, 207, 232, 0.8)',
                    'rgba(162, 210, 255, 0.8)',
                    'rgba(192, 192, 255, 0.8)',
                    'rgba(255, 192, 203, 0.8)',
                    'rgba(221, 160, 221, 0.8)'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 15,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

function createHeatmap(companies, clos) {
    const container = document.getElementById('heatmap-container');
    
    if (companies.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">No companies to display</p>';
        return;
    }
    
    let html = '<table class="heatmap-table"><thead><tr><th>Company</th>';
    
    clos.forEach(clo => {
        html += `<th>${clo.id}</th>`;
    });
    
    html += '</tr></thead><tbody>';
    
    companies.forEach(company => {
        html += `<tr><td class="company-name">${company.company_name}</td>`;
        
        clos.forEach(clo => {
            const isSelected = company.selected_clos.includes(clo.id);
            html += `<td><span class="heatmap-cell ${isSelected ? 'selected' : 'not-selected'}" title="${company.company_name} - ${clo.name}"></span></td>`;
        });
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    container.innerHTML = html;
}
