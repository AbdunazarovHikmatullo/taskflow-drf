"""Проверка, что страницы Django Admin открываются."""

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("url", ["/admin/tracker/project/", "/admin/tracker/task/",
                                 "/admin/tracker/tag/", "/admin/tracker/comment/"])
def test_admin_changelists(client, tasks, url):
    admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "AdminPass123")
    client.force_login(admin)
    assert client.get(url).status_code == 200
