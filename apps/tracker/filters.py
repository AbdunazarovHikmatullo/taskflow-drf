"""Фильтры для списков задач (django-filter)."""

import django_filters

from .models import Tag, Task


class TaskFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(choices=Task.Status.choices)
    priority = django_filters.MultipleChoiceFilter(choices=Task.Priority.choices)
    priority_min = django_filters.NumberFilter(field_name="priority", lookup_expr="gte")
    due_before = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")
    due_after = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())
    unassigned = django_filters.BooleanFilter(field_name="assignee", lookup_expr="isnull")
    mine = django_filters.BooleanFilter(method="filter_mine", label="Только мои задачи")

    class Meta:
        model = Task
        fields = ("project", "assignee", "author")

    def filter_mine(self, queryset, name, value):
        if value:
            return queryset.filter(assignee=self.request.user)
        return queryset
