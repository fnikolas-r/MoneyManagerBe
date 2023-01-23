from rest_framework import serializers,validators
from keuangan.models import Rekening,Kategori,Transaksi


class RekeningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rekening
        exclude = ["user"]

    def validate_name(self, value):
        user = self.context['request'].user
        queryset = Rekening.objects.filter(user=user)
        if queryset.filter(name=value).exists():
            raise serializers.ValidationError("Nama tersebut telah ada")
        return value





