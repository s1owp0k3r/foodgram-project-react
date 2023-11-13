from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class Tag(models.Model):
    """Модель тега"""

    name = models.CharField(max_length=200, verbose_name='Название')
    color = models.CharField(max_length=7, null=True, verbose_name='Цвет')
    slug = models.SlugField(max_length=200, null=True, verbose_name='Слаг')

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента"""

    name = models.CharField(max_length=200, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта"""

    name = models.CharField(max_length=200, verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(1)]
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Фото'
    )
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ('-id',)

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """Связь рецептов с тегами"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tags',
        verbose_name='Рецепт',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Тег',
    )

    class Meta:
        verbose_name = "тег рецепта"
        verbose_name_plural = "Теги рецептов"


class RecipeIngredient(models.Model):
    """Связь рецептов с ингредиентами"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.IntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = "ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецептов"


class User(AbstractUser):
    """Модель пользователя"""

    username = models.CharField(
        max_length=150, unique=True, verbose_name='Никнейм'
    )
    email = models.EmailField(
        max_length=254, unique=True, verbose_name='Email'
    )
    first_name = models.CharField(
        max_length=150, blank=True, verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150, blank=True, verbose_name='Фамилия'
    )
    subscriptions = models.ManyToManyField(
        'User',
        through='UserSubscription',
        related_name='subscribers',
        verbose_name='Автор',
    )
    shopping_cart = models.ManyToManyField(
        Recipe,
        through='ShoppingCart',
        related_name='shopping_carts',
        verbose_name='Список покупок',
    )
    favorite = models.ManyToManyField(
        Recipe,
        through='Favorite',
        related_name='favorites',
        verbose_name='Избранное',
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
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscription'],
                name='unique_user_subscription'
            )
        ]


class UserRecipeCollection(models.Model):
    """Абстрактный класс для моделей списка покупок и избранного"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True


class ShoppingCart(UserRecipeCollection):
    """Списки покупок пользователей"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart_users',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart_user_recipe'
            )
        ]


class Favorite(UserRecipeCollection):
    """Избранное пользователей"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_users',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_user_recipe'
            )
        ]
