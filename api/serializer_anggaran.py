from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from planning.models import KelompokAnggaran,AnggaranPerKategori,TabunganDanInvestasi,DaftarBelanja


class LimitAnggaranSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnggaranPerKategori
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(queryset=AnggaranPerKategori.objects.all(),fields=['kelompok_anggaran','kategori'])
        ]

class TabunganInvestasiSerializer(serializers.ModelSerializer):
    class Meta:
        model = TabunganDanInvestasi
        fields = ("id","nominal","jenis","asal_rekening","kelompok_anggaran")
        validators = [
            UniqueTogetherValidator(queryset=TabunganDanInvestasi.objects.all(),fields=["jenis","asal_rekening","kelompok_anggaran"])
        ]

class DaftarBelanjaSerializer(serializers.ModelSerializer):
    is_done = serializers.BooleanField(read_only=True)
    class Meta:
        model = DaftarBelanja
        exclude = ["id"]

class AnggaranSerializer(serializers.ModelSerializer):
    daftar_rencana_belanja = DaftarBelanjaSerializer(read_only=True, many=True)
    daftar_limit_anggaran = LimitAnggaranSerializer(read_only=True,many=True)
    daftar_tabungan_dan_investasi = TabunganInvestasiSerializer(read_only=True,many=True)

    class Meta:
        model = KelompokAnggaran
        exclude = ["user"]
