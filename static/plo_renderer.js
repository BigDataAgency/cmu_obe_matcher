// PLO Rendering Helper Functions for Groups → CLOs → PLOs Hierarchy

function createPLORenderer(data, ctxMap) {
    const mappedPlos = Array.isArray(data.mapped_plos) ? data.mapped_plos : [];
    const cloPlOMappings = Array.isArray(data.clo_plo_mappings) ? data.clo_plo_mappings : [];
    
    // Build a map: clo_id -> [plo_id1, plo_id2, ...]
    const cloToPloMap = new Map();
    cloPlOMappings.forEach(mapping => {
        const cloId = String(mapping.clo_id || '').trim();
        const ploId = String(mapping.plo_id || '').trim();
        if (!cloId || !ploId) return;
        
        if (!cloToPloMap.has(cloId)) {
            cloToPloMap.set(cloId, []);
        }
        cloToPloMap.get(cloId).push(ploId);
    });
    
    // Build a map: plo_id -> plo_object
    const ploById = new Map();
    mappedPlos.forEach(plo => {
        if (plo && plo.id) {
            ploById.set(String(plo.id), plo);
        }
    });
    
    return {
        renderPLOsForCLOs: function(cloIds, targetElement) {
            if (!targetElement) return;
            
            if (!cloIds || cloIds.length === 0) {
                targetElement.innerHTML = '<p style="color:#999; margin:0; font-size: 13px;">ไม่มี PLO (เลือก CLO ก่อน)</p>';
                return;
            }

            // Find PLOs mapped to selected CLOs using actual mapping data
            const ploIdsSet = new Set();
            cloIds.forEach(cloId => {
                const mappedPloIds = cloToPloMap.get(String(cloId));
                if (mappedPloIds) {
                    mappedPloIds.forEach(ploId => ploIdsSet.add(ploId));
                }
            });

            if (ploIdsSet.size === 0) {
                targetElement.innerHTML = '<p style="color:#999; margin:0; font-size: 13px;">ไม่พบ PLO ที่เชื่อมกับ CLO เหล่านี้</p>';
                return;
            }

            // Get PLO objects
            const relatedPlos = Array.from(ploIdsSet)
                .map(ploId => ploById.get(ploId))
                .filter(Boolean);

            if (relatedPlos.length === 0) {
                targetElement.innerHTML = '<p style="color:#999; margin:0; font-size: 13px;">ไม่พบข้อมูล PLO</p>';
                return;
            }

            // Sort by PLO level (1 = top level first) and then by ID
            relatedPlos.sort((a, b) => {
                const levelA = parseInt(a.plo_level) || 999;
                const levelB = parseInt(b.plo_level) || 999;
                if (levelA !== levelB) return levelA - levelB;
                return (a.id || '').localeCompare(b.id || '');
            });

            const ploHtml = relatedPlos.map(plo => {
                const ploName = escapeHtml(plo.name || plo.id);
                const ploDetail = escapeHtml((plo.detail || '').slice(0, 150));
                const ploLevel = plo.plo_level === '1' ? '🔵' : '🔸';
                const levelText = plo.plo_level === '1' ? 'PLO หลัก' : 'PLO ย่อย';
                
                return `<div class="plo-item">
                    <div class="plo-header">
                        ${ploLevel} <strong>${ploName}</strong> 
                        <span style="color:#666; font-size: 11px; margin-left: 6px;">(${escapeHtml(plo.id)} - ${levelText})</span>
                    </div>
                    <div class="plo-detail">${ploDetail}${(plo.detail || '').length > 150 ? '…' : ''}</div>
                </div>`;
            }).join('');

            targetElement.innerHTML = ploHtml;
        },
        
        getPLOStats: function(cloIds) {
            if (!cloIds || cloIds.length === 0) return { total: 0, topLevel: 0, subLevel: 0 };
            
            // Find PLOs mapped to selected CLOs
            const ploIdsSet = new Set();
            cloIds.forEach(cloId => {
                const mappedPloIds = cloToPloMap.get(String(cloId));
                if (mappedPloIds) {
                    mappedPloIds.forEach(ploId => ploIdsSet.add(ploId));
                }
            });
            
            const relatedPlos = Array.from(ploIdsSet)
                .map(ploId => ploById.get(ploId))
                .filter(Boolean);
            
            const topLevel = relatedPlos.filter(p => p.plo_level === '1').length;
            const subLevel = relatedPlos.filter(p => p.plo_level === '2').length;
            
            return {
                total: relatedPlos.length,
                topLevel: topLevel,
                subLevel: subLevel
            };
        }
    };
}

// Helper function to escape HTML (if not already defined)
if (typeof escapeHtml === 'undefined') {
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
