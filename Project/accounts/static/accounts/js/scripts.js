// Общие функции для работы с модальными окнами
function openModal(id) {
    document.getElementById(id).classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
}

// Переключение видимости пароля
function togglePasswordVisibility(id) {
    const input = document.getElementById(id);
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
}

// Функция для показа уведомлений
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    // Форма добавления ребенка
    const addChildForm = document.getElementById('addChildForm');
    if (addChildForm) {
        addChildForm.addEventListener('submit', handleAddChildFormSubmit);
    }

    // Форма смены пароля
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', handleChangePasswordFormSubmit);
    }

    // Форма подтверждения Telegram
    const verifyTelegramForm = document.getElementById('verifyTelegramForm');
    if (verifyTelegramForm) {
        verifyTelegramForm.addEventListener('submit', handleVerifyTelegramFormSubmit);
    }

    // Формы удаления ребенка
    document.querySelectorAll('.delete-child-form').forEach(form => {
        form.addEventListener('submit', handleDeleteChildFormSubmit);
    });

    // Валидация полей формы
    setupFormValidation();
});

// Обработчики форм
function handleAddChildFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(this);

    fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Ошибка: ' + Object.values(data.errors).join('\n'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function handleChangePasswordFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(this);

    fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Ошибка: ' + Object.values(data.errors).join('\n'));
        }
    });
}

function handleVerifyTelegramFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(this);

    fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeModal('telegramModal');
            showToast(data.message || 'Telegram аккаунт успешно привязан!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast(data.error || 'Ошибка при привязке Telegram', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка', 'error');
    });
}

function handleDeleteChildFormSubmit(e) {
    e.preventDefault();
    if (confirm('Вы уверены, что хотите удалить этого ребенка?')) {
        const formData = new FormData(this);

        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });
    }
}

function setupFormValidation() {
    const firstNameField = document.getElementById('id_first_name');
    const lastNameField = document.getElementById('id_last_name');
    const phoneField = document.getElementById('id_phone_number');

    if (firstNameField) {
        firstNameField.addEventListener('input', function() {
            const regex = /^[A-Za-zА-Яа-яЁё]+$/;
            if (!regex.test(this.value) && this.value !== "") {
                this.setCustomValidity('Имя может содержать только буквы.');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    if (lastNameField) {
        lastNameField.addEventListener('input', function() {
            const regex = /^[A-Za-zА-Яа-яЁё]+$/;
            if (!regex.test(this.value) && this.value !== "") {
                this.setCustomValidity('Фамилия может содержать только буквы.');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    if (phoneField) {
        phoneField.addEventListener('input', function() {
            const regex = /^\+?\d+$/;
            if (!regex.test(this.value) && this.value !== "") {
                this.setCustomValidity('Номер телефона может содержать только цифры и символ "+" в начале.');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}