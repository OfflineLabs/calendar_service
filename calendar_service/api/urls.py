from django.conf.urls import url, include
from rest_framework import routers

from api import views


router = routers.DefaultRouter()
router.register(r'calendars', views.CalendarViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'rules', views.RuleViewSet)

occurrence_router = routers.SimpleRouter()
occurrence_router.register(r'occurrences', views.OccurrenceViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^events/(?P<event_id>\d+)/', include(occurrence_router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]