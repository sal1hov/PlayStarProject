// main/static/main/js/notifications.js
function showNotification(type, message, duration = 5000) {
    const container = document.createElement('div');
    container.className = 'notification-container';

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                ${type === 'success' ? '✅' : '⚠️'}
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium">${message}</p>
            </div>
        </div>
    `;

    container.appendChild(notification);
    document.body.appendChild(container);

    setTimeout(() => {
        notification.classList.add('hide');
        setTimeout(() => container.remove(), 300);
    }, duration);
}