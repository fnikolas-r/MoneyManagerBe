import datetime

from rest_framework import serializers
from django.db.models import Sum,F,Value
from keuangan.models import Rekening, Kategori, Transaksi, UtangPiutang, Transfer
from django.db.models.functions import  Coalesce

def rekening_balance_validator(context,value,rekening_id,message="Nominal Melebihi Total Saldo"):
    transaksi = Transaksi.objects.filter(user=context["request"].user).filter(rekening=rekening_id)
    transaksi = transaksi.annotate(hasil=F('price') * F('trc_type')).aggregate(balance=Coalesce(Sum('hasil'), Value(0)))
    rek = rekening_id.initial_deposit

    if (rek + transaksi.get("balance")) < value:
        raise serializers.ValidationError(f"{message}")

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

class TransaksiSerializer(serializers.ModelSerializer):
    id_transfer = serializers.UUIDField(read_only=True)
    id_utang_piutang = serializers.UUIDField(read_only=True)

    class Meta:
        model = Transaksi
        exclude = ["user"]

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Kategori
        exclude = ["user"]

class UtangPiutangSerializer(serializers.ModelSerializer):

    class Meta:
        model = UtangPiutang
        exclude = ["user"]

    def validate(self, attrs):

        # Validator rekening balance
        rekening_balance_validator(self.context, attrs["nominal"], attrs["rekening"])

        # Validator isDone tidak boleh post
        if self.context['request'].method == "POST" and attrs["is_done"]:
            raise  serializers.ValidationError("Cannot set is_done while creating Utang Piutang")

        return attrs



    def create(self, validated_data):

        up : UtangPiutang = super(UtangPiutangSerializer,self).create(validated_data)
        pelaku = validated_data['person_in_charge']

        if(up.type=="U"):
            trc_type = 1
            tipe = "Utang"
        else:
            trc_type = -1
            tipe = "Piutang"

        tr = Transaksi(
            trc_type=trc_type,
            pelaku=pelaku,
            trc_name=f"*{tipe} | {validated_data['keterangan']}",
            price=validated_data["nominal"],
            rekening=up.rekening,
            trc_date=validated_data["tgl_transaksi"],
            kategori=None,
            user=self.context['request'].user,
            id_utang_piutang=up
        )
        tr.save()

        return up

    # TODO: MAKE IT SIMPLER
    def update(self, instance, validated_data):

        pelaku = validated_data['person_in_charge']

        if(instance.type=="U"):
            trc_type = 1
        else:
            trc_type = -1

        for tr in Transaksi.objects.filter(id_utang_piutang=instance).all():
            tr.delete()

        tr = Transaksi(
            trc_type=trc_type,
            pelaku=pelaku,
            trc_name=f"({instance.type}) {validated_data['keterangan']}",
            price=validated_data["nominal"],
            rekening=instance.rekening,
            trc_date=validated_data["tgl_transaksi"],
            kategori=None,
            user=self.context['request'].user,
            id_utang_piutang=instance
        )
        tr.save()

        if validated_data["is_done"]:
            tr = Transaksi(
                trc_type=trc_type*-1,
                pelaku=pelaku+" |LUNAS",
                trc_name=f"({instance.type}) {validated_data['keterangan']}",
                price=validated_data["nominal"],
                rekening=instance.rekening,
                trc_date=datetime.datetime.now(),
                kategori=None,
                user=self.context['request'].user,
                id_utang_piutang=instance
            )
            tr.save()

        instance: UtangPiutang = super(UtangPiutangSerializer, self).update(instance, validated_data)
        return instance




class RekeningStatsSerializer(serializers.Serializer):
    balance = serializers.FloatField()
    max_income = TransaksiSerializer()
    min_income = TransaksiSerializer()
    avg = serializers.FloatField()
    median = serializers.FloatField()

class TransferSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transfer
        exclude = ["user"]

    def validate(self, attrs):
        super(TransferSerializer,self).validate(attrs)

        rekening_balance_validator(self.context,attrs["nominal"],attrs["from_account"])

        if attrs["from_account"] == attrs["to_account"]:
            raise serializers.ValidationError("Akun yang di tuju tidak boleh sama")
        return attrs

    def create(self, validated_data):
        from_account = validated_data['from_account']
        to_account = validated_data['to_account']
        trf = Transfer(
            from_account=from_account,
            to_account=to_account,
            user = self.context['request'].user,
            keterangan = validated_data['keterangan'],
            tgl_transfer = validated_data["tgl_transfer"],
            nominal = validated_data["nominal"],
        )
        trf.save()
        for trc in [[-1,"ke",to_account,from_account],[1,"dari",from_account,to_account]]:
            tr = Transaksi(
                trc_type=trc[0],
                pelaku=f"Transfer | {validated_data['keterangan']}",
                trc_name=f"Transfer {trc[1]} {trc[2].name}",
                price=validated_data["nominal"],
                rekening=trc[3],
                trc_date=validated_data["tgl_transfer"],
                kategori=None,
                user = self.context['request'].user,
                id_transfer = trf
            )
            tr.save()

        return trf

    def update(self, instance, validated_data):
        from_account = validated_data['from_account']
        to_account = validated_data['to_account']

        for tr in Transaksi.objects.filter(id_transfer=instance).all():
            tr.delete()

        for trc in [[-1,"ke",to_account,from_account],[1,"dari",from_account,to_account]]:
            tr = Transaksi(
                trc_type=trc[0],
                pelaku=f"Transfer | {validated_data['keterangan']}",
                trc_name=f"Transfer {trc[1]} {trc[2].name}",
                price=validated_data["nominal"],
                rekening=trc[3],
                trc_date=validated_data["tgl_transfer"],
                kategori=None,
                user = self.context['request'].user,
                id_transfer = instance
            )
            tr.save()

        instance = super(TransferSerializer, self).update(instance, validated_data)
        instance.save()
        return  instance