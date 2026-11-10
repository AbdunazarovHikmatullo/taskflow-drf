"""Комментарии и теги."""

import pytest

pytestmark = pytest.mark.django_db


def test_comment_flow(api, tasks, owner, member):
    task = tasks[0]
    resp = api(member).post("/api/comments/", {"task": task.id, "text": "Беру в работу"}, format="json")
    assert resp.status_code == 201
    comment_id = resp.json()["id"]
    assert resp.json()["author"]["username"] == "member"

    listed = api(owner).get("/api/comments/", {"task": task.id}).json()
    assert listed["count"] == 1

    # Чужой комментарий нельзя изменить или удалить
    assert api(owner).patch(f"/api/comments/{comment_id}/", {"text": "x"}, format="json").status_code == 403
    assert api(owner).delete(f"/api/comments/{comment_id}/").status_code == 403

    resp = api(member).patch(f"/api/comments/{comment_id}/", {"text": "Готово к ревью"}, format="json")
    assert resp.status_code == 200
    assert api(member).delete(f"/api/comments/{comment_id}/").status_code == 204


def test_comments_count_in_task(api, tasks, owner):
    for text in ("Первый", "Второй"):
        api(owner).post("/api/comments/", {"task": tasks[0].id, "text": text}, format="json")
    resp = api(owner).get(f"/api/tasks/{tasks[0].id}/")
    assert resp.json()["comments_count"] == 2


def test_stranger_cannot_comment(api, tasks, stranger):
    resp = api(stranger).post("/api/comments/", {"task": tasks[0].id, "text": "Спам"}, format="json")
    assert resp.status_code == 400
    assert api(stranger).get("/api/comments/").json()["count"] == 0


def test_tag_create_and_uniqueness(api, project, member, stranger):
    resp = api(member).post("/api/tags/", {"project": project.id, "name": "frontend", "color": "#00ff00"},
                            format="json")
    assert resp.status_code == 201
    dup = api(member).post("/api/tags/", {"project": project.id, "name": "frontend"}, format="json")
    assert dup.status_code == 400
    bad_color = api(member).post("/api/tags/", {"project": project.id, "name": "ui", "color": "green"},
                                 format="json")
    assert bad_color.status_code == 400
    assert api(stranger).post("/api/tags/", {"project": project.id, "name": "x"}, format="json").status_code == 400


def test_tags_filtered_by_project(api, tags, owner, stranger):
    assert api(owner).get("/api/tags/").json()["count"] == 2
    assert api(stranger).get("/api/tags/").json()["count"] == 0
