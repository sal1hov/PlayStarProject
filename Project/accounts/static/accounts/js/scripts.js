// Скрипт для управления модальным окном в шаблоне profile_edit.html для добавления ребёнка
    function openModal() {
        document.getElementById('modal').classList.remove('hidden');
    }

    function closeModal() {
        document.getElementById('modal').classList.add('hidden');
    }

// скрипт для управления модальным окном в шаблоне profile_edit.html для смены пароля
    // Функции для открытия и закрытия модальных окон
    function openModal(modalId) {
        document.getElementById(modalId).classList.remove('hidden');
    }

    function closeModal(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    }


 // Функция для переключения видимости пароля в модальном окне для смены пароля
    function togglePasswordVisibility(inputId) {
        const input = document.getElementById(inputId);
        if (input.type === 'password') {
            input.type = 'text';
        } else {
            input.type = 'password';
        }
    }

// скрипт sweetalert2 на модальное окно на смену пароля
document.getElementById('changePasswordForm').addEventListener('submit', function (event) {
    event.preventDefault(); // Отменяем стандартную отправку формы

    const form = event.target;
    const formData = new FormData(form);
    const profileEditUrl = form.getAttribute('data-profile-edit-url'); // Получаем URL из атрибута

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken'), // Добавляем CSRF-токен
            'Accept': 'application/json', // Указываем, что ожидаем JSON-ответ
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка сети или сервера');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Успешная смена пароля
            Swal.fire({
                icon: 'success',
                title: 'Успех!',
                text: data.message,
            }).then(() => {
                window.location.href = profileEditUrl; // Используем URL из атрибута
            });
        } else {
            // Ошибка валидации
            Swal.fire({
                icon: 'error',
                title: 'Ошибка',
                text: data.message,
            });
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        Swal.fire({
            icon: 'error',
            title: 'Ошибка',
            text: 'Произошла ошибка при отправке формы.',
        });
    });
});

// AJAX

document.addEventListener('DOMContentLoaded', function() {
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
});
