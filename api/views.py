from django.db.models import  F,Sum,Q, Max,Min
from django.db.models.functions import  Coalesce
from rest_framework import viewsets,response,generics,status
from rest_framework.views import APIView
from rest_framework.decorators import action
from .serializer import RekeningSerializer, TransaksiSerializer,CategorySerializer, \
    UtangPiutangSerializer,TransferSerializer,TransaksiSummarySerializer
from .auth_serializer import RegisterSerializer,LoginSerializer
from keuangan.models import Rekening, Transaksi, Kategori,UtangPiutang,Transfer
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.contrib.auth.models import User
from .permission import  NotTransferAndUtangPiutang
from rest_framework_simplejwt.views import TokenObtainPairView

# Create your views here.
class KeuanganViewSetComplex(viewsets.ModelViewSet):

    def __init__(self,model,custom_filter=False,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.myModel = model
        self.custom_filter = custom_filter

    def get_queryset(self):
        try:
            user = self.request.user
            return self.myModel.objects.filter(user=user)
        except:
            return []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return response.Response({"message"})

class RekeningViewSet(KeuanganViewSetComplex):
    serializer_class = RekeningSerializer
    permission_classes = [IsAuthenticated]
    def __init__(self,*args,**kwargs):
        super().__init__(model=Rekening,*args,**kwargs)
    @action(detail=True)
    def transaksi(self,request,pk=None):
        transaksi = Transaksi.objects.filter(user=self.request.user).filter(rekening__id=pk).all()
        transaksi = TransaksiSerializer(transaksi,many=True)
        return response.Response(transaksi.data)

    @action(detail=False)
    def stats_summary(self,request):

        transaksi = Transaksi.objects.filter(user=self.request.user)
        transaksi = transaksi.annotate(hasil=F('price')*F('trc_type')).values("rekening").annotate(
            total=Coalesce(Sum("hasil"),0),
            name=F("rekening__name"),
            latest_trc=Max("trc_date"),
            first_trc=Min("trc_date")
        )

        return response.Response(TransaksiSummarySerializer(transaksi,many=True).data,status=status.HTTP_200_OK)

    @action(detail=True)
    def transfer_list(self,request,pk=None):
        transaksi = Transfer.objects.filter(user=self.request.user).filter(Q(from_account=pk)|Q(to_account=pk)).all()
        return response.Response(TransferSerializer(transaksi,many=True).data,status = status.HTTP_200_OK)
class TransaksiViewSet(KeuanganViewSetComplex):
    serializer_class = TransaksiSerializer
    permission_classes = [IsAuthenticated,NotTransferAndUtangPiutang]


    def __init__(self,*args,**kwargs):
        super().__init__(model=Transaksi,*args,**kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_protected:
            return response.Response("Tidak Dapat Menghapus Data yang dilindungi", status=status.HTTP_400_BAD_REQUEST)
        else:
            return super(TransaksiViewSet,self).destroy(request,*args,**kwargs)

class TransferViewSet(KeuanganViewSetComplex):
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self,*args,**kwargs):
        super().__init__(model=Transfer,*args,**kwargs)

class KategoriViewSet(KeuanganViewSetComplex):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def __init__(self,*args,**kwargs):
        super().__init__(model=Kategori,*args,**kwargs)

    @action(methods=["GET"],detail=True)
    def transaksi(self,request,pk=None):
        return response.Response(
            TransaksiSerializer(Transaksi.objects.filter(kategori=pk).all(),many=True).data,
            status = status.HTTP_200_OK
        )
class UtangPiutangViewSet(KeuanganViewSetComplex):
    permission_classes = [IsAuthenticated]
    serializer_class = UtangPiutangSerializer

    def __init__(self,*args,**kwargs):
        super().__init__(model=UtangPiutang,*args,**kwargs)



# Auth
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):

        return response.Response(RegisterSerializer(request.user).data,status.HTTP_200_OK)
