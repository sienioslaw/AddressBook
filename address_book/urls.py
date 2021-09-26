from rest_framework import routers

from .views import AuthViewSet, AddressViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register('/api/auth', AuthViewSet, basename='auth')
router.register('/api/addresses', AddressViewSet, basename='addresses')

urlpatterns = router.urls