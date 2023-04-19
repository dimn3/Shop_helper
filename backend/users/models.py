from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'admin'),
    )

    username = models.CharField(
        'Никнейм',
        max_length=150,
        blank=True,
        unique=True
    )
    email = models.EmailField(
        'Почта',
        max_length=254,
        blank=True,
        unique=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=True
        )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=True
        )
    password = models.CharField(
        'Пароль',
        max_length=150,
        blank=True
        )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )

    USERNAME_FIELDS = 'email',
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return str(self.username)
