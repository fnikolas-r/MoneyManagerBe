import csv
import json
from django.shortcuts import get_object_or_404
from django.db.models import F, Sum, Q, Max, Min
from django.db import transaction
from django.db.models.functions import Coalesce
from rest_framework import viewsets, response, generics, status, mixins
from rest_framework.decorators import action, api_view
from .serializer import RekeningSerializer, TransaksiSerializer, CategorySerializer, \
    UtangPiutangSerializer, TransferSerializer, TransaksiSummarySerializer
from .auth_serializer import UserSerializer, LoginSerializer, ProfileSerializer
from keuangan.models import Rekening, Transaksi, Kategori, UtangPiutang, Transfer
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .permission import NotTransferAndUtangPiutang
from rest_framework_simplejwt.views import TokenObtainPairView
from copy import deepcopy as dp
from django.http import HttpResponse
from datetime import datetime
from pengguna.models import Profile
import os
import requests as req_lib
from rest_framework_simplejwt.tokens import RefreshToken


# Functions
def export_csv(user, serializer):
    response = HttpResponse(content_type='text/csv')
    current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    response['Content-Disposition'] = 'attachment; filename="{current}_{user}_{filename}"'.format(current=current_date,
                                                                                                  user=user.username,
                                                                                                  filename='output.csv')

    object_serializer = serializer(
        Transaksi.objects.filter(user=user),
        many=True
    )
    header = TransaksiSerializer.Meta.fields

    writer = csv.DictWriter(response, fieldnames=header)
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
            first_trc=Min("trc_date"),
            pinned=F("rekening__is_pinned"),
            trf_minimum=Coalesce(F("rekening__trf_minimum"),0)
        ).order_by("-pinned","-total")
        return response.Response(TransaksiSummarySerializer(transaksi, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def set_pinned(self, request, pk=None, *args, **kwargs):
        instance: Rekening = get_object_or_404(Rekening, pk=pk)
        instance.is_pinned = not instance.is_pinned
        instance.save()
        return response.Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)

    @action(detail=True)
    def transfer_list(self, request, pk=None):
        transaksi = Transfer.objects.filter(user=self.request.user).filter(Q(from_account=pk) | Q(to_account=pk)).all()
        return response.Response(TransferSerializer(transaksi, many=True).data, status=status.HTTP_200_OK)


class TransaksiViewSet(KeuanganViewSetComplex):
    serializer_class = TransaksiSerializer
    permission_classes = [IsAuthenticated, NotTransferAndUtangPiutang]

    def __init__(self, *args, **kwargs):
        super().__init__(model=Transaksi, custom_order='-trc_date', *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_protected:
            return response.Response("Tidak Dapat Menghapus Data yang dilindungi", status=status.HTTP_400_BAD_REQUEST)
        else:
            return super(TransaksiViewSet, self).destroy(request, *args, **kwargs)

    @action(methods=["GET"], detail=False)
    def exports(self, request):
        output = request.query_params.get("o")
        if output == "csv":
            return export_csv(self.request.user, self.serializer_class)
        return response.Response({"message": "Harap Tentukan jenis File Output"}, status.HTTP_400_BAD_REQUEST)


class TransferViewSet(KeuanganViewSetComplex):
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(model=Transfer, custom_order='-tgl_transfer', *args, **kwargs)


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
        super().__init__(model=UtangPiutang, custom_order='-tgl_transaksi', *args, **kwargs)

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
    serializer_class = UserSerializer


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


@api_view(["POST"])
def login_by_google(request):
    key = request.data.get("t")
    if not key:
        return response.Response({"message": "Token Otentikasi Tidak Ditemukan"}, status=status.HTTP_400_BAD_REQUEST)
    result = req_lib.get(f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={key}",
                         headers={"Authorization": "Bearer " + key})
    try:
        result = result.json()
        id = result.get('id')
        profile = Profile.objects.filter(google_id=id)
        if profile.exists():
            profile = profile.first()
            profile.google_data = json.dumps(result)
            profile.save()
            refresh = RefreshToken.for_user(profile.user)
            return response.Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return response.Response({"message": "Akun Tidak Ditemukan"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return response.Response({"message": f"Terjadi Kesalahan {e}"}
                                 , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def link_google(request):
    print(request.data)
    key = request.data.get("t")
    if not key:
        return response.Response({"message": "Token Otentikasi Tidak Ditemukan"}, status=status.HTTP_400_BAD_REQUEST)
    result = req_lib.get(f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={key}",
                         headers={"Authorization": "Bearer " + key})
    try:
        result = result.json()
        id = result.get('id')
        profile = Profile.objects.filter(user=request.user).first()
        profile.google_id = id;
        profile.google_data = json.dumps(result)
        profile.save()
        return response.Response({"message": "Berhasil Login"}, status=status.HTTP_200_OK)

    except Exception as e:
        return response.Response({"message": f"Terjadi Kesalahan {e}"}
                                 , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileViewSet(mixins.ListModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            user = self.request.user
            return Profile.objects.filter(user=user)
        except:
            return []

    def retrieve(self, request, *args, **kwargs):
        instance = Profile.objects.filter(user=self.request.user).first()
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        instance = Profile.objects.filter(user=self.request.user).first()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return response.Response(ProfileSerializer(
            Profile.objects.filter(user=self.request.user).first()).data,
                                 status=status.HTTP_200_OK)

    @action(methods=["POST"], detail=False)
    def delete_photo(self, request, *args, **kwargs):
        instance = Profile.objects.filter(user=self.request.user).first()
        if instance.photo:
            if os.path.isfile(instance.photo.path):
                os.remove(instance.photo.path)
                instance.photo = None
                instance.save()
                return response.Response({"message": "Berhasil Menghapus File"}, status=status.HTTP_200_OK)
        return response.Response({"message": "Tidak Ada File Profile"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["DELETE"], detail=False)
    def delete_google_link(self, request, *args, **kwargs):
        instance = Profile.objects.filter(user=self.request.user).first()
        instance.google_id = None
        instance.google_data = None
        instance.save()

        return response.Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)
