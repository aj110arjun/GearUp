/**
 * Modern Admin Product List logic for GearUp.
 * Handles search cleaning, mobile toggles, and auto-submission.
 */

(function() {
    function initFilters() {
        const input = document.getElementById('search-input');
        const clearBtn = document.getElementById('clear-btn');
        const filterForm = document.getElementById('filter-form');
        const filterToggle = document.getElementById('filter-toggle');
        
        if (!filterForm) return;

        // Search Input Handlers
        if (input && clearBtn) {
            const toggleClearBtn = () => {
                if (input.value) {
                    clearBtn.classList.remove('hidden');
                    clearBtn.classList.add('flex');
                } else {
                    clearBtn.classList.add('hidden');
                    clearBtn.classList.remove('flex');
                }
            };
            
            input.addEventListener('input', toggleClearBtn);
            
            clearBtn.addEventListener('click', () => {
                input.value = '';
                toggleClearBtn();
                filterForm.submit();
            });
            
            toggleClearBtn();
        }

        // Mobile Filter Toggle
        if (filterToggle) {
            filterToggle.addEventListener('click', () => {
                filterForm.classList.toggle('hidden');
                // When revealed, it should use the grid layout
                if (!filterForm.classList.contains('hidden')) {
                    filterForm.classList.add('grid');
                }
            });
        }

        // Auto-submit on Select Change
        const filterSelects = filterForm.querySelectorAll('select');
        filterSelects.forEach(select => {
            select.addEventListener('change', () => {
                // Show a subtle loading state
                select.classList.add('opacity-50', 'pointer-events-none');
                filterForm.submit();
            });
        });

        // Row interaction enrichment
        const tableRows = document.querySelectorAll('tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                row.classList.add('bg-blue-50', 'bg-opacity-30');
            });
            row.addEventListener('mouseleave', () => {
                row.classList.remove('bg-blue-50', 'bg-opacity-30');
            });
        });
    }

    // Graceful initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFilters);
    } else {
        initFilters();
    }
})();
