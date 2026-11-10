"""Проекты: видимость, права владельца, участники, статистика."""

import pytest

from apps.tracker.models import Project

pytestmark = pytest.mark.django_db


def test_create_project_sets_owner(api, owner, member):
    resp = api(owner).post("/api/projects/", {"name": "CRM", "member_ids": [member.id]}, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["owner"]["username"] == "owner"
    assert [m["username"] for m in body["members"]] == ["member"]


def test_projects_visible_only_to_participants(api, project, owner, member, stranger):
    assert api(owner).get("/api/projects/").json()["count"] == 1
    assert api(member).get("/api/projects/").json()["count"] == 1
    assert api(stranger).get("/api/projects/").json()["count"] == 0
    assert api(stranger).get(f"/api/projects/{project.id}/").status_code == 404


def test_only_owner_can_update_and_delete(api, project, owner, member):
    url = f"/api/projects/{project.id}/"
    assert api(member).patch(url, {"name": "Взлом"}, format="json").status_code == 403
    assert api(member).delete(url).status_code == 403

    resp = api(owner).patch(url, {"name": "Магазин 2.0"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Магазин 2.0"
    assert api(owner).delete(url).status_code == 204
    assert not Project.objects.exists()


def test_add_and_remove_member(api, project, owner, member, stranger, tasks):
    url = f"/api/projects/{project.id}"
    # Участник не может управлять составом
    assert api(member).post(f"{url}/add-member/", {"user_id": stranger.id}, format="json").status_code == 403

    resp = api(owner).post(f"{url}/add-member/", {"user_id": stranger.id}, format="json")
    assert resp.status_code == 200
    assert {m["username"] for m in resp.json()["members"]} == {"member", "stranger"}

    resp = api(owner).post(f"{url}/remove-member/", {"user_id": member.id}, format="json")
    assert resp.status_code == 200
    # Задачи удалённого участника остались без исполнителя
    tasks[1].refresh_from_db()
    assert tasks[1].assignee is None
    assert api(member).get(f"{url}/").status_code == 404


def test_project_stats(api, project, owner, tasks):
    resp = api(owner).get(f"/api/projects/{project.id}/stats/")
    assert resp.status_code == 200
    assert resp.json() == {"todo": 1, "in_progress": 1, "review": 0, "done": 1, "total": 3}


def test_project_search_and_tasks_count(api, project, owner, tasks):
    Project.objects.create(name="Блог", owner=owner)
    resp = api(owner).get("/api/projects/", {"search": "магазин"})
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["tasks_count"] == 3
