from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        USER = 'USER', 'User'

    role = models.CharField(max_length=50, choices=Roles.choices, default=Roles.USER)

    def __str__(self):
        return f"{self.username} ({self.role})"
