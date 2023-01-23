from rest_framework import routers,renderers
from django.urls import path,include
from .views import RekeningViewSet,RegisterView
from rest_framework_simplejwt.views import TokenRefreshView,TokenObtainPairView

router = routers.DefaultRouter()
router.register(r'rekening', RekeningViewSet, basename='k_akun')


urlpatterns = [
    path('',include(router.urls)),
    path('login/', TokenObtainPairView.as_view(), name='obtain_token'),
    path('login/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('register/', RegisterView.as_view(), name='auth_register'),
]