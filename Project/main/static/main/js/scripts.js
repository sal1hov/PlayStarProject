document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('tgModal');
    const openBtn = document.getElementById('tgLoginBtn');
    const closeBtn = document.getElementById('closeModal');
    const cancelBtn = document.getElementById('cancelBtn');
    const confirmBtn = document.getElementById('confirmBtn');
    const codeInput = document.getElementById('tgCode');

    // Функция открытия модального окна
    function openModal() {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        codeInput && codeInput.focus();
    }

    // Функция закрытия модального окна
    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    // Обработчики событий
    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    // Закрытие по клику вне окна
    modal.addEventListener('click', function(e) {
        if (e.target === modal) closeModal();
    });

    // Закрытие по ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });

    // Обработчик подтверждения кода
    if (confirmBtn && codeInput) {
        confirmBtn.addEventListener('click', async function() {
            const code = codeInput.value.trim();

            if (!/^\d{6}$/.test(code)) {
                alert('Пожалуйста, введите 6-значный цифровой код');
                codeInput.focus();
                return;
            }

            try {
                const response = await fetch('/accounts/telegram-login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ code: code })
                });

                const data = await response.json();
                if (data.success) {
                    window.location.href = data.redirect || '/';
                } else {
                    throw new Error(data.error || 'Неверный код подтверждения');
                }
            } catch (error) {
                console.error('Error:', error);
                alert(error.message);
                codeInput.focus();
            }
        });
    }

    // Вспомогательная функция для получения CSRF токена
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    // Для отладки
    window.debugModal = {
        open: openModal,
        close: closeModal
    };
});