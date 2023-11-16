import io

from django.db.models import F, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import backend.constants as const
from backend.settings import BASE_DIR
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from users.models import User, UserSubscription

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
    serializer_class = RecipeWriteSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.recipes.favorite_and_shopping_cart(
            self.request.user
        ).select_related(
            'author'
        ).prefetch_related(
            'tags'
        ).prefetch_related(
            'ingredients'
        )


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


class UserCollectionCreateDeleteViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin
):

    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        if not (recipe := Recipe.objects.filter(pk=id).first()):
            return Response(
                {"errors": "Некорректный номер рецепта."},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
        if not (record := self._model.objects.filter(
            user=user, recipe=recipe
        )):
            return Response(
                {"errors": ERROR_MESSAGES[self._model]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartCreateDeleteViewSet(
    mixins.ListModelMixin,
    UserCollectionCreateDeleteViewSet
):

    _model = ShoppingCart
    _serializer = ShoppingCartWriteSerializer

    @action(detail=False, method=['get'])
    def shopping_cart_download(self, request):
        sc_ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount'))
        text = 'Список покупок:\n\n'
        for ingredient in sc_ingredients:
            text += (
                f'{ingredient["name"]} '
                f'({ingredient["measurement_unit"]}) - '
                f'{ingredient["amount"]}\n'
            )
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        font_dir = BASE_DIR / 'data/DejaVuSans.ttf'
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_dir))
        p.setFont('DejaVuSans', const.PDF_FONT_SIZE)
        textobject = p.beginText(2 * cm, 29.7 * cm - 2 * cm)
        for line in text.splitlines(False):
            textobject.textLine(line.rstrip())
        p.drawText(textobject)
        p.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename='shopping-list.pdf'
        )


class FavoriteCreateDeleteViewSet(UserCollectionCreateDeleteViewSet):

    _model = Favorite
    _serializer = FavoriteWriteSerializer
