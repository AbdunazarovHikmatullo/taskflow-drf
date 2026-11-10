"""Сериализаторы пользователей и регистрации."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Публичное представление пользователя (без пароля)."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name")
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value.lower()

    def validate(self, attrs):
        # Проверяем пароль стандартными валидаторами Django
        validate_password(attrs["password"], user=User(username=attrs.get("username"), email=attrs.get("email")))
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
