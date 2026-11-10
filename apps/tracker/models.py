"""Модели трекера: проекты, теги, задачи и комментарии."""

from django.conf import settings
from django.db import models
from django.db.models import Q


class TimeStampedModel(models.Model):
    """Абстрактная модель с датами создания и изменения."""

    created_at = models.DateTimeField("создано", auto_now_add=True)
    updated_at = models.DateTimeField("обновлено", auto_now=True)

    class Meta:
        abstract = True


class ProjectQuerySet(models.QuerySet):
    def for_user(self, user):
        """Проекты, где пользователь владелец или участник."""
        return self.filter(Q(owner=user) | Q(members=user)).distinct()


class Project(TimeStampedModel):
    name = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_projects", verbose_name="владелец"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="projects", blank=True, verbose_name="участники"
    )

    objects = ProjectQuerySet.as_manager()

    class Meta:
        verbose_name = "проект"
        verbose_name_plural = "проекты"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name

    def has_member(self, user) -> bool:
        """Владелец тоже считается участником проекта."""
        return user.is_authenticated and (
            self.owner_id == user.id or self.members.filter(pk=user.pk).exists()
        )


class Tag(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags", verbose_name="проект")
    name = models.CharField("название", max_length=50)
    color = models.CharField("цвет", max_length=7, default="#6c757d", help_text="HEX, например #ff0000")

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"
        ordering = ("name",)
        constraints = [models.UniqueConstraint(fields=("project", "name"), name="unique_tag_per_project")]

    def __str__(self) -> str:
        return self.name


class Task(TimeStampedModel):
    class Status(models.TextChoices):
        TODO = "todo", "К выполнению"
        IN_PROGRESS = "in_progress", "В работе"
        REVIEW = "review", "На проверке"
        DONE = "done", "Готово"

    class Priority(models.IntegerChoices):
        # Числа позволяют сортировать задачи по важности
        LOW = 1, "Низкий"
        MEDIUM = 2, "Средний"
        HIGH = 3, "Высокий"
        CRITICAL = 4, "Критический"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks", verbose_name="проект")
    title = models.CharField("заголовок", max_length=255)
    description = models.TextField("описание", blank=True)
    status = models.CharField("статус", max_length=20, choices=Status.choices, default=Status.TODO, db_index=True)
    priority = models.PositiveSmallIntegerField("приоритет", choices=Priority.choices, default=Priority.MEDIUM)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_tasks", verbose_name="автор"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="исполнитель",
    )
    tags = models.ManyToManyField(Tag, related_name="tasks", blank=True, verbose_name="теги")
    due_date = models.DateField("срок", null=True, blank=True)

    class Meta:
        verbose_name = "задача"
        verbose_name_plural = "задачи"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("project", "status"))]

    def __str__(self) -> str:
        return self.title


class Comment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments", verbose_name="задача")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments", verbose_name="автор"
    )
    text = models.TextField("текст")

    class Meta:
        verbose_name = "комментарий"
        verbose_name_plural = "комментарии"
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.author} → {self.task}: {self.text[:30]}"
