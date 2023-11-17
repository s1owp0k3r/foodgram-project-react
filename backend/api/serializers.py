import base64
import os
from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

import backend.constants as const
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    ShoppingCart,
    Tag
)
from users.models import User, UserSubscription

ERROR_MESSAGES = {
    ShoppingCart: 'Этот рецепт уже добавлен в список покупок.',
    Favorite: 'Этот рецепт уже добавлен в избранное.'
}


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = str(uuid4())[:12] + '.' + ext
            data = ContentFile(base64.b64decode(imgstr), name=filename)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=const.USER_EMAIL_MAX_LENGTH,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=const.USER_NAME_MAX_LENGTH,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    first_name = serializers.CharField(
        max_length=const.USER_NAME_MAX_LENGTH,
        required=True
    )
    last_name = serializers.CharField(
        max_length=const.USER_NAME_MAX_LENGTH,
        required=True
    )
    password = serializers.CharField(
        max_length=const.USER_NAME_MAX_LENGTH,
        write_only=True,
        required=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        validated_data['password'] = make_password(
            validated_data.get('password')
        )
        return super().create(validated_data)

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        return (
            current_user.is_authenticated
            and UserSubscription.objects.filter(
                user=current_user, subscription=obj
            ).exists()
        )


class UserCreateSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class SubscriptionReadSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
        )

    def get_recipes(self, obj):
        recipes_limit = self.context['recipes_limit']
        if recipes_limit:
            recipes_limit = int(recipes_limit)
        return RecipeSubscriptionSerializer(
            obj.recipes.all()[:recipes_limit],
            many=True
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()


class SubscriptionWriteSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = UserSubscription
        fields = '__all__'
        read_only_fields = ('id',)

    def validate(self, data):
        user = data['user']
        subscription = data['subscription']
        if self.context['request'].method == 'POST':
            if user == subscription:
                raise serializers.ValidationError(
                    {"errors": "Вы не можете подписаться на самого себя."}
                )
            if UserSubscription.objects.filter(
                user=user, subscription=subscription
            ).exists():
                raise serializers.ValidationError(
                    {"errors": "Вы уже подписаны на этого пользователя."}
                )
        return data

    def create(self, validated_data):
        return UserSubscription.objects.create(
            user=validated_data['user'],
            subscription=validated_data['subscription']
        )

    def to_representation(self, data):
        return SubscriptionReadSerializer(
            context=self.context
        ).to_representation(data)


class UserCollectionReadSerializer(serializers.ModelSerializer):

    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class UserCollectionWriteSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        abstract = True
        fields = '__all__'
        read_only_fields = ('id',)

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if self.context['request'].method == 'POST':
            if self.Meta.model.objects.filter(
                user=user, recipe=recipe
            ).exists():
                raise serializers.ValidationError(
                    {
                        "errors": ERROR_MESSAGES[self.Meta.model]
                    }
                )
        return data


class ShoppingCartWriteSerializer(UserCollectionWriteSerializer):

    class Meta(UserCollectionWriteSerializer.Meta):
        model = ShoppingCart


class FavoriteWriteSerializer(UserCollectionWriteSerializer):

    class Meta(UserCollectionWriteSerializer.Meta):
        model = Favorite


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeTagSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        source='tag.id',
        read_only=True
    )
    name = serializers.StringRelatedField(
        source='tag.name',
        read_only=True
    )
    color = serializers.StringRelatedField(
        source='tag.color',
        read_only=True
    )
    slug = serializers.StringRelatedField(
        source='tag.slug',
        read_only=True
    )

    class Meta:
        model = RecipeTag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):

    name = serializers.StringRelatedField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeIngredientReadSerializer(RecipeIngredientSerializer):

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        read_only=True
    )


class RecipeIngredientWriteSerializer(RecipeIngredientSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )


class RecipeSerializer(serializers.ModelSerializer):

    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeReadSerializer(RecipeSerializer):
    author = UserSerializer(read_only=True)
    tags = RecipeTagSerializer(source='recipe_tags', many=True)
    ingredients = RecipeIngredientReadSerializer(many=True)


class RecipeWriteSerializer(RecipeSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    name = serializers.CharField(max_length=const.NAME_MAX_LENGTH)
    cooking_time = serializers.IntegerField(
        min_value=const.COOKING_TIME_MIN_VALUE
    )

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Укажите теги для рецепта.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Уберите повторяющиеся теги.')
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Укажите ингредиенты для рецепта.'
            )
        ingredient_ids = [ingredient['id'] for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Уберите повторяющиеся ингредиенты.'
            )
        if [
            amount for ingredient in value if (
                amount := ingredient['amount']
            ) <= const.AMOUNT_MIN_VALUE
        ]:
            raise serializers.ValidationError(
                'Некорректное количество ингредиента.'
            )
        return value

    @staticmethod
    def create_or_update(user, validated_data, recipe=None):
        validated_data['author'] = user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        if recipe:
            if os.path.exists(recipe.image.path):
                os.remove(recipe.image.path)
            new_image = validated_data.pop('image')
            Recipe.objects.filter(id=recipe.id).update(**validated_data)
            recipe = Recipe.objects.get(id=recipe.id)
            recipe.image = new_image
            recipe.save()
            RecipeIngredient.objects.filter(recipe=recipe).delete()
            RecipeTag.objects.filter(recipe=recipe).delete()
        else:
            recipe = Recipe.objects.create(**validated_data)

        recipe_ingredients = [RecipeIngredient(
            ingredient=ingredient['id'],
            recipe=recipe,
            amount=ingredient['amount']
        ) for ingredient in ingredients]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        recipe_tags = [RecipeTag(
            tag=tag, recipe=recipe
        ) for tag in tags]
        RecipeTag.objects.bulk_create(recipe_tags)

        return recipe

    def create(self, validated_data):
        return self.create_or_update(
            self.context.get('request').user, validated_data
        )

    def update(self, instance, validated_data):
        return self.create_or_update(
            self.context.get('request').user, validated_data, instance
        )

    def to_representation(self, data):
        return RecipeReadSerializer(
            Recipe.objects.favorite_and_shopping_cart(
                self.context.get('request').user.id
            ).get(id=data.id),
            context=self.context
        ).data


class RecipeSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
