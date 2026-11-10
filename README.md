# TaskFlow — трекер задач на Django REST Framework

**TaskFlow** — backend для командного трекера задач (упрощённый аналог Jira/Trello).
Пользователи создают проекты, приглашают участников, ведут задачи со статусами, приоритетами,
исполнителями, сроками и тегами, обсуждают их в комментариях. Доступ к данным ограничен
кастомными правами: проект и его задачи видят только владелец и участники.

> Портфолио-проект: демонстрирует ViewSets, сериализаторы с валидацией, кастомные permissions,
> django-filter, JWT, OpenAPI-документацию, Django Admin, PostgreSQL в Docker и тесты.

## Возможности

- **JWT-аутентификация** (SimpleJWT): регистрация, получение и обновление токенов, `/me`
- **Проекты**: владелец и участники, добавление/удаление участников, статистика по статусам
- **Задачи**: статусы (`todo`, `in_progress`, `review`, `done`), приоритеты (1–4), исполнитель,
  срок, теги; быстрые действия `change-status` и `assign-to-me`
- **Комментарии** к задачам и **теги** внутри проекта
- **Права доступа**:
  - менять/удалять проект и управлять участниками может только владелец
  - задачи читают и редактируют все участники, удаляет — автор или владелец проекта
  - комментарий изменяет и удаляет только его автор
  - исполнитель и теги задачи должны принадлежать её проекту
- **Фильтры, поиск, сортировка** (django-filter, SearchFilter, OrderingFilter)
- **Пагинация** с параметром `page_size` (до 100)
- **OpenAPI 3** (drf-spectacular): Swagger UI на `/api/docs/`
- **Django Admin**: инлайны, фильтры, поиск, редактирование статуса прямо в списке
- Docker Compose: Django + Gunicorn + PostgreSQL, автоматические миграции и collectstatic

## Стек

| Область | Технологии |
|---|---|
| Язык | Python 3.12 |
| Фреймворк | Django 5.1, Django REST Framework 3.15 |
| Аутентификация | djangorestframework-simplejwt |
| Фильтрация | django-filter |
| Документация | drf-spectacular (OpenAPI 3, Swagger UI) |
| База данных | PostgreSQL 16 (psycopg 3), SQLite для тестов |
| Сервер | Gunicorn, WhiteNoise |
| Тесты | pytest, pytest-django |
| Инфраструктура | Docker, Docker Compose |

## Структура проекта

```
taskflow-drf/
├── config/                 # настройки, корневые URL, WSGI/ASGI
├── apps/
│   ├── users/              # регистрация, профиль, поиск пользователей
│   └── tracker/
│       ├── models.py       # Project, Task, Tag, Comment
│       ├── serializers.py  # сериализаторы с валидацией
│       ├── permissions.py  # кастомные права: владелец / участник / автор
│       ├── filters.py      # FilterSet для задач
│       ├── views.py        # ViewSet'ы и дополнительные actions
│       ├── admin.py        # настройка Django Admin
│       └── tests/          # pytest-тесты API и админки
├── conftest.py             # общие фикстуры
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh           # migrate + collectstatic + createsuperuser
└── requirements.txt
```

## Запуск через Docker

```bash
git clone https://github.com/AbdunazarovHikmatullo/taskflow-drf.git
cd taskflow-drf
cp .env.example .env        # задайте DJANGO_SECRET_KEY и пароль суперпользователя
docker compose up --build -d
```

- API: http://localhost:8000/api/
- Swagger UI: http://localhost:8000/api/docs/
- Django Admin: http://localhost:8000/admin/ (логин/пароль из `DJANGO_SUPERUSER_*` в `.env`)
- Health-check: http://localhost:8000/health/

Остановить и удалить данные: `docker compose down -v`.

## Локальный запуск и тесты

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate          # по умолчанию SQLite
python manage.py createsuperuser
python manage.py runserver

pytest -v                          # запуск тестов
```

## Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/token/` | Получить `access` и `refresh` токены |
| POST | `/api/auth/token/refresh/` | Обновить `access` токен |
| GET | `/api/auth/me/` | Текущий пользователь |
| GET | `/api/auth/users/?search=` | Поиск пользователей |
| CRUD | `/api/projects/` | Проекты |
| POST | `/api/projects/{id}/add-member/` | Добавить участника (владелец) |
| POST | `/api/projects/{id}/remove-member/` | Убрать участника (владелец) |
| GET | `/api/projects/{id}/stats/` | Количество задач по статусам |
| CRUD | `/api/tasks/` | Задачи |
| POST | `/api/tasks/{id}/change-status/` | Сменить статус |
| POST | `/api/tasks/{id}/assign-to-me/` | Назначить на себя |
| CRUD | `/api/tags/` | Теги проекта |
| CRUD | `/api/comments/` | Комментарии (`?task=<id>`) |

### Фильтры задач

`project`, `status` (можно несколько), `priority`, `priority_min`, `assignee`, `author`,
`tags`, `unassigned=true`, `mine=true`, `due_before`, `due_after`,
поиск `search` (заголовок, описание, теги), сортировка `ordering`
(`priority`, `due_date`, `created_at`, `status`, `title`, минус — по убыванию), `page`, `page_size`.

## Примеры запросов

```bash
API=http://localhost:8000/api

# Регистрация и получение токена
curl -X POST $API/auth/register/ -H "Content-Type: application/json" \
  -d '{"username": "hikmat", "email": "hikmat@example.com", "password": "VeryStr0ngPass"}'
TOKEN=$(curl -s -X POST $API/auth/token/ -H "Content-Type: application/json" \
  -d '{"username": "hikmat", "password": "VeryStr0ngPass"}' | python -c "import sys,json;print(json.load(sys.stdin)['access'])")
AUTH="Authorization: Bearer $TOKEN"

# Проект и участник
curl -X POST $API/projects/ -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"name": "Интернет-магазин", "description": "Backend на Django"}'
curl -X POST $API/projects/1/add-member/ -H "$AUTH" -H "Content-Type: application/json" -d '{"user_id": 2}'

# Тег и задача
curl -X POST $API/tags/ -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"project": 1, "name": "backend", "color": "#0d6efd"}'
curl -X POST $API/tasks/ -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"project": 1, "title": "Настроить CI", "priority": 3, "assignee_id": 2, "tag_ids": [1], "due_date": "2026-12-01"}'

# Фильтры, поиск, сортировка
curl "$API/tasks/?project=1&status=todo&status=in_progress&priority_min=3&ordering=-priority" -H "$AUTH"
curl "$API/tasks/?search=CI&mine=true&page_size=10" -H "$AUTH"

# Смена статуса и комментарий
curl -X POST $API/tasks/1/change-status/ -H "$AUTH" -H "Content-Type: application/json" -d '{"status": "review"}'
curl -X POST $API/comments/ -H "$AUTH" -H "Content-Type: application/json" -d '{"task": 1, "text": "Готово к ревью"}'

# Статистика проекта
curl $API/projects/1/stats/ -H "$AUTH"
# {"todo": 0, "in_progress": 0, "review": 1, "done": 0, "total": 1}
```

## Лицензия

MIT — см. [LICENSE](LICENSE).

## Автор

Hikmatullo Abdunazarov — Python backend-разработчик.
