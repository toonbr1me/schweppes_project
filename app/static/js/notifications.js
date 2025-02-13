class NotificationManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'notifications-container';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
        
        notification.innerHTML = `
            <div class="notification-icon">${icon}</div>
            <div class="notification-content">
                <div class="notification-title">${this.getTitle(type)}</div>
                <div class="notification-message">${message}</div>
            </div>
            <div class="notification-close">×</div>
            <div class="notification-progress">
                <div class="notification-progress-bar"></div>
            </div>
        `;

        this.container.appendChild(notification);

        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.close(notification);
        });

        setTimeout(() => this.close(notification), duration);
    }

    close(notification) {
        notification.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }

    getTitle(type) {
        switch(type) {
            case 'success': return 'Успешно';
            case 'error': return 'Ошибка';
            default: return 'Информация';
        }
    }
}

// Initialize notification manager
const notifications = new NotificationManager();

// Add to window for global access
window.showNotification = (message, type, duration) => {
    notifications.show(message, type, duration);
};
