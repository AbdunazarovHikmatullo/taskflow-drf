"""Регистрация и профиль текущего пользователя."""

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя. Доступна без авторизации."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


class MeView(generics.RetrieveAPIView):
    """Данные текущего пользователя."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """Список пользователей — нужен, чтобы находить людей для добавления в проект."""

    queryset = User.objects.filter(is_active=True).order_by("username")
    serializer_class = UserSerializer
    search_fields = ("username", "email", "first_name", "last_name")
