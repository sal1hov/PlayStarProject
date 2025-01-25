// Функция для показа/скрытия пароля
function togglePasswordVisibility(fieldId) {
    const passwordField = document.getElementById(fieldId);
    if (passwordField.type === "password") {
        passwordField.type = "text";
    } else {
        passwordField.type = "password";
    }
}

// Функция для проверки, содержит ли строка только буквы и пробелы
function validateName(input) {
    const regex = /^[A-Za-zА-Яа-я\s]+$/;
    return regex.test(input);
}

// Функция для проверки, содержит ли строка только цифры
function validateNumber(input) {
    const regex = /^\d+$/;
    return regex.test(input);
}

// Функция для проверки номера телефона в формате +7XXXXXXXXXX
function validatePhoneNumber(input) {
    const regex = /^\+7\d{10}$/;
    return regex.test(input);
}

// Функция для отображения уведомления с использованием SweetAlert2
function showNotification(message) {
    Swal.fire({
        icon: 'error',  // Тип иконки
        title: 'Ошибка',  // Заголовок уведомления
        text: message,  // Текст уведомления
        confirmButtonText: 'OK',  // Текст кнопки
        confirmButtonColor: '#3b82f6',  // Цвет кнопки (синий)
    });
}

// Валидация полей при отправке формы
document.querySelector('form').addEventListener('submit', function (event) {
    const firstName = document.getElementById('id_first_name').value;
    const lastName = document.getElementById('id_last_name').value;
    const childName = document.getElementById('id_child_name').value;
    const childAge = document.getElementById('id_child_age').value;
    const phoneNumber = document.getElementById('id_phone_number').value;

    // Валидация имени
    if (!validateName(firstName)) {
        showNotification('Имя может содержать только буквы и пробелы.');
        event.preventDefault();
        return;
    }

    // Валидация фамилии
    if (!validateName(lastName)) {
        showNotification('Фамилия может содержать только буквы и пробелы.');
        event.preventDefault();
        return;
    }

    // Валидация имени ребёнка
    if (!validateName(childName)) {
        showNotification('Имя ребёнка может содержать только буквы и пробелы.');
        event.preventDefault();
        return;
    }

    // Валидация возраста ребёнка
    if (!validateNumber(childAge)) {
        showNotification('Возраст ребёнка может содержать только цифры.');
        event.preventDefault();
        return;
    }

    // Валидация номера телефона
    if (!validatePhoneNumber(phoneNumber)) {
        showNotification('Номер телефона должен быть в формате +7XXXXXXXXXX.');
        event.preventDefault();
        return;
    }
});

// Валидация в реальном времени для имени, фамилии и имени ребёнка
document.getElementById('id_first_name').addEventListener('input', function () {
    if (!validateName(this.value)) {
        this.setCustomValidity('Имя может содержать только буквы и пробелы.');
    } else {
        this.setCustomValidity('');
    }
});

document.getElementById('id_last_name').addEventListener('input', function () {
    if (!validateName(this.value)) {
        this.setCustomValidity('Фамилия может содержать только буквы и пробелы.');
    } else {
        this.setCustomValidity('');
    }
});

document.getElementById('id_child_name').addEventListener('input', function () {
    if (!validateName(this.value)) {
        this.setCustomValidity('Имя ребёнка может содержать только буквы и пробелы.');
    } else {
        this.setCustomValidity('');
    }
});

// Валидация в реальном времени для возраста ребёнка
document.getElementById('id_child_age').addEventListener('input', function () {
    if (!validateNumber(this.value)) {
        this.setCustomValidity('Возраст ребёнка может содержать только цифры.');
    } else {
        this.setCustomValidity('');
    }
});

// Валидация в реальном времени для номера телефона
document.getElementById('id_phone_number').addEventListener('input', function () {
    if (!validatePhoneNumber(this.value)) {
        this.setCustomValidity('Номер телефона должен быть в формате +7XXXXXXXXXX.');
    } else {
        this.setCustomValidity('');
    }
});