from . import views
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(r'properties', views.PropertyViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'requests', views.RequestViewSet)
router.register(r'snapshots', views.SnapshotViewSet)
router.register(r'participant', views.ParticipantViewSet)
router.register(r'stickers', views.StickerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('fetch-room/', views.get_chat),
    path('room-import', views.import_room),
    path('post-import', views.import_post),
    path('posts/', views.get_posts),
    path('make_label/', views.make_label)
]
