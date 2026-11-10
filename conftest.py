"""Общие фикстуры pytest для API-тестов."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.tracker.models import Project, Tag, Task

User = get_user_model()


@pytest.fixture
def make_user(db):
    def _make(username: str) -> User:
        return User.objects.create_user(username=username, email=f"{username}@example.com", password="Str0ngPass!")
    return _make


@pytest.fixture
def owner(make_user):
    return make_user("owner")


@pytest.fixture
def member(make_user):
    return make_user("member")


@pytest.fixture
def stranger(make_user):
    return make_user("stranger")


@pytest.fixture
def api():
    """Возвращает функцию, создающую клиента, авторизованного как указанный пользователь."""
    def _client(user=None) -> APIClient:
        client = APIClient()
        if user is not None:
            client.force_authenticate(user)
        return client
    return _client


@pytest.fixture
def project(owner, member):
    project = Project.objects.create(name="Интернет-магазин", owner=owner)
    project.members.add(member)
    return project


@pytest.fixture
def tags(project):
    return [Tag.objects.create(project=project, name="backend"), Tag.objects.create(project=project, name="bug")]


@pytest.fixture
def tasks(project, owner, member, tags):
    t1 = Task.objects.create(project=project, title="Настроить CI", author=owner, priority=Task.Priority.HIGH,
                             due_date="2026-12-01")
    t2 = Task.objects.create(project=project, title="Исправить оплату", author=member, assignee=member,
                             status=Task.Status.IN_PROGRESS, priority=Task.Priority.CRITICAL, due_date="2026-11-20")
    t3 = Task.objects.create(project=project, title="Написать документацию", author=owner,
                             status=Task.Status.DONE, priority=Task.Priority.LOW, description="README и API")
    t1.tags.add(tags[0])
    t2.tags.add(tags[0], tags[1])
    return [t1, t2, t3]
