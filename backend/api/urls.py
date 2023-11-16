from django.urls import include, path, re_path

from rest_framework.routers import DefaultRouter

from .views import (
    FavoriteCreateDeleteViewSet,
    IngredientViewSet,
    MySubscriptionsView,
    RecipeViewSet,
    ShoppingCartCreateDeleteViewSet,
    SubscriptionCreateDeleteView,
    TagViewSet
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
        'recipes/download_shopping_cart/',
        ShoppingCartCreateDeleteViewSet.as_view(
            {'get': 'shopping_cart_download'}
        )
    ),
    re_path(
        r'^recipes/(?P<id>\d+)/shopping_cart/',
        ShoppingCartCreateDeleteViewSet.as_view(
            {'post': 'post', 'delete': 'delete'}
        )
    ),
    re_path(
        r'^recipes/(?P<id>\d+)/favorite/',
        FavoriteCreateDeleteViewSet.as_view(
            {'post': 'post', 'delete': 'delete'}
        )
    ),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
