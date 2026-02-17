// Patch to add PLO rendering to both displayGroupedAnalysisResults and renderModalGroupedEditor
// This script should be loaded after app.js

(function() {
    // Store original functions
    const originalDisplayGrouped = window.displayGroupedAnalysisResults;
    const originalRenderModal = window.renderModalGroupedEditor;
    
    // Patch displayGroupedAnalysisResults
    if (typeof originalDisplayGrouped === 'function') {
        window.displayGroupedAnalysisResults = function(data) {
            // Call original function
            originalDisplayGrouped(data);
            
            // Apply searchable dropdowns and PLO rendering
            setTimeout(() => {
                const groupsEditor = document.getElementById('groups-editor');
                if (!groupsEditor) return;
                
                const ctxMap = buildCLOContextMap(data);
                const ploRenderer = createPLORenderer(data, ctxMap);
                
                groupsEditor.querySelectorAll('.group-card').forEach(card => {
                    const picker = card.querySelector('[data-role="clo-picker"]');
                    const selectedWrap = card.querySelector('[data-role="group-selected"]');
                    const ploWrap = card.querySelector('[data-role="group-plos"]');
                    
                    if (!picker || !selectedWrap || !ploWrap) return;
                    
                    // Make dropdown searchable
                    if (typeof makeDropdownSearchable === 'function') {
                        makeDropdownSearchable(picker);
                    }
                    
                    // Patch the renderSelectedChips function for this card
                    const addBtn = card.querySelector('[data-role="clo-add"]');
                    if (addBtn) {
                        const originalClickHandler = addBtn.onclick;
                        addBtn.onclick = null;
                        
                        addBtn.addEventListener('click', function() {
                            // Wait for chips to render
                            setTimeout(() => {
                                const selectedIds = Array.from(selectedWrap.querySelectorAll('.clo-chip'))
                                    .map(chip => chip.dataset.cloId)
                                    .filter(Boolean);
                                
                                if (ploRenderer && typeof ploRenderer.renderPLOsForCLOs === 'function') {
                                    ploRenderer.renderPLOsForCLOs(selectedIds, ploWrap);
                                }
                            }, 50);
                        });
                    }
                    
                    // Patch remove button clicks
                    selectedWrap.addEventListener('click', function(e) {
                        if (e.target.dataset.role === 'remove') {
                            setTimeout(() => {
                                const selectedIds = Array.from(selectedWrap.querySelectorAll('.clo-chip'))
                                    .map(chip => chip.dataset.cloId)
                                    .filter(Boolean);
                                
                                if (ploRenderer && typeof ploRenderer.renderPLOsForCLOs === 'function') {
                                    ploRenderer.renderPLOsForCLOs(selectedIds, ploWrap);
                                }
                            }, 50);
                        }
                    });
                    
                    // Initial render
                    const selectedIds = Array.from(selectedWrap.querySelectorAll('.clo-chip'))
                        .map(chip => chip.dataset.cloId)
                        .filter(Boolean);
                    
                    if (ploRenderer && typeof ploRenderer.renderPLOsForCLOs === 'function') {
                        ploRenderer.renderPLOsForCLOs(selectedIds, ploWrap);
                    }
                });
            }, 100);
        };
    }
    
    // Patch renderModalGroupedEditor
    if (typeof originalRenderModal === 'function') {
        window.renderModalGroupedEditor = function(company) {
            // Call original function
            originalRenderModal(company);
            
            // Apply searchable dropdowns and PLO rendering
            setTimeout(() => {
                const groupsEditor = document.getElementById('modal-groups-editor');
                if (!groupsEditor) return;
                
                const ctxMap = buildCLOContextMap(company);
                const ploRenderer = createPLORenderer(company, ctxMap);
                
                groupsEditor.querySelectorAll('.group-card').forEach(card => {
                    const picker = card.querySelector('[data-role="clo-picker"]');
                    const selectedWrap = card.querySelector('[data-role="group-selected"]');
                    const ploWrap = card.querySelector('[data-role="group-plos"]');
                    
                    if (!picker || !selectedWrap || !ploWrap) return;
                    
                    // Make dropdown searchable
                    if (typeof makeDropdownSearchable === 'function') {
                        makeDropdownSearchable(picker);
                    }
                    
                    // Patch the renderSelectedChips function for this card
                    const addBtn = card.querySelector('[data-role="clo-add"]');
                    if (addBtn) {
                        addBtn.addEventListener('click', function() {
                            setTimeout(() => {
                                const selectedIds = Array.from(selectedWrap.querySelectorAll('.clo-chip'))
                                    .map(chip => chip.dataset.cloId)
                                    .filter(Boolean);
                                
                                if (ploRenderer && typeof ploRenderer.renderPLOsForCLOs === 'function') {
                                    ploRenderer.renderPLOsForCLOs(selectedIds, ploWrap);
                                }
                            }, 50);
                        });
                    }
                    
                    // Patch remove button clicks
                    selectedWrap.addEventListener('click', function(e) {
                        if (e.target.dataset.role === 'remove') {
                            setTimeout(() => {
                                const selectedIds = Array.from(selectedWrap.querySelectorAll('.clo-chip'))
                                    .map(chip => chip.dataset.cloId)
                                    .filter(Boolean);
                                
                                if (ploRenderer && typeof ploRenderer.renderPLOsForCLOs === 'function') {
                                    ploRenderer.renderPLOsForCLOs(selectedIds, ploWrap);
                                }
                            }, 50);
                        }
                    });
                    
                    // Initial render
                    const selectedIds = Array.from(selectedWrap.querySelectorAll('.clo-chip'))
                        .map(chip => chip.dataset.cloId)
                        .filter(Boolean);
                    
                    if (ploRenderer && typeof ploRenderer.renderPLOsForCLOs === 'function') {
                        ploRenderer.renderPLOsForCLOs(selectedIds, ploWrap);
                    }
                });
            }, 100);
        };
    }
})();
