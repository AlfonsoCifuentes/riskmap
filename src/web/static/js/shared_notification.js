// Shared notification utility
(function (global) {
    // Ensure Riskmap A.I. namespace exists
    global.RiskMapAI = global.RiskMapAI || {};

    function showNotification(message, type = 'info') {
        let t = (type || 'info').toLowerCase();
        // Normalize alternative type names
        if (t === 'danger') t = 'error';

        const notification = document.createElement('div');
            notification.className = 'notification notification-' + t;
        notification.innerHTML = 
            '<div class="notification-content">' +
                '<i class="fas fa-' + (t === 'success' ? 'check' : t === 'error' ? 'times' : t === 'warning' ? 'exclamation' : 'info') + '-circle"></i>' +
                '<span>' + message + '</span>' +
            '</div>';
            // Use CSS classes in `static/css/notification.css` for styling

        document.body.appendChild(notification);

            setTimeout(() => {
                notification.classList.add('show');
        }, 100);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Expose in a lightweight namespace but also offer backward compatible global helpers
    global.RiskMapAI.showNotification = showNotification;
    // Provide a global alias for old code
    global.showNotification = function(message, type) {
        return global.RiskMapAI.showNotification(message, type);
    };
    // Support old showAlert(type, message) pattern (type first)
    global.showAlert = function(type, message) {
        // Some legacy calls may pass (message, type) — detect and handle both patterns
        if (message === undefined && typeof type === 'string') {
            // No message passed — treat as info message
            return global.RiskMapAI.showNotification(type, 'info');
        }
        // For showAlert(type, message) -> map to showNotification(message, type)
        return global.RiskMapAI.showNotification(message, type);
    };
    
})(window);
