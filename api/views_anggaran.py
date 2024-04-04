from django.db.models import Model
from rest_framework import viewsets, response, generics, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from api.serializer_anggaran import AnggaranSerializer, LimitAnggaranSerializer, TabunganInvestasiSerializer, \
    DaftarBelanjaSerializer
from planning.models import KelompokAnggaran, AnggaranPerKategori, TabunganDanInvestasi, DaftarBelanja
from keuangan.models import Transaksi,Rekening


class AnggaranBaseViewSet(viewsets.ModelViewSet):

    def __init__(self, model, custom_order=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.myModel: Model = model
        self.custom_order = custom_order

    def get_queryset(self):
        try:
            user = self.request.user
            if self.custom_order:
                return self.myModel.objects.filter(kelompok_anggaran__user=user).order_by(self.custom_order)

            return self.myModel.objects.filter(kelompok_anggaran__user=user)
        except:
            return []

class AnggaranViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AnggaranSerializer

    def get_queryset(self):
        try:
            user = self.request.user
            return KelompokAnggaran.objects.filter(user=user)
        except:
            return []

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return response.Response({"message"})

class LimitAnggaranViewSet(AnggaranBaseViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = LimitAnggaranSerializer

    def __init__(self,  *args, **kwargs):
        super().__init__(AnggaranPerKategori, *args, **kwargs)

class TabunganInvestasiViewSet(AnggaranBaseViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = TabunganInvestasiSerializer

    def __init__(self,  *args, **kwargs):
        super().__init__(TabunganDanInvestasi, *args, **kwargs)

class DaftarBelanjaViewSet(AnggaranBaseViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DaftarBelanjaSerializer

    def __init__(self,  *args, **kwargs):
        super().__init__(DaftarBelanja, *args, **kwargs)

    @action(methods=["POST"],detail=True)

    def set_done(self, request, pk=None):

        buylist : DaftarBelanja  = DaftarBelanja.objects.filter(pk=pk).first()
        if not buylist.is_done:
            trc = Transaksi(
                        trc_type=-1,
                        pelaku=request.data["penerima"],
                        trc_name=buylist.trc_name,
                        price=buylist.price,
                        rekening=Rekening.objects.filter(pk=request.data['rekening']).first(),
                        kategori=buylist.kategori,
                        user=self.request.user,
                    )
            trc.save()
            buylist.transaksi = trc
        else:
            Transaksi.objects.filter(pk=buylist.transaksi.id).first().delete()
            buylist.transaksi = None
            buylist.save()

        buylist.is_done = not buylist.is_done
        buylist.save()
        return response.Response(self.serializer_class(buylist).data, status.HTTP_200_OK)