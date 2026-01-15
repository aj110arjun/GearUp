/**
 * Dashboard analytics and interaction logic.
 */

document.addEventListener('DOMContentLoaded', function () {
    const config = window.DASHBOARD_CONFIG || {};
    
    // Check if we have sales data
    const hasSalesData = (config.salesData && config.salesData.length > 0);
    
    if (hasSalesData) {
        // Prepare chart data
        const labels = config.salesData.map(day => day.date);
        const series = [config.salesData.map(day => day.sales || 0)];
        
        // Chart options
        const options = {
            showArea: true,
            showLine: true,
            showPoint: true,
            fullWidth: true,
            axisX: {
                showGrid: true,
                showLabel: true,
                offset: 30
            },
            axisY: {
                showGrid: true,
                showLabel: true,
                onlyInteger: false,
                scaleMinSpace: 40,
                labelInterpolationFnc: function(value) {
                    if (value >= 1000000) {
                        return '₹' + (value / 1000000).toFixed(1) + 'M';
                    } else if (value >= 1000) {
                        return '₹' + (value / 1000).toFixed(0) + 'k';
                    }
                    return '₹' + value;
                }
            },
            chartPadding: {
                top: 20,
                right: 20,
                bottom: 30,
                left: 40
            },
            low: 0
        };
        
        // Create chart
        if (typeof Chartist !== 'undefined') {
            new Chartist.Line('#sales-chart', {
                labels: labels,
                series: series
            }, options);
            
            // Add SVG gradient for area fill
            addChartGradient();
        }
    }
    
    function addChartGradient() {
        const chartContainer = document.querySelector('#sales-chart');
        if (!chartContainer) return;
        const svg = chartContainer.querySelector('svg');
        if (svg) {
            const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
            gradient.setAttribute('id', 'gradient');
            gradient.setAttribute('x1', '0%');
            gradient.setAttribute('y1', '0%');
            gradient.setAttribute('x2', '0%');
            gradient.setAttribute('y2', '100%');
            
            const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop1.setAttribute('offset', '0%');
            stop1.setAttribute('stop-color', '#3b82f6');
            stop1.setAttribute('stop-opacity', '0.5');
            
            const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop2.setAttribute('offset', '100%');
            stop2.setAttribute('stop-color', '#3b82f6');
            stop2.setAttribute('stop-opacity', '0');
            
            gradient.appendChild(stop1);
            gradient.appendChild(stop2);
            defs.appendChild(gradient);
            svg.insertBefore(defs, svg.firstChild);
        }
    }
    
    // Auto-submit filter form
    const filterSelect = document.querySelector('select[name="filter"]');
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            this.form.submit();
        });
    }

    // Custom Report Form Validation
    const reportForm = document.getElementById('customReportForm');
    if (reportForm) {
        reportForm.addEventListener('submit', function(e) {
            const startDateInput = document.getElementById('startDate');
            const endDateInput = document.getElementById('endDate');
            
            if (!startDateInput || !endDateInput) return;

            const startDate = new Date(startDateInput.value);
            const endDate = new Date(endDateInput.value);
            const today = new Date();
            today.setHours(23, 59, 59, 999); // Allow today

            // 1. Check if dates are in the future
            if (startDate > today) {
                e.preventDefault();
                window.showSnackbar('Start date cannot be in the future', 'error');
                return;
            }

            if (endDate > today) {
                e.preventDefault();
                window.showSnackbar('End date cannot be in the future', 'error');
                return;
            }

            // 2. Check if start date is after end date
            if (startDate > endDate) {
                e.preventDefault();
                window.showSnackbar('Start date must be before or equal to end date', 'error');
                return;
            }
        });
    }
});

// Report Modal Functions (Globally accessible)
window.openReportModal = function() {
    const modal = document.getElementById('reportModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
};

window.closeReportModal = function() {
    const modal = document.getElementById('reportModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
};

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('reportModal');
    if (event.target == modal) {
        window.closeReportModal();
    }
};
