from django.core.validators import MinValueValidator
from django.db import models

import backend.constants as const
from users.models import User


class Tag(models.Model):
    """Модель тега"""

    name = models.CharField(
        max_length=const.NAME_MAX_LENGTH, verbose_name='Название'
    )
    color = models.CharField(
        max_length=const.COLOR_MAX_LENGTH, null=True, verbose_name='Цвет'
    )
    slug = models.SlugField(
        max_length=const.NAME_MAX_LENGTH, null=True, verbose_name='Слаг'
    )

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "Теги"
        ordering = ('id',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента"""

    name = models.CharField(
        max_length=const.NAME_MAX_LENGTH, verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=const.NAME_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_mu'
            )
        ]

    def __str__(self):
        return self.name


class RecipeQuerySet(models.QuerySet):
    def favorite_and_shopping_cart(self, user_id=None):
        user_favorite = Favorite.objects.filter(
            recipe=models.OuterRef('pk'),
            user__id=user_id
        )
        user_shopping_cart = ShoppingCart.objects.filter(
            recipe=models.OuterRef('pk'),
            user__id=user_id
        )
        return self.annotate(
            is_favorited=models.Exists(user_favorite),
            is_in_shopping_cart=models.Exists(user_shopping_cart)
        )


class Recipe(models.Model):
    """Модель рецепта"""

    name = models.CharField(
        max_length=const.NAME_MAX_LENGTH, verbose_name='Название'
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(const.COOKING_TIME_MIN_VALUE)]
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Фото'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги',
    )
    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ('-id',)

    def __str__(self):
        return self.name


class UserRecipeCollection(models.Model):
    """Абстрактный класс для моделей списка покупок и избранного"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    class Meta:
        default_related_name = '%(class)s'
        abstract = True
        ordering = ('id',)


class ShoppingCart(UserRecipeCollection):
    """Списки покупок пользователей"""

    class Meta(UserRecipeCollection.Meta):
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

    class Meta(UserRecipeCollection.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_user_recipe'
            )
        ]


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
        ordering = ('id',)


class RecipeIngredient(models.Model):
    """Связь рецептов с ингредиентами"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Ингредиент',
    )
    amount = models.IntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = "ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецептов"
        ordering = ('id',)
