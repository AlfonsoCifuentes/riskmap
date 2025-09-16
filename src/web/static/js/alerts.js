
// Sistema de Alertas Frontend
class AlertsSystem {
    constructor() {
        this.alertsContainer = document.getElementById('alerts-container');
        this.alertsButton = document.getElementById('alerts-button');
        this.alertsBadge = document.getElementById('alerts-badge');
        
        this.initializeAlerts();
        this.startPolling();
    }
    
    async initializeAlerts() {
        try {
            const response = await fetch('/api/alerts/active');
            const data = await response.json();
            
            if (data.success) {
                this.displayAlerts(data.alerts);
                this.updateBadge(data.count);
            }
        } catch (error) {
            console.error('Error cargando alertas:', error);
        }
    }
    
    displayAlerts(alerts) {
        if (!this.alertsContainer) return;
        
        this.alertsContainer.innerHTML = '';
        
        if (alerts.length === 0) {
            this.alertsContainer.innerHTML = `
                <div class="alert-item no-alerts">
                    <i class="fas fa-check-circle text-success"></i>
                    <span>No hay alertas activas</span>
                </div>
            `;
            return;
        }
        
        alerts.forEach(alert => {
            const alertElement = this.createAlertElement(alert);
            this.alertsContainer.appendChild(alertElement);
        });
    }
    
    createAlertElement(alert) {
        const div = document.createElement('div');
        div.className = `alert-item severity-${alert.severity}`;
        div.dataset.alertId = alert.id;
        
        const severityIcons = {
            low: 'fa-info-circle text-info',
            medium: 'fa-exclamation-triangle text-warning',
            high: 'fa-exclamation-circle text-danger',
            critical: 'fa-skull-crossbones text-danger'
        };
        
        const icon = severityIcons[alert.severity] || 'fa-info-circle';
        
        div.innerHTML = `
            <div class="alert-header">
                <i class="fas ${icon}"></i>
                <span class="alert-title">${alert.title}</span>
                <button class="btn btn-sm btn-outline-secondary dismiss-alert" 
                        onclick="alertsSystem.dismissAlert('${alert.id}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="alert-body">
                <p>${alert.message}</p>
                <small class="text-muted">
                    <i class="fas fa-clock"></i> 
                    ${new Date(alert.created_at).toLocaleString()}
                </small>
            </div>
        `;
        
        return div;
    }
    
    async dismissAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/dismiss`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Remover elemento del DOM
                const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
                if (alertElement) {
                    alertElement.remove();
                }
                
                // Actualizar contador
                this.updateBadgeCount(-1);
                
                // Mostrar notificación
                this.showNotification('Alerta descartada', 'success');
            }
        } catch (error) {
            console.error('Error descartando alerta:', error);
            this.showNotification('Error descartando alerta', 'error');
        }
    }
    
    updateBadge(count) {
        if (this.alertsBadge) {
            this.alertsBadge.textContent = count;
            this.alertsBadge.style.display = count > 0 ? 'inline' : 'none';
        }
    }
    
    updateBadgeCount(delta) {
        if (this.alertsBadge) {
            const currentCount = parseInt(this.alertsBadge.textContent) || 0;
            const newCount = Math.max(0, currentCount + delta);
            this.updateBadge(newCount);
        }
    }
    
    startPolling() {
        // Polling cada 30 segundos para nuevas alertas
        setInterval(() => {
            this.initializeAlerts();
        }, 30000);
    }
    
    showNotification(message, type = 'info') {
        // Crear notificación toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-body">
                <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i>
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remover después de 3 segundos
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Inicializar sistema de alertas cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.alertsSystem = new AlertsSystem();
});
            