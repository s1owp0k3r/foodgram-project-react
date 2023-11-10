from django_filters import CharFilter, NumberFilter
from django_filters.filters import ModelMultipleChoiceFilter
from django_filters.rest_framework import FilterSet

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтр для рецептов"""

    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )
    is_favorited = NumberFilter(
        field_name='favorites__id', method='filter_in'
    )
    is_in_shopping_cart = NumberFilter(
        field_name='shopping_carts__id', method='filter_in'
    )

    def filter_in(self, queryset, name, value):
        if value == 0:
            return queryset
        lookup = '__'.join([name, 'exact'])
        return queryset.filter(**{lookup: self.request.user.id})

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')


class IngredientFilter(FilterSet):
    """Фильтр для ингредиентов"""

    name = CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
