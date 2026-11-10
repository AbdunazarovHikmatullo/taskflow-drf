"""Настройка Django Admin для трекера."""

from django.contrib import admin

from .models import Comment, Project, Tag, Task


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ("title", "status", "priority", "assignee", "due_date")
    show_change_link = True


class TagInline(admin.TabularInline):
    model = Tag
    extra = 0


class CommentInline(admin.StackedInline):
    model = Comment
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "members_count", "tasks_count", "created_at")
    search_fields = ("name", "description", "owner__username")
    list_filter = ("created_at",)
    filter_horizontal = ("members",)
    inlines = (TagInline, TaskInline)

    @admin.display(description="участников")
    def members_count(self, obj):
        return obj.members.count()

    @admin.display(description="задач")
    def tasks_count(self, obj):
        return obj.tasks.count()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "priority", "assignee", "due_date", "created_at")
    list_filter = ("status", "priority", "project", "due_date")
    list_editable = ("status", "priority")
    search_fields = ("title", "description")
    autocomplete_fields = ("project", "assignee", "author")
    filter_horizontal = ("tags",)
    date_hierarchy = "created_at"
    inlines = (CommentInline,)
    list_select_related = ("project", "assignee")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "project")
    list_filter = ("project",)
    search_fields = ("name",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "short_text", "created_at")
    search_fields = ("text", "task__title", "author__username")
    list_select_related = ("task", "author")

    @admin.display(description="текст")
    def short_text(self, obj):
        return obj.text[:60]
