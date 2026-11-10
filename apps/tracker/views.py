"""ViewSet'ы трекера задач."""

from django.contrib.auth import get_user_model
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import TaskFilter
from .models import Comment, Project, Tag, Task
from .permissions import (
    IsAuthorOrReadOnly,
    IsOwnerOrProjectOwnerForDelete,
    IsProjectMember,
    IsProjectOwner,
)
from .serializers import (
    CommentSerializer,
    MemberActionSerializer,
    ProjectSerializer,
    TagSerializer,
    TaskSerializer,
    TaskStatusSerializer,
)

User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    """Проекты пользователя. Видны только проекты, где он владелец или участник."""

    serializer_class = ProjectSerializer
    search_fields = ("name", "description")
    ordering_fields = ("name", "created_at", "tasks_count")
    filterset_fields = ("owner",)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # генерация OpenAPI-схемы
            return Project.objects.none()
        return (
            Project.objects.for_user(self.request.user)
            .select_related("owner")
            .prefetch_related("members")
            .annotate(tasks_count=Count("tasks", distinct=True))
            .order_by("-created_at")
        )

    def get_permissions(self):
        perms = [permissions.IsAuthenticated()]
        if self.action in {"update", "partial_update", "destroy", "add_member", "remove_member"}:
            perms.append(IsProjectOwner())
        else:
            perms.append(IsProjectMember())
        return perms

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(request=MemberActionSerializer, responses=ProjectSerializer)
    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, pk=None):
        """Добавить участника в проект (только владелец)."""
        project = self.get_object()
        serializer = MemberActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project.members.add(serializer.validated_data["user"])
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(request=MemberActionSerializer, responses=ProjectSerializer)
    @action(detail=True, methods=["post"], url_path="remove-member")
    def remove_member(self, request, pk=None):
        """Убрать участника из проекта. Его задачи остаются без исполнителя."""
        project = self.get_object()
        serializer = MemberActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        project.members.remove(user)
        project.tasks.filter(assignee=user).update(assignee=None)
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(responses={200: {"type": "object", "additionalProperties": {"type": "integer"}}})
    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Статистика по задачам проекта: количество в каждом статусе."""
        project = self.get_object()
        counts = dict(project.tasks.values_list("status").annotate(c=Count("id")).values_list("status", "c"))
        data = {s.value: counts.get(s.value, 0) for s in Task.Status}
        data["total"] = sum(counts.values())
        return Response(data)


class TaskViewSet(viewsets.ModelViewSet):
    """Задачи из проектов пользователя с фильтрами, поиском и сортировкой."""

    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    search_fields = ("title", "description", "tags__name")
    ordering_fields = ("created_at", "updated_at", "due_date", "priority", "status", "title")
    permission_classes = [permissions.IsAuthenticated, IsProjectMember, IsOwnerOrProjectOwnerForDelete]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        projects = Project.objects.for_user(self.request.user)
        return (
            Task.objects.filter(project__in=projects)
            .select_related("project__owner", "author", "assignee")
            .prefetch_related("tags")
            .annotate(comments_count=Count("comments", distinct=True))
            .order_by("-created_at")
            .distinct()
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @extend_schema(request=TaskStatusSerializer, responses=TaskSerializer)
    @action(detail=True, methods=["post"], url_path="change-status")
    def change_status(self, request, pk=None):
        """Быстрая смена статуса задачи (например, для канбан-доски)."""
        task = self.get_object()
        serializer = TaskStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task.status = serializer.validated_data["status"]
        task.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(request=None, responses=TaskSerializer)
    @action(detail=True, methods=["post"], url_path="assign-to-me")
    def assign_to_me(self, request, pk=None):
        """Назначить задачу на себя."""
        task = self.get_object()
        task.assignee = request.user
        task.save(update_fields=["assignee", "updated_at"])
        return Response(self.get_serializer(self.get_object()).data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ModelViewSet):
    """Теги проектов."""

    serializer_class = TagSerializer
    filterset_fields = ("project",)
    search_fields = ("name",)
    ordering_fields = ("name",)
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Tag.objects.none()
        return Tag.objects.filter(project__in=Project.objects.for_user(self.request.user)).select_related("project")


class CommentViewSet(viewsets.ModelViewSet):
    """Комментарии к задачам. Фильтр по задаче: ?task=<id>."""

    serializer_class = CommentSerializer
    filterset_fields = ("task", "author")
    search_fields = ("text",)
    ordering_fields = ("created_at",)
    permission_classes = [permissions.IsAuthenticated, IsProjectMember, IsAuthorOrReadOnly]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Comment.objects.none()
        return (
            Comment.objects.filter(task__project__in=Project.objects.for_user(self.request.user))
            .select_related("author", "task__project")
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
