from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    FavoriteCreateDeleteView, IngredientViewSet, MySubscriptionsView,
    ShoppingCartCreateDeleteView, shopping_cart_download,
    SubscriptionCreateDeleteView, RecipeViewSet, TagViewSet
)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path(
        'users/subscriptions/', MySubscriptionsView.as_view({'get': 'list'})
    ),
    re_path(
        r'^users/(?P<id>\d+)/subscribe/',
        SubscriptionCreateDeleteView.as_view()
    ),
    path(
        'recipes/download_shopping_cart/', shopping_cart_download
    ),
    re_path(
        r'^recipes/(?P<id>\d+)/shopping_cart/',
        ShoppingCartCreateDeleteView.as_view()
    ),
    re_path(
        r'^recipes/(?P<id>\d+)/favorite/',
        FavoriteCreateDeleteView.as_view()
    ),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
