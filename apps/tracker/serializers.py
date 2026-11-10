"""Сериализаторы трекера задач."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Comment, Project, Tag, Task

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        source="members", queryset=User.objects.all(), many=True, write_only=True, required=False
    )
    tasks_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Project
        fields = (
            "id", "name", "description", "owner", "members", "member_ids",
            "tasks_count", "created_at", "updated_at",
        )


class MemberActionSerializer(serializers.Serializer):
    """Тело запроса для добавления или удаления участника."""

    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user")


class TagSerializer(serializers.ModelSerializer):
    color = serializers.RegexField(r"^#[0-9a-fA-F]{6}$", required=False)

    class Meta:
        model = Tag
        fields = ("id", "project", "name", "color")
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Tag.objects.all(), fields=("project", "name"),
                message="Тег с таким названием уже есть в проекте.",
            )
        ]

    def validate_project(self, project: Project) -> Project:
        # Создавать теги можно только в своих проектах
        if not project.has_member(self.context["request"].user):
            raise serializers.ValidationError("Вы не участник этого проекта.")
        return project


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "task", "author", "text", "created_at", "updated_at")

    def get_fields(self):
        fields = super().get_fields()
        # При редактировании комментарий нельзя «перенести» в другую задачу
        if self.instance is not None:
            fields["task"].read_only = True
        return fields

    def validate_task(self, task: Task) -> Task:
        if not task.project.has_member(self.context["request"].user):
            raise serializers.ValidationError("Вы не участник проекта этой задачи.")
        return task


class TaskSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee", queryset=User.objects.all(), write_only=True, required=False, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags", queryset=Tag.objects.all(), many=True, write_only=True, required=False
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    comments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Task
        fields = (
            "id", "project", "title", "description", "status", "status_display",
            "priority", "priority_display", "author", "assignee", "assignee_id",
            "tags", "tag_ids", "due_date", "comments_count", "created_at", "updated_at",
        )

    def get_fields(self):
        fields = super().get_fields()
        # Перенос задачи между проектами запрещён
        if self.instance is not None:
            fields["project"].read_only = True
        return fields

    def validate(self, attrs):
        user = self.context["request"].user
        project = attrs.get("project") or getattr(self.instance, "project", None)

        if not project.has_member(user):
            raise serializers.ValidationError({"project": "Вы не участник этого проекта."})

        assignee = attrs.get("assignee")
        if assignee is not None and not project.has_member(assignee):
            raise serializers.ValidationError({"assignee_id": "Исполнитель должен быть участником проекта."})

        tags = attrs.get("tags", [])
        if any(tag.project_id != project.id for tag in tags):
            raise serializers.ValidationError({"tag_ids": "Теги должны принадлежать проекту задачи."})
        return attrs


class TaskStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.Status.choices)
