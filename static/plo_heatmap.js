// PLO Heatmap Function

async function createPLOHeatmap(companies) {
    const container = document.getElementById('plo-heatmap-container');
    
    if (!container) return;
    
    if (companies.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">ยังไม่มีบริษัทให้แสดง</p>';
        return;
    }
    
    // Collect all PLO IDs and mappings from companies
    const allPLOIds = new Set();
    const ploDetails = new Map(); // plo_id -> plo object
    
    companies.forEach(company => {
        if (company.mapped_plos && Array.isArray(company.mapped_plos)) {
            company.mapped_plos.forEach(plo => {
                if (plo && plo.id) {
                    allPLOIds.add(plo.id);
                    if (!ploDetails.has(plo.id)) {
                        ploDetails.set(plo.id, plo);
                    }
                }
            });
        }
    });
    
    if (allPLOIds.size === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">ยังไม่มี PLO ที่ถูก match</p>';
        return;
    }
    
    // Sort PLOs by level and ID
    const sortedPLOs = Array.from(ploDetails.values()).sort((a, b) => {
        const levelA = parseInt(a.plo_level) || 999;
        const levelB = parseInt(b.plo_level) || 999;
        if (levelA !== levelB) return levelA - levelB;
        return (a.id || '').localeCompare(b.id || '');
    });
    
    let html = '<table class="heatmap-table"><thead><tr><th>บริษัท</th><th>กลุ่ม</th>';
    
    // Header with PLO names, curriculum_id and descriptions
    sortedPLOs.forEach(plo => {
        const ploLevel = plo.plo_level === '1' ? '🔵' : '🔸';
        const levelText = plo.plo_level === '1' ? 'PLO หลัก' : 'PLO ย่อย';
        const name = plo.name || plo.id;
        const curriculumId = plo.curriculum_id || '-';
        const detail = (plo.detail || '').slice(0, 150);
        const tooltip = `${ploLevel} PLO: ${escapeHtml(name)}\nPLO ID: ${escapeHtml(plo.id)}\nCurriculum ID: ${curriculumId}\nLevel: ${levelText}\nDescription: ${escapeHtml(detail)}${detail.length >= 150 ? '...' : ''}`;
        const headerText = `${ploLevel} ${escapeHtml(name)}\n(${curriculumId})`;
        html += `<th title="${tooltip}" style="white-space: pre-line; font-size: 11px; line-height: 1.3;">${headerText}</th>`;
    });
    
    html += '</tr></thead><tbody>';
    
    // Build rows for each company/group
    companies.forEach(company => {
        const groups = company && Array.isArray(company.groups) ? company.groups : [];
        const cloPlOMappings = company.clo_plo_mappings || [];
        
        // Build map: group -> selected CLOs -> PLO IDs
        const groupToPLOs = new Map();
        
        if (!groups.length) {
            // No groups - use selected_clos
            const selected = Array.isArray(company.selected_clos) ? company.selected_clos : [];
            const ploIds = new Set();
            
            cloPlOMappings.forEach(mapping => {
                if (selected.includes(String(mapping.clo_id))) {
                    ploIds.add(String(mapping.plo_id));
                }
            });
            
            groupToPLOs.set('(ไม่มีการจัดกลุ่ม)', ploIds);
        } else {
            // Has groups
            groups.forEach(group => {
                const groupName = (group && group.group_name) ? group.group_name : (group && group.group_id) ? group.group_id : '';
                const selected = (group && Array.isArray(group.selected_clos)) ? group.selected_clos : [];
                const ploIds = new Set();
                
                cloPlOMappings.forEach(mapping => {
                    if (selected.includes(String(mapping.clo_id))) {
                        ploIds.add(String(mapping.plo_id));
                    }
                });
                
                groupToPLOs.set(groupName, ploIds);
            });
        }
        
        // Render rows
        const groupNames = Array.from(groupToPLOs.keys());
        const rowspan = groupNames.length;
        
        groupNames.forEach((groupName, idx) => {
            const ploIds = groupToPLOs.get(groupName);
            
            html += '<tr>';
            if (idx === 0) {
                html += `<td class="company-name" rowspan="${rowspan}">${escapeHtml(company.company_name || '')}</td>`;
            }
            html += `<td class="group-name">${escapeHtml(groupName)}</td>`;
            
            sortedPLOs.forEach(plo => {
                const isSelected = ploIds.has(plo.id);
                const ploLevel = plo.plo_level === '1' ? '🔵' : '🔸';
                const name = plo.name || plo.id;
                const detail = (plo.detail || '').slice(0, 100);
                const tooltip = `${escapeHtml(company.company_name || '')} - ${escapeHtml(groupName)}\n${ploLevel} ${escapeHtml(plo.id)}: ${escapeHtml(name)}\n${escapeHtml(detail)}`;
                html += `<td><span class="heatmap-cell ${isSelected ? 'selected' : 'not-selected'}" title="${tooltip}"></span></td>`;
            });
            
            html += '</tr>';
        });
    });
    
    html += '</tbody></table>';
    
    container.innerHTML = html;
}

// Helper function if not already defined
if (typeof escapeHtml === 'undefined') {
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
