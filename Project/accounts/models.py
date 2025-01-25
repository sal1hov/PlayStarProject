from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Если у вас есть другие модели, специфичные для accounts, оставьте их здесь
# Например:
# class SomeOtherModel(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     ...

# Убедитесь, что модель Profile удалена из этого файла