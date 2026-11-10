"""Кастомные права доступа: владелец проекта и участники."""

from rest_framework import permissions

from .models import Comment, Project, Task


def _project_of(obj) -> Project:
    """Возвращает проект, к которому относится объект."""
    if isinstance(obj, Project):
        return obj
    if isinstance(obj, Comment):
        return obj.task.project
    return obj.project


class IsProjectOwner(permissions.BasePermission):
    """Изменять и удалять проект может только его владелец."""

    message = "Действие доступно только владельцу проекта."

    def has_object_permission(self, request, view, obj):
        return _project_of(obj).owner_id == request.user.id


class IsProjectMember(permissions.BasePermission):
    """Доступ к объекту есть у владельца проекта и его участников."""

    message = "Вы не являетесь участником этого проекта."

    def has_object_permission(self, request, view, obj):
        return _project_of(obj).has_member(request.user)


class IsOwnerOrProjectOwnerForDelete(permissions.BasePermission):
    """
    Для задач: читать и менять могут все участники,
    а удалять — только автор задачи или владелец проекта.
    """

    message = "Удалить задачу может только её автор или владелец проекта."

    def has_object_permission(self, request, view, obj: Task):
        if request.method != "DELETE":
            return True
        return obj.author_id == request.user.id or obj.project.owner_id == request.user.id


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Для комментариев: редактировать и удалять может только автор."""

    message = "Изменять комментарий может только его автор."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id
