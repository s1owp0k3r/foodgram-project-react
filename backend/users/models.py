from django.contrib.auth.models import AbstractUser
from django.db import models

import backend.constants as const


class User(AbstractUser):
    """Модель пользователя"""

    username = models.CharField(
        max_length=const.USER_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Никнейм'
    )
    email = models.EmailField(
        max_length=const.USER_EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Email'
    )
    first_name = models.CharField(
        max_length=const.USER_NAME_MAX_LENGTH,
        blank=True,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=const.USER_NAME_MAX_LENGTH,
        blank=True,
        verbose_name='Фамилия'
    )
    subscriptions = models.ManyToManyField(
        'User',
        through='UserSubscription',
        related_name='subscribers',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class UserSubscription(models.Model):
    """Подписки пользователей"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_subscriptions',
        verbose_name='Пользователь',
    )
    subscription = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_subscribers',
        verbose_name='Подписка',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscription'],
                name='unique_user_subscription'
            )
        ]
