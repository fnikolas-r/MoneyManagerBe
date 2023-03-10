from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from .views import RegisterView, UserProfileView
from .views import RekeningViewSet, TransaksiViewSet, KategoriViewSet, UtangPiutangViewSet, TransferViewSet

router = routers.DefaultRouter()
router.register(r'rekening', RekeningViewSet, basename='k_akun')
router.register(r'transaksi',TransaksiViewSet,basename='k_trc')
router.register(r'kategori',KategoriViewSet,basename='k_cat')
router.register(r'utangpiutang',UtangPiutangViewSet,basename='k_up')
router.register(r'transfer',TransferViewSet,basename='k_trf')



urlpatterns = [
    path('',include(router.urls)),
    path('login/', TokenObtainPairView.as_view(), name='obtain_token'),
    path('login/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('login/profile/', UserProfileView.as_view(), name='user_profile'),
    path('register/', RegisterView.as_view(), name='auth_register'),
]