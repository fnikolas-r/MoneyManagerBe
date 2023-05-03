import csv
from django.db.models import F, Sum, Q, Max, Min
from django.db import transaction
from django.db.models.functions import Coalesce
from rest_framework import viewsets, response, generics, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from .serializer import RekeningSerializer, TransaksiSerializer, CategorySerializer, \
    UtangPiutangSerializer, TransferSerializer, TransaksiSummarySerializer
from .auth_serializer import RegisterSerializer, LoginSerializer
from keuangan.models import Rekening, Transaksi, Kategori, UtangPiutang, Transfer
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .permission import NotTransferAndUtangPiutang
from rest_framework_simplejwt.views import TokenObtainPairView
from copy import deepcopy as dp
from django.http import HttpResponse
from datetime import datetime


# Functions
def export_csv(user,serializer):
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    response['Content-Disposition'] = 'attachment; filename="{current}_{user}_{filename}"'.format(current=current_date,
                                                                                                  user=user.username,
                                                                                                  filename='output.csv')

    object_serializer = serializer(
        Transaksi.objects.filter(user=user),
        many=True
    )
    header= TransaksiSerializer.Meta.fields

    writer = csv.DictWriter(response,fieldnames=header)
    writer.writeheader()
    for row in object_serializer.data:
        writer.writerow(row)
    return response

# Create your views here.
class KeuanganViewSetComplex(viewsets.ModelViewSet):

    def __init__(self, model, custom_order=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.myModel = model
        self.custom_filter = custom_order

    def get_queryset(self):
        try:
            user = self.request.user
            if self.custom_filter:
                return self.myModel.objects.filter(user=user).order_by(self.custom_filter)

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

    def __init__(self, *args, **kwargs):
        super().__init__(model=Rekening, *args, **kwargs)

    @action(detail=True)
    def transaksi(self, request, pk=None):
        transaksi = Transaksi.objects.filter(user=self.request.user).filter(rekening__id=pk).all()
        transaksi = TransaksiSerializer(transaksi, many=True)
        return response.Response(transaksi.data)

    @action(detail=False)
    def stats_summary(self, request):
        transaksi = Transaksi.objects.filter(user=self.request.user)
        transaksi = transaksi.annotate(hasil=F('price') * F('trc_type')).values("rekening").annotate(
            total=Coalesce(Sum("hasil"), 0),
            name=F("rekening__name"),
            rekening_hidden=F("rekening__is_hidden"),
            icon=F("rekening__icon"),
            latest_trc=Max("trc_date"),
            first_trc=Min("trc_date")
        ).order_by("-total")

        return response.Response(TransaksiSummarySerializer(transaksi, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True)
    def transfer_list(self, request, pk=None):
        transaksi = Transfer.objects.filter(user=self.request.user).filter(Q(from_account=pk) | Q(to_account=pk)).all()
        return response.Response(TransferSerializer(transaksi, many=True).data, status=status.HTTP_200_OK)


class TransaksiViewSet(KeuanganViewSetComplex):
    serializer_class = TransaksiSerializer
    permission_classes = [IsAuthenticated, NotTransferAndUtangPiutang]

    def __init__(self, *args, **kwargs):
        super().__init__(model=Transaksi,custom_order='-trc_date',*args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_protected:
            return response.Response("Tidak Dapat Menghapus Data yang dilindungi", status=status.HTTP_400_BAD_REQUEST)
        else:
            return super(TransaksiViewSet, self).destroy(request, *args, **kwargs)

    @action(methods=["GET"],detail=False)
    def exports(self,request):
        output = request.query_params.get("o")
        if output == "csv":
            return export_csv(self.request.user,self.serializer_class)
        return response.Response({"message": "Harap Tentukan jenis File Output"}, status.HTTP_400_BAD_REQUEST)


class TransferViewSet(KeuanganViewSetComplex):
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(model=Transfer,custom_order='-tgl_transfer', *args, **kwargs)


class KategoriViewSet(KeuanganViewSetComplex):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(model=Kategori, *args, **kwargs)

    @action(methods=["GET"], detail=True)
    def transaksi(self, request, pk=None):
        return response.Response(
            TransaksiSerializer(Transaksi.objects.filter(kategori=pk).all(), many=True).data,
            status=status.HTTP_200_OK
        )


class UtangPiutangViewSet(KeuanganViewSetComplex):
    permission_classes = [IsAuthenticated]
    serializer_class = UtangPiutangSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(model=UtangPiutang,custom_order='-tgl_transaksi', *args, **kwargs)

    @action(detail=True, methods=["POST"])
    def set_done(self, request, pk=None):
        # Kalau done hapus
        # Kalau ga done maka kasih done
        up: UtangPiutang = UtangPiutang.objects.filter(id=pk).first()

        tujuan = up.rekening
        if request.data.get("tujuan"):
            tujuan = Rekening.objects.get(pk=request.data.get("tujuan"))

        done_cat = 1
        if up.type == "U":
            done_cat = -1
        if (up.is_done):
            Transaksi.objects.exclude(trc_date=up.tgl_transaksi).filter(id_utang_piutang=up,
                                                                        trc_type=done_cat).first().delete()
        else:
            new_trc = Transaksi(
                trc_type=done_cat,
                pelaku=up.person_in_charge,
                trc_name=f"Pelunasan {'Utang' if up.type == 'U' else 'Piutang'} dari {up.person_in_charge}",
                price=up.nominal,
                rekening=tujuan,
                kategori=None,
                user=request.user,
                id_utang_piutang=up)
            new_trc.save()
        up.is_done = not up.is_done
        up.save()

        return response.Response(self.serializer_class(up).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def split_bill(self, request):
        penerima = request.data
        rekening = Rekening.objects.get(id=penerima['rekening'])
        data = dp(penerima)
        del data["split_bills"]

        try:
            with transaction.atomic():
                tipe = data['type']
                for x in penerima["split_bills"]:
                    data["nominal"] = x["amt"]
                    pelaku = x['person']

                    if str(pelaku).lower() not in ['saya', 'i', 'i am', 'aku']:
                        up = UtangPiutang(
                            user=self.request.user,
                            keterangan=data['keterangan'],
                            due_date=data['due_date'],
                            person_in_charge=pelaku,
                            tgl_transaksi=data['tgl_transaksi'],
                            nominal=data['nominal'],
                            rekening=rekening,
                            type=tipe
                        )
                        up.save()
                    else:
                        up = None

                    tr = Transaksi(
                        trc_type=1 if tipe == 'U' else -1,
                        pelaku=pelaku,
                        trc_name=f"{'Utang dari' if tipe == 'U' else 'Piutang ke'} {pelaku} ket:{data['keterangan']}",
                        price=data["nominal"],
                        rekening=rekening,
                        trc_date=data["tgl_transaksi"],
                        kategori=None,
                        user=self.request.user,
                        id_utang_piutang=up
                    )
                    tr.save()
                return response.Response({"message": "Berhasil Menambahkan Split Bill"}, status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        return response.Response(RegisterSerializer(request.user).data, status.HTTP_200_OK)
