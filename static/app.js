const API_BASE = '/api/v1';

let allCLOs = [];
let currentAnalysis = null;
let currentCompanyName = null;
let currentAnalysisMode = 'simple';

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(`${tabName}-tab`).classList.add('active');

    const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn =>
        btn.dataset && btn.dataset.tab === tabName
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

function renderDashboardGroupsTable(companies, clos) {
    const container = document.getElementById('dashboard-groups-table');
    if (!container) return;

    const cloNameById = new Map((clos || []).map(c => [c.id, c.name]));

    if (!companies || companies.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#999; margin: 0;">ยังไม่มีข้อมูล</p>';
        return;
    }

    const rowsHtml = companies.map(company => {
        const groups = company && Array.isArray(company.groups) ? company.groups : [];

        if (!groups.length) {
            const selected = Array.isArray(company.selected_clos) ? company.selected_clos : [];
            const tags = selected.map(id => {
                const name = cloNameById.get(id);
                return `<span class="dashboard-clo-chip">${escapeHtml(id)}${name ? `: ${escapeHtml(name)}` : ''}</span>`;
            }).join('');

            return `
                <tr>
                    <td class="dashboard-company">${escapeHtml(company.company_name || '')}</td>
                    <td class="dashboard-groups">
                        <div class="dashboard-muted">(ไม่มีการจัดกลุ่ม)</div>
                    </td>
                    <td class="dashboard-clos">
                        <div class="dashboard-chips">${tags || '<span class="dashboard-muted">ยังไม่ได้เลือก CLO</span>'}</div>
                    </td>
                </tr>
            `;
        }

        const groupsHtml = groups.map(g => {
            const groupName = (g && g.group_name) ? g.group_name : (g && g.group_id) ? g.group_id : '';
            const selected = (g && Array.isArray(g.selected_clos)) ? g.selected_clos : [];

            const chips = selected.map(id => {
                const name = cloNameById.get(id);
                return `<span class="dashboard-clo-chip">${escapeHtml(id)}${name ? `: ${escapeHtml(name)}` : ''}</span>`;
            }).join('');

            return `
                <div class="dashboard-group-block">
                    <div class="dashboard-group-title">${escapeHtml(groupName)}</div>
                    <div class="dashboard-chips">${chips || '<span class="dashboard-muted">ยังไม่ได้เลือก CLO</span>'}</div>
                </div>
            `;
        }).join('');

        return `
            <tr>
                <td class="dashboard-company">${escapeHtml(company.company_name || '')}</td>
                <td class="dashboard-groups" colspan="2">${groupsHtml}</td>
            </tr>
        `;
    }).join('');

    container.innerHTML = `
        <div class="dashboard-table-wrap">
            <table class="dashboard-table">
                <thead>
                    <tr>
                        <th style="width: 24%;">ชื่อบริษัท</th>
                        <th>กลุ่ม และ CLO ของแต่ละกลุ่ม</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        </div>
    `;
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

        alert('สร้างบริษัทตัวอย่างเรียบร้อยแล้ว!');
    } catch (error) {
        alert(`เกิดข้อผิดพลาดในการสร้างข้อมูลตัวอย่าง: ${error.message}`);
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

    const modeInput = document.querySelector('input[name="analysis-mode"]:checked');
    currentAnalysisMode = modeInput ? modeInput.value : 'simple';
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = '🔄 กำลังวิเคราะห์...';
    
    try {
        const endpoint = currentAnalysisMode === 'grouped' ? 'analyze-company-grouped' : 'analyze-company';
        const response = await fetch(`${API_BASE}/${endpoint}`, {
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
            throw new Error(error.detail || 'วิเคราะห์บริษัทไม่สำเร็จ');
        }
        
        const data = await response.json();
        currentAnalysis = data;
        if (currentAnalysisMode === 'grouped') {
            displayGroupedAnalysisResults(data);
        } else {
            displayAnalysisResults(data);
        }
        
    } catch (error) {
        alert(`เกิดข้อผิดพลาด: ${error.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '🔍 วิเคราะห์ด้วย AI';
    }
});

function displayAnalysisResults(data) {
    const resultSection = document.getElementById('analysis-result');
    const companyInfo = document.getElementById('company-info');
    const aiReasoning = document.getElementById('ai-reasoning');
    const cloSelection = document.getElementById('clo-selection');

    const simpleSection = document.getElementById('simple-analysis');
    const groupedSection = document.getElementById('grouped-analysis');
    if (simpleSection) simpleSection.style.display = 'block';
    if (groupedSection) groupedSection.style.display = 'none';
    
    companyInfo.innerHTML = `
        <h4>${data.company_name}</h4>
        <p><strong>คุณสมบัติ/ความต้องการ:</strong> ${data.requirements}</p>
        ${data.culture ? `<p><strong>วัฒนธรรมองค์กร:</strong> ${data.culture}</p>` : ''}
        ${data.desired_traits ? `<p><strong>ลักษณะ/ทักษะที่ต้องการ:</strong> ${data.desired_traits}</p>` : ''}
    `;
    
    aiReasoning.innerHTML = `
        <strong>เหตุผลจาก AI:</strong>
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

function displayGroupedAnalysisResults(data) {
    const resultSection = document.getElementById('analysis-result');
    const companyInfo = document.getElementById('company-info');
    const aiReasoning = document.getElementById('ai-reasoning');
    const groupsEditor = document.getElementById('groups-editor');
    const unionSummary = document.getElementById('union-clos-summary');

    const simpleSection = document.getElementById('simple-analysis');
    const groupedSection = document.getElementById('grouped-analysis');
    if (simpleSection) simpleSection.style.display = 'none';
    if (groupedSection) groupedSection.style.display = 'block';

    companyInfo.innerHTML = `
        <h4>${data.company_name}</h4>
        <p><strong>คุณสมบัติ/ความต้องการ:</strong> ${data.requirements}</p>
        ${data.culture ? `<p><strong>วัฒนธรรมองค์กร:</strong> ${data.culture}</p>` : ''}
        ${data.desired_traits ? `<p><strong>ลักษณะ/ทักษะที่ต้องการ:</strong> ${data.desired_traits}</p>` : ''}
    `;

    aiReasoning.innerHTML = `
        <strong>เหตุผลจาก AI:</strong>
        <p>ผลลัพธ์นี้ถูกจัดกลุ่มเป็นธีม คุณสามารถเปลี่ยนชื่อกลุ่ม และเลือก/ยกเลิก CLO แยกตามกลุ่มได้</p>
    `;

    if (groupsEditor) {
        groupsEditor.innerHTML = '';
    }

    const groups = Array.isArray(data.groups) ? data.groups : [];
    groups.forEach(group => {
        const card = document.createElement('div');
        card.className = 'group-card';
        card.dataset.groupId = group.group_id;

        const evidence = Array.isArray(group.evidence) ? group.evidence : [];
        const evidenceHtml = evidence.map(e => `<span class="evidence-chip">${escapeHtml(e)}</span>`).join('');

        card.innerHTML = `
            <div class="group-card-header">
                <input class="group-name-input" type="text" value="${escapeHtml(group.group_name)}" data-role="group-name" />
            </div>
            <p style="margin: 0 0 8px; color: #666;">${escapeHtml(group.summary || '')}</p>
            ${evidenceHtml ? `<div class="evidence-chips">${evidenceHtml}</div>` : ''}
            <div class="clo-grid" data-role="group-clos"></div>
        `;

        const cloGrid = card.querySelector('[data-role="group-clos"]');
        const selected = new Set(Array.isArray(group.selected_clos) ? group.selected_clos : []);

        allCLOs.forEach(clo => {
            const cloItem = document.createElement('div');
            const isChecked = selected.has(clo.id);
            cloItem.className = `clo-item ${isChecked ? 'selected' : ''}`;
            cloItem.innerHTML = `
                <div class="clo-item-header">
                    <input type="checkbox" data-role="group-clo" data-clo-id="${clo.id}" ${isChecked ? 'checked' : ''}>
                    <span class="clo-item-id">${clo.id}</span>
                    <span class="clo-item-name">${escapeHtml(clo.name)}</span>
                </div>
                <div class="clo-item-desc">${escapeHtml(clo.description)}</div>
            `;

            cloItem.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox') {
                    const checkbox = cloItem.querySelector('input[type="checkbox"]');
                    checkbox.checked = !checkbox.checked;
                }
                cloItem.classList.toggle('selected');
                updateUnionSummary();
            });

            cloGrid.appendChild(cloItem);
        });

        card.querySelector('[data-role="group-name"]').addEventListener('input', () => {
            updateUnionSummary();
        });

        if (groupsEditor) {
            groupsEditor.appendChild(card);
        }
    });

    updateUnionSummary();

    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });

    function updateUnionSummary() {
        if (!unionSummary) return;
        const selected = getGroupedSelectedCLOs();
        if (selected.length === 0) {
            unionSummary.innerHTML = '<p style="color:#666; margin:0;">ยังไม่ได้เลือก CLO</p>';
            return;
        }

        const tags = selected.map(id => {
            const clo = allCLOs.find(c => c.id === id);
            const label = clo ? `${id}: ${clo.name}` : id;
            return `<span class="union-tag">${escapeHtml(label)}</span>`;
        }).join('');
        unionSummary.innerHTML = `<div class="union-tags">${tags}</div>`;
    }
}

function getGroupedSelectedCLOs() {
    const groupsEditor = document.getElementById('groups-editor');
    if (!groupsEditor) return [];
    const seen = new Set();
    const out = [];
    groupsEditor.querySelectorAll('.group-card').forEach(card => {
        card.querySelectorAll('input[data-role="group-clo"]:checked').forEach(cb => {
            const id = cb.dataset.cloId;
            if (id && !seen.has(id)) {
                seen.add(id);
                out.push(id);
            }
        });
    });
    return out;
}

function buildGroupsPayloadFromUI() {
    const groupsEditor = document.getElementById('groups-editor');
    const baseGroups = currentAnalysis && Array.isArray(currentAnalysis.groups) ? currentAnalysis.groups : [];
    if (!groupsEditor || baseGroups.length === 0) return [];

    const groupsById = new Map(baseGroups.map(g => [g.group_id, g]));
    const payloadGroups = [];

    groupsEditor.querySelectorAll('.group-card').forEach(card => {
        const groupId = card.dataset.groupId;
        const base = groupsById.get(groupId);
        if (!base) return;

        const nameInput = card.querySelector('input[data-role="group-name"]');
        const groupName = nameInput ? nameInput.value.trim() : base.group_name;

        const selectedClos = Array.from(card.querySelectorAll('input[data-role="group-clo"]:checked'))
            .map(cb => cb.dataset.cloId)
            .filter(Boolean);

        payloadGroups.push({
            group_id: base.group_id,
            group_name: groupName || base.group_name,
            summary: base.summary || '',
            evidence: Array.isArray(base.evidence) ? base.evidence : [],
            suggested_clos: Array.isArray(base.suggested_clos) ? base.suggested_clos : [],
            selected_clos: selectedClos,
            reasoning: base.reasoning || ''
        });
    });

    return payloadGroups;
}

function escapeHtml(str) {
    return String(str)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

async function saveCompany() {
    try {
        if (currentAnalysisMode === 'grouped') {
            const groups = buildGroupsPayloadFromUI();
            if (groups.length === 0) {
                alert('ไม่พบกลุ่มสำหรับบันทึก กรุณากดวิเคราะห์ใหม่อีกครั้ง');
                return;
            }

            const unionSelected = getGroupedSelectedCLOs();
            if (unionSelected.length === 0) {
                alert('กรุณาเลือก CLO อย่างน้อย 1 รายการ');
                return;
            }

            const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(currentAnalysis.company_name)}/groups`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    groups: groups
                })
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || 'บันทึกกลุ่มของบริษัทไม่สำเร็จ');
            }
        } else {
            const selectedCLOs = Array.from(document.querySelectorAll('#clo-selection input[type="checkbox"]:checked'))
                .map(cb => cb.id.replace('clo-', ''));

            if (selectedCLOs.length === 0) {
                alert('กรุณาเลือก CLO อย่างน้อย 1 รายการ');
                return;
            }

            const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(currentAnalysis.company_name)}/clos`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    selected_clos: selectedCLOs
                })
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || 'บันทึกบริษัทไม่สำเร็จ');
            }
        }
        
        alert('บันทึกบริษัทเรียบร้อยแล้ว!');
        resetForm();
        showTab('companies');
        
    } catch (error) {
        alert(`เกิดข้อผิดพลาด: ${error.message}`);
    }
}

function resetForm() {
    document.getElementById('company-form').reset();
    document.getElementById('analysis-result').style.display = 'none';
    currentAnalysis = null;
    currentAnalysisMode = 'simple';
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
                    <div class="empty-state-text">ยังไม่มีบริษัทในระบบ ลองเพิ่มบริษัทแรกของคุณได้เลย</div>
                </div>
            `;
            return;
        }
        
        data.companies.forEach(company => {
            const companyCard = document.createElement('div');
            companyCard.className = 'company-card';
            
            const cloTags = company.selected_clos.map(cloId => {
                const clo = allCLOs.find(c => c.id === cloId);
                return `<span class="clo-tag">${cloId}: ${clo ? clo.name : 'ไม่ทราบชื่อ'}</span>`;
            }).join('');
            
            companyCard.innerHTML = `
                <h3>${company.company_name}</h3>
                <div class="company-card-details">
                    <p><strong>คุณสมบัติ/ความต้องการ:</strong> ${company.requirements.substring(0, 150)}${company.requirements.length > 150 ? '...' : ''}</p>
                    ${company.culture ? `<p><strong>วัฒนธรรมองค์กร:</strong> ${company.culture.substring(0, 100)}${company.culture.length > 100 ? '...' : ''}</p>` : ''}
                    <p><strong>CLO ที่เลือก (${company.selected_clos.length}):</strong></p>
                    <div class="clo-tags">${cloTags}</div>
                </div>
                <div class="company-actions">
                    <button class="btn-primary" onclick="viewCompanyDetail('${company.company_name}')">ดู/แก้ไข</button>
                </div>
            `;
            
            companiesList.appendChild(companyCard);
        });
        
    } catch (error) {
        loadingDiv.style.display = 'none';
        companiesList.innerHTML = `<p style="color: red;">เกิดข้อผิดพลาดในการโหลดรายชื่อบริษัท: ${error.message}</p>`;
    }
}

async function viewCompanyDetail(companyName) {
    try {
        const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(companyName)}`);
        const company = await response.json();
        
        currentCompanyName = companyName;
        
        document.getElementById('modal-company-name').textContent = company.company_name;
        document.getElementById('modal-company-details').innerHTML = `
            <p><strong>คุณสมบัติ/ความต้องการ:</strong> ${company.requirements}</p>
            ${company.culture ? `<p><strong>วัฒนธรรมองค์กร:</strong> ${company.culture}</p>` : ''}
            ${company.desired_traits ? `<p><strong>ลักษณะ/ทักษะที่ต้องการ:</strong> ${company.desired_traits}</p>` : ''}
            <p><strong>เหตุผลจาก AI:</strong> ${company.ai_reasoning}</p>
        `;
        
        if (allCLOs.length === 0) {
            await loadCLOs();
        }

        const modalSimpleEditor = document.getElementById('modal-simple-editor');
        const modalGroupedEditor = document.getElementById('modal-grouped-editor');

        if (company.groups && Array.isArray(company.groups) && company.groups.length > 0) {
            if (modalSimpleEditor) modalSimpleEditor.style.display = 'none';
            if (modalGroupedEditor) modalGroupedEditor.style.display = 'block';
            renderModalGroupedEditor(company);
        } else {
            if (modalSimpleEditor) modalSimpleEditor.style.display = 'block';
            if (modalGroupedEditor) modalGroupedEditor.style.display = 'none';

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
                        <span class="clo-item-name">${escapeHtml(clo.name)}</span>
                    </div>
                    <div class="clo-item-desc">${escapeHtml(clo.description)}</div>
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
        }
        
        document.getElementById('company-detail-modal').classList.add('active');
        
    } catch (error) {
        alert(`เกิดข้อผิดพลาดในการโหลดรายละเอียดบริษัท: ${error.message}`);
    }
}

function renderModalGroupedEditor(company) {
    const groupsEditor = document.getElementById('modal-groups-editor');
    const unionSummary = document.getElementById('modal-union-clos-summary');
    if (!groupsEditor || !unionSummary) return;

    groupsEditor.innerHTML = '';

    const groups = Array.isArray(company.groups) ? company.groups : [];
    groups.forEach(group => {
        const card = document.createElement('div');
        card.className = 'group-card';
        card.dataset.groupId = group.group_id;

        const evidence = Array.isArray(group.evidence) ? group.evidence : [];
        const evidenceHtml = evidence.map(e => `<span class="evidence-chip">${escapeHtml(e)}</span>`).join('');

        card.innerHTML = `
            <div class="group-card-header">
                <input class="group-name-input" type="text" value="${escapeHtml(group.group_name)}" data-role="group-name" />
            </div>
            <p style="margin: 0 0 8px; color: #666;">${escapeHtml(group.summary || '')}</p>
            ${evidenceHtml ? `<div class="evidence-chips">${evidenceHtml}</div>` : ''}
            <div class="clo-grid" data-role="group-clos"></div>
        `;

        const cloGrid = card.querySelector('[data-role="group-clos"]');
        const selected = new Set(Array.isArray(group.selected_clos) ? group.selected_clos : []);

        allCLOs.forEach(clo => {
            const cloItem = document.createElement('div');
            const isChecked = selected.has(clo.id);
            cloItem.className = `clo-item ${isChecked ? 'selected' : ''}`;
            cloItem.innerHTML = `
                <div class="clo-item-header">
                    <input type="checkbox" data-role="group-clo" data-clo-id="${clo.id}" ${isChecked ? 'checked' : ''}>
                    <span class="clo-item-id">${clo.id}</span>
                    <span class="clo-item-name">${escapeHtml(clo.name)}</span>
                </div>
                <div class="clo-item-desc">${escapeHtml(clo.description)}</div>
            `;

            cloItem.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox') {
                    const checkbox = cloItem.querySelector('input[type="checkbox"]');
                    checkbox.checked = !checkbox.checked;
                }
                cloItem.classList.toggle('selected');
                updateUnionSummary();
            });

            cloGrid.appendChild(cloItem);
        });

        card.querySelector('[data-role="group-name"]').addEventListener('input', () => {
            updateUnionSummary();
        });

        groupsEditor.appendChild(card);
    });

    updateUnionSummary();

    function updateUnionSummary() {
        const selected = getModalGroupedSelectedCLOs();
        if (selected.length === 0) {
            unionSummary.innerHTML = '<p style="color:#666; margin:0;">ยังไม่ได้เลือก CLO</p>';
            return;
        }

        const tags = selected.map(id => {
            const clo = allCLOs.find(c => c.id === id);
            const label = clo ? `${id}: ${clo.name}` : id;
            return `<span class="union-tag">${escapeHtml(label)}</span>`;
        }).join('');
        unionSummary.innerHTML = `<div class="union-tags">${tags}</div>`;
    }
}

function getModalGroupedSelectedCLOs() {
    const groupsEditor = document.getElementById('modal-groups-editor');
    if (!groupsEditor) return [];
    const seen = new Set();
    const out = [];
    groupsEditor.querySelectorAll('.group-card').forEach(card => {
        card.querySelectorAll('input[data-role="group-clo"]:checked').forEach(cb => {
            const id = cb.dataset.cloId;
            if (id && !seen.has(id)) {
                seen.add(id);
                out.push(id);
            }
        });
    });
    return out;
}

function buildModalGroupsPayloadFromUI(company) {
    const groupsEditor = document.getElementById('modal-groups-editor');
    const baseGroups = company && Array.isArray(company.groups) ? company.groups : [];
    if (!groupsEditor || baseGroups.length === 0) return [];

    const groupsById = new Map(baseGroups.map(g => [g.group_id, g]));
    const payloadGroups = [];

    groupsEditor.querySelectorAll('.group-card').forEach(card => {
        const groupId = card.dataset.groupId;
        const base = groupsById.get(groupId);
        if (!base) return;

        const nameInput = card.querySelector('input[data-role="group-name"]');
        const groupName = nameInput ? nameInput.value.trim() : base.group_name;

        const selectedClos = Array.from(card.querySelectorAll('input[data-role="group-clo"]:checked'))
            .map(cb => cb.dataset.cloId)
            .filter(Boolean);

        payloadGroups.push({
            group_id: base.group_id,
            group_name: groupName || base.group_name,
            summary: base.summary || '',
            evidence: Array.isArray(base.evidence) ? base.evidence : [],
            suggested_clos: Array.isArray(base.suggested_clos) ? base.suggested_clos : [],
            selected_clos: selectedClos,
            reasoning: base.reasoning || ''
        });
    });

    return payloadGroups;
}

async function updateCompanyCLOs() {
    try {
        const responseCompany = await fetch(`${API_BASE}/companies/${encodeURIComponent(currentCompanyName)}`);
        if (!responseCompany.ok) {
            const text = await responseCompany.text();
            throw new Error(text || 'โหลดข้อมูลบริษัทเพื่ออัปเดตไม่สำเร็จ');
        }
        const company = await responseCompany.json();

        if (company.groups && Array.isArray(company.groups) && company.groups.length > 0) {
            const groups = buildModalGroupsPayloadFromUI(company);
            const unionSelected = getModalGroupedSelectedCLOs();
            if (unionSelected.length === 0) {
                alert('กรุณาเลือก CLO อย่างน้อย 1 รายการ');
                return;
            }

            const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(currentCompanyName)}/groups`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    groups: groups
                })
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || 'อัปเดตกลุ่มของบริษัทไม่สำเร็จ');
            }
        } else {
            const selectedCLOs = Array.from(document.querySelectorAll('#modal-clo-selection input[type="checkbox"]:checked'))
                .map(cb => cb.id.replace('modal-clo-', ''));

            if (selectedCLOs.length === 0) {
                alert('กรุณาเลือก CLO อย่างน้อย 1 รายการ');
                return;
            }

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
                const text = await response.text();
                throw new Error(text || 'อัปเดต CLO ของบริษัทไม่สำเร็จ');
            }
        }
        
        alert('อัปเดต CLO ของบริษัทเรียบร้อยแล้ว!');
        closeModal();
        loadCompanies();
        
    } catch (error) {
        alert(`เกิดข้อผิดพลาด: ${error.message}`);
    }
}

async function deleteCompany() {
    if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการลบบริษัท ${currentCompanyName}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(currentCompanyName)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('ลบบริษัทไม่สำเร็จ');
        }
        
        alert('ลบบริษัทเรียบร้อยแล้ว!');
        closeModal();
        loadCompanies();
        
    } catch (error) {
        alert(`เกิดข้อผิดพลาด: ${error.message}`);
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
        closReference.innerHTML = `<p style="color: red;">เกิดข้อผิดพลาดในการโหลดรายการ CLO: ${error.message}</p>`;
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

            const groupsTable = document.getElementById('dashboard-groups-table');
            if (groupsTable) {
                groupsTable.innerHTML = '';
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

        // Create grouped summary table
        renderDashboardGroupsTable(companies, clos);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        const emptyState = document.getElementById('dashboard-empty');
        if (emptyState) {
            emptyState.style.display = 'block';
            emptyState.querySelector('.empty-state-text').textContent = `เกิดข้อผิดพลาดในการโหลดแดชบอร์ด: ${error.message}`;
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
                label: 'จำนวนบริษัท',
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
        ctx.parentElement.innerHTML = '<p style="text-align: center; color: #999;">ยังไม่มีข้อมูล</p>';
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
        container.innerHTML = '<p style="text-align: center; color: #999;">ยังไม่มีบริษัทให้แสดง</p>';
        return;
    }
    
    let html = '<table class="heatmap-table"><thead><tr><th>บริษัท</th>';
    
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
