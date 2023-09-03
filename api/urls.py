from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from .views import RegisterView
from .views import RekeningViewSet, TransaksiViewSet, KategoriViewSet, UtangPiutangViewSet, TransferViewSet,\
    ProfileViewSet
from .views import login_by_google,link_google

router = routers.DefaultRouter()
router.register(r'rekening', RekeningViewSet, basename='k_akun')
router.register(r'transaksi',TransaksiViewSet,basename='k_trc')
router.register(r'kategori',KategoriViewSet,basename='k_cat')
router.register(r'utangpiutang',UtangPiutangViewSet,basename='k_up')
router.register(r'transfer',TransferViewSet,basename='k_trf')



urlpatterns = [
    path('',include(router.urls)),
    path('login/', TokenObtainPairView.as_view(), name='obtain_token'),
    path('login/social/google/',login_by_google,name='obtain_token_by_google'),
    path('login/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('login/profile/', ProfileViewSet.as_view({
        'get': 'retrieve',
        'patch':'patch',
        'delete':'delete_google_link'
    }), name='user_profile'),
    path('login/profile/delete_photo/', ProfileViewSet.as_view({
        'post':'delete_photo'
    }), name='user_photo_delete'),
    path('login/profile/link/',link_google , name='user_google_link'),
    path('register/', RegisterView.as_view(), name='auth_register'),
]