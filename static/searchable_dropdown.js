// Searchable Dropdown Enhancement
// Converts a regular <select> into a searchable dropdown

function makeDropdownSearchable(selectElement) {
    if (!selectElement || selectElement.tagName !== 'SELECT') return;
    
    // Skip if already converted
    if (selectElement.dataset.searchable === 'true') return;
    selectElement.dataset.searchable = 'true';
    
    const wrapper = document.createElement('div');
    wrapper.className = 'searchable-dropdown-wrapper';
    wrapper.style.position = 'relative';
    wrapper.style.width = '100%';
    
    // Create search input
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'searchable-dropdown-input';
    searchInput.placeholder = 'พิมพ์เพื่อค้นหา CLO...';
    searchInput.style.cssText = `
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #ddd;
        border-radius: 6px;
        font-size: 13px;
        box-sizing: border-box;
    `;
    
    // Create dropdown list
    const dropdownList = document.createElement('div');
    dropdownList.className = 'searchable-dropdown-list';
    dropdownList.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        max-height: 300px;
        overflow-y: auto;
        background: white;
        border: 1px solid #ddd;
        border-radius: 6px;
        margin-top: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        display: none;
    `;
    
    // Store original options
    const options = Array.from(selectElement.options).filter(opt => opt.value);
    
    function renderOptions(filter = '') {
        dropdownList.innerHTML = '';
        const filterLower = filter.toLowerCase();
        
        const filtered = options.filter(opt => {
            const text = opt.textContent.toLowerCase();
            return text.includes(filterLower);
        });
        
        if (filtered.length === 0) {
            dropdownList.innerHTML = '<div style="padding: 12px; color: #999; text-align: center;">ไม่พบ CLO</div>';
            return;
        }
        
        filtered.forEach(opt => {
            const item = document.createElement('div');
            item.className = 'searchable-dropdown-item';
            item.textContent = opt.textContent;
            item.dataset.value = opt.value;
            item.style.cssText = `
                padding: 10px 12px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
                font-size: 13px;
                line-height: 1.4;
            `;
            
            item.addEventListener('mouseenter', () => {
                item.style.background = '#f5f5f5';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.background = 'white';
            });
            
            item.addEventListener('click', () => {
                selectElement.value = opt.value;
                searchInput.value = '';
                dropdownList.style.display = 'none';
                
                // Trigger change event
                const event = new Event('change', { bubbles: true });
                selectElement.dispatchEvent(event);
            });
            
            dropdownList.appendChild(item);
        });
    }
    
    // Event listeners
    searchInput.addEventListener('focus', () => {
        renderOptions(searchInput.value);
        dropdownList.style.display = 'block';
    });
    
    searchInput.addEventListener('input', () => {
        renderOptions(searchInput.value);
        dropdownList.style.display = 'block';
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
            dropdownList.style.display = 'none';
        }
    });
    
    // Replace select with wrapper
    selectElement.style.display = 'none';
    selectElement.parentNode.insertBefore(wrapper, selectElement);
    wrapper.appendChild(searchInput);
    wrapper.appendChild(dropdownList);
    wrapper.appendChild(selectElement);
}

// Auto-apply to all CLO picker dropdowns
function initSearchableDropdowns() {
    document.querySelectorAll('[data-role="clo-picker"]').forEach(select => {
        makeDropdownSearchable(select);
    });
}

// Re-apply when new dropdowns are added
const originalAppendChild = Element.prototype.appendChild;
Element.prototype.appendChild = function(child) {
    const result = originalAppendChild.call(this, child);
    if (child.nodeType === 1 && child.querySelector) {
        const pickers = child.querySelectorAll('[data-role="clo-picker"]');
        pickers.forEach(select => makeDropdownSearchable(select));
    }
    return result;
};
