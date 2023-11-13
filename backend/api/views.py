from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    UserSubscription
)

from .filters import IngredientFilter, RecipeFilter
from .mixins import PatchModelMixin
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    ERROR_MESSAGES,
    FavoriteWriteSerializer,
    IngredientSerializer,
    RecipeWriteSerializer,
    ShoppingCartWriteSerializer,
    SubscriptionReadSerializer,
    SubscriptionWriteSerializer,
    TagSerializer,
    UserCollectionReadSerializer
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PatchModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Recipe.objects.all()
    serializer_class = RecipeWriteSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class MySubscriptionsView(
    viewsets.GenericViewSet,
    mixins.ListModelMixin
):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionReadSerializer

    def get_queryset(self):
        return self.request.user.subscriptions.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipes_limit'] = self.request.GET.get('recipes_limit')
        return context


class SubscriptionCreateDeleteView(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        recipes_limit = request.query_params.get('recipes_limit')
        subscribed_user = get_object_or_404(User, pk=id)
        serializer = SubscriptionWriteSerializer(
            context={'request': request, 'recipes_limit': recipes_limit},
            data={
                'user': self.request.user.id,
                'subscription': subscribed_user.id,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionReadSerializer(
                subscribed_user,
                context={'request': request, 'recipes_limit': recipes_limit}
            ).data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, id):
        current_user = self.request.user
        subscribed_user = get_object_or_404(User, pk=id)
        subscription = UserSubscription.objects.filter(
            user=current_user, subscription=subscribed_user
        )
        if not subscription:
            return Response(
                {"errors": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def shopping_cart_download(request):
    sc_ingredients = QuerySet(RecipeIngredient)
    for recipe in request.user.shopping_cart.all():
        sc_ingredients |= RecipeIngredient.objects.filter(recipe=recipe)
    sc_ingredients = sc_ingredients.values(
        name=F('ingredient__name'),
        measurement_unit=F('ingredient__measurement_unit')
    ).annotate(amount=Sum('amount'))
    text_file = ''
    for ingredient in sc_ingredients:
        text_file += (
            f'{ingredient["name"]} '
            f'({ingredient["measurement_unit"]}) - {ingredient["amount"]}\n'
        )
    response = HttpResponse(
        text_file,
        content_type='text/plain',
        status=status.HTTP_200_OK
    )
    return response


class UserCollectionCreateDeleteView(APIView):

    permission_classes = (IsAuthenticated,)

    class Meta:
        abstract = True

    def post(self, request, id):
        if not Recipe.objects.filter(pk=id).exists():
            return Response(
                {"errors": "Некорректный номер рецепта."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe = Recipe.objects.get(pk=id)
        serializer = self._serializer(
            context={'request': request},
            data={
                'user': self.request.user.id,
                'recipe': recipe.id,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            UserCollectionReadSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=id)
        record = self._model.objects.filter(
            user=user, recipe=recipe
        )
        if not record:
            return Response(
                {"errors": ERROR_MESSAGES[self._model]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartCreateDeleteView(UserCollectionCreateDeleteView):

    _model = ShoppingCart
    _serializer = ShoppingCartWriteSerializer


class FavoriteCreateDeleteView(UserCollectionCreateDeleteView):

    _model = Favorite
    _serializer = FavoriteWriteSerializer
