from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, ProjectViewSet, TagViewSet, TaskViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")
router.register("tags", TagViewSet, basename="tag")
router.register("comments", CommentViewSet, basename="comment")

urlpatterns = router.urls
