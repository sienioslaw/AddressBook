from django.contrib.auth import get_user_model, logout
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError
from rest_framework.authtoken.models import Token
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response

from . import serializers
from .models import Address
from .utils import get_and_authenticate_user

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny, ]
    serializer_class = serializers.EmptySerializer
    serializer_classes = {
        'login': serializers.UserLoginSerializer,
    }

    @action(methods=['POST', ], detail=False)
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_and_authenticate_user(**serializer.validated_data)
        # if token already exist then remove before re-creating
        is_tokened = Token.objects.filter(user=user).first()
        if is_tokened:
            user.auth_token.delete()
        data = serializers.AuthUserSerializer(user).data
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['POST', ], detail=False, permission_classes=(IsAuthenticated, ))
    def logout(self, request):
        logout(request)
        Token.objects.filter(key=request.auth.key).delete()
        data = {'success': 'Sucessfully logged out'}
        return Response(data=data, status=status.HTTP_200_OK)

    def get_serializer_class(self):

        if not isinstance(self.serializer_classes, dict):
            raise ImproperlyConfigured("serializer_classes should be a dict mapping.")

        if self.action in self.serializer_classes.keys():
            return self.serializer_classes[self.action]
        return super().get_serializer_class()


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = serializers.AddressSerializer
    permission_classes = [IsAuthenticated]
    filter_fields = ["street", "city", "postcode", "country"]

    def get_queryset(self):
        query_set = self.queryset.filter(user=self.request.user)
        return query_set

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as exc:
            content = {'error': 'User already have this address'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['DELETE'], name='Delete multiple')
    def delete_multiple(self, request, *args, **kwargs):
        """
        ?ids=1,2,3,4

        """

        ids = self.request.query_params.get('ids', None)
        if ids:
            # Convert parameter string to list of integers
            ids = [ int(x) for x in ids.split(',') ]
            query_set = self.queryset.filter(user=self.request.user, pk__in=ids)
        else:
            query_set = self.queryset.filter(user=self.request.user)

        for entry in query_set:
            entry.delete()

        return Response({'success': 'deleted entries: %s' % ids}, status=status.HTTP_204_NO_CONTENT)
