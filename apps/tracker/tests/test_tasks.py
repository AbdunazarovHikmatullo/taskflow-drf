"""Задачи: CRUD, права, фильтры, поиск, сортировка, пагинация."""

import pytest

from apps.tracker.models import Tag, Task

pytestmark = pytest.mark.django_db


def test_member_creates_task(api, project, member, tags):
    payload = {"project": project.id, "title": "Добавить фильтры", "priority": 3,
               "assignee_id": member.id, "tag_ids": [tags[0].id], "due_date": "2026-12-31"}
    resp = api(member).post("/api/tasks/", payload, format="json")
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["author"]["username"] == "member"
    assert body["assignee"]["username"] == "member"
    assert body["status"] == "todo"
    assert body["priority_display"] == "Высокий"
    assert [t["name"] for t in body["tags"]] == ["backend"]


def test_stranger_cannot_create_task(api, project, stranger):
    resp = api(stranger).post("/api/tasks/", {"project": project.id, "title": "Чужая"}, format="json")
    assert resp.status_code == 400


def test_assignee_must_be_member(api, project, owner, stranger):
    resp = api(owner).post("/api/tasks/", {"project": project.id, "title": "X", "assignee_id": stranger.id},
                           format="json")
    assert resp.status_code == 400
    assert "assignee_id" in resp.json()


def test_tags_must_belong_to_project(api, project, owner, make_user):
    from apps.tracker.models import Project
    other = Project.objects.create(name="Другой", owner=owner)
    foreign_tag = Tag.objects.create(project=other, name="чужой")
    resp = api(owner).post("/api/tasks/", {"project": project.id, "title": "X", "tag_ids": [foreign_tag.id]},
                           format="json")
    assert resp.status_code == 400


def test_stranger_cannot_see_tasks(api, tasks, stranger):
    assert api(stranger).get("/api/tasks/").json()["count"] == 0
    assert api(stranger).get(f"/api/tasks/{tasks[0].id}/").status_code == 404


def test_delete_only_by_author_or_project_owner(api, tasks, owner, member):
    # Участник не может удалить чужую задачу
    assert api(member).delete(f"/api/tasks/{tasks[0].id}/").status_code == 403
    # Свою — может
    assert api(member).delete(f"/api/tasks/{tasks[1].id}/").status_code == 204
    # Владелец проекта может удалить любую
    assert api(owner).delete(f"/api/tasks/{tasks[2].id}/").status_code == 204


def test_member_can_update_task(api, tasks, member):
    resp = api(member).patch(f"/api/tasks/{tasks[0].id}/", {"description": "Через GitHub Actions"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["description"] == "Через GitHub Actions"


def test_change_status_and_assign_to_me(api, tasks, owner):
    task = tasks[0]
    resp = api(owner).post(f"/api/tasks/{task.id}/change-status/", {"status": "review"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["status"] == "review"

    bad = api(owner).post(f"/api/tasks/{task.id}/change-status/", {"status": "unknown"}, format="json")
    assert bad.status_code == 400

    resp = api(owner).post(f"/api/tasks/{task.id}/assign-to-me/")
    assert resp.json()["assignee"]["username"] == "owner"


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"status": "done"}, {"Написать документацию"}),
        ({"status": ["todo", "in_progress"]}, {"Настроить CI", "Исправить оплату"}),
        ({"priority_min": 3}, {"Настроить CI", "Исправить оплату"}),
        ({"unassigned": "true"}, {"Настроить CI", "Написать документацию"}),
        ({"due_before": "2026-11-25"}, {"Исправить оплату"}),
        ({"due_after": "2026-11-25"}, {"Настроить CI"}),
        ({"search": "оплат"}, {"Исправить оплату"}),
        ({"search": "README"}, {"Написать документацию"}),
        ({"search": "bug"}, {"Исправить оплату"}),
    ],
)
def test_task_filters(api, tasks, owner, params, expected):
    resp = api(owner).get("/api/tasks/", params)
    assert resp.status_code == 200
    assert {t["title"] for t in resp.json()["results"]} == expected


def test_filter_by_tag_and_mine(api, tasks, tags, member):
    by_tag = api(member).get("/api/tasks/", {"tags": tags[1].id}).json()
    assert [t["title"] for t in by_tag["results"]] == ["Исправить оплату"]
    mine = api(member).get("/api/tasks/", {"mine": "true"}).json()
    assert [t["title"] for t in mine["results"]] == ["Исправить оплату"]


def test_ordering_by_priority(api, tasks, owner):
    resp = api(owner).get("/api/tasks/", {"ordering": "-priority"})
    assert [t["priority"] for t in resp.json()["results"]] == [4, 3, 1]


def test_pagination(api, project, owner):
    Task.objects.bulk_create(Task(project=project, title=f"Задача {i}", author=owner) for i in range(25))
    first = api(owner).get("/api/tasks/", {"page_size": 10}).json()
    assert first["count"] == 25
    assert len(first["results"]) == 10
    assert first["next"] is not None
    last = api(owner).get("/api/tasks/", {"page_size": 10, "page": 3}).json()
    assert len(last["results"]) == 5


def test_cannot_move_task_to_other_project(api, tasks, owner):
    from apps.tracker.models import Project
    other = Project.objects.create(name="Другой", owner=owner)
    resp = api(owner).patch(f"/api/tasks/{tasks[0].id}/", {"project": other.id}, format="json")
    assert resp.status_code == 200
    assert resp.json()["project"] == tasks[0].project_id
