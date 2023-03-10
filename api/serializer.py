from rest_framework.validators import ValidationError
from django.db.models.functions import Coalesce
from django.db.models import F,Sum,Value
from rest_framework import serializers
from rest_framework.validators import ValidationError

from keuangan.models import Rekening, Kategori, Transaksi, UtangPiutang, Transfer


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

    # def validate_name(self, value):
    #     user = self.context['request'].user
    #     queryset = Rekening.objects.filter(user=user)
    #     if queryset.filter(name=value).exists():
    #         raise serializers.ValidationError("Nama tersebut telah ada")
    #     return value

    def create(self, validated_data):

        rek_new : Rekening = super(RekeningSerializer,self).create(validated_data)
        if validated_data["initial_deposit"] >0:

            tr = Transaksi(
                trc_type=1,
                pelaku="Initial Deposit",
                trc_name=f"Initial Deposit rek {rek_new.name}",
                price=validated_data["initial_deposit"],
                rekening=rek_new,
                trc_date=rek_new.date_created,
                kategori=None,
                user=self.context['request'].user,
                is_protected= True
            )
            tr.save()

        return rek_new

    def update(self, instance, validated_data):

        rek : Rekening = super(RekeningSerializer,self).update(instance,validated_data)

        first_trc = Transaksi.objects.filter(rekening=rek,trc_date=rek.date_created,user=rek.user).first()
        first_trc.price = validated_data["initial_deposit"]
        first_trc.save()

        return rek




class TransaksiSummarySerializer(serializers.Serializer):
    rekening = serializers.UUIDField()
    total = serializers.IntegerField()
    name = serializers.CharField(max_length=50)
    latest_trc = serializers.DateTimeField()
    first_trc = serializers.DateTimeField()
    icon = serializers.CharField(max_length=30)
    rekening_hidden = serializers.BooleanField(read_only=True)


class TransaksiSerializer(serializers.ModelSerializer):
    id_transfer = serializers.UUIDField(read_only=True)
    id_utang_piutang = serializers.UUIDField(read_only=True)
    is_protected = serializers.BooleanField(read_only=True,required=False)
    rekeneing_id = serializers.UUIDField(read_only=True)
    kategori_id = serializers.UUIDField(read_only=True)
    rekening_hidden = serializers.BooleanField(read_only=True,required=False)

    class Meta:
        model = Transaksi
        exclude = ["user"]



    def to_representation(self, instance:Transaksi):
        rep = super(TransaksiSerializer, self).to_representation(instance)
        rep['rekening'] = instance.rekening.name
        rep['rekening_hidden'] = instance.rekening.is_hidden
        rep['rekening_id'] = instance.rekening.id
        rep['kategori'] = instance.kategori.name if instance.kategori else None
        rep['id_transfer'] = instance.id_transfer.id if instance.id_transfer else None
        rep['id_utang_piutang'] = instance.id_utang_piutang.id if instance.id_utang_piutang else None
        rep['kategori_id'] = instance.kategori.id if instance.kategori else None
        rep["trc_date"] = instance.trc_date.strftime("%Y-%m-%dT%H:%M")
        return rep

    def update(self, instance, validated_data):

        if instance.is_protected:
            raise ValidationError("Transaksi Tidak Dapat Diubah")
        instance = super(TransaksiSerializer,self).update(instance,validated_data)
        return instance


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Kategori
        exclude = ["user"]



class UtangPiutangSerializer(serializers.ModelSerializer):
    rekening_id = serializers.UUIDField(read_only=True)
    is_done = serializers.BooleanField(read_only=True)
    class Meta:
        model = UtangPiutang
        exclude = ["user"]

    def validate(self, attrs):

        # Validator rekening balance
        rekening_balance_validator(self.context, attrs["nominal"], attrs["rekening"])

        return attrs




    def create(self, validated_data):

        up : UtangPiutang = super(UtangPiutangSerializer,self).create(validated_data)
        pelaku = validated_data['person_in_charge']


        tr = Transaksi(
            trc_type=1 if up.type == 'U' else -1,
            pelaku=pelaku,
            trc_name=f"{'Utang dari' if up.type =='U' else 'Piutang ke'} {up.person_in_charge} ket:{validated_data['keterangan']}",
            price=validated_data["nominal"],
            rekening=up.rekening,
            trc_date=validated_data["tgl_transaksi"],
            kategori=None,
            user=self.context['request'].user,
            id_utang_piutang=up
        )
        tr.save()

        return up


    # NOTE: Untuk data maka ganti namanya
    def update(self, instance : UtangPiutang, validated_data):
        trc_type_changed = instance.type != validated_data["type"]

        instance = super(UtangPiutangSerializer,self).update(instance,validated_data)


        if(trc_type_changed):
            # Utang Jadi Piutang
            # Transaksi Pendapatan jadi pengeluaran
            for trc in Transaksi.objects.filter(id_utang_piutang=instance).all():
                trc.trc_type = -1 if trc.trc_type == 1 else 1
                trc.name = f"{'Utang' if instance.type=='P' else 'Piutang'} -ket:{validated_data['keterangan']}"
                trc.save()

        for trc in Transaksi.objects.filter(id_utang_piutang=instance).all():
            trc.pelaku = validated_data['person_in_charge']
            trc.date = validated_data["tgl_transaksi"]
            trc.rekening = validated_data["rekening"]
            trc.price = validated_data["nominal"]
            trc.save()


        return instance

    def to_representation(self, instance:UtangPiutang):
        rep = super(UtangPiutangSerializer, self).to_representation(instance)
        rep['rekening'] = instance.rekening.name
        rep['rekening_id'] = instance.rekening.id
        rep["tgl_transaksi"] = instance.tgl_transaksi.strftime("%Y-%m-%dT%H:%M")
        rep["due_date"] = instance.due_date.strftime("%Y-%m-%dT%H:%M")
        return rep



class RekeningStatsSerializer(serializers.Serializer):
    balance = serializers.FloatField()
    max_income = TransaksiSerializer()
    min_income = TransaksiSerializer()
    avg = serializers.FloatField()
    median = serializers.FloatField()

class TransferSerializer(serializers.ModelSerializer):
    from_account_id = serializers.UUIDField(read_only=True)
    to_account_id = serializers.UUIDField(read_only=True)
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

    def to_representation(self, instance:Transfer):
        rep = super(TransferSerializer, self).to_representation(instance)
        rep['from_account'] = instance.from_account.name
        rep['from_account_id'] = instance.from_account.id
        rep['to_account'] = instance.to_account.name
        rep['to_account_id'] = instance.to_account.id
        rep["tgl_transfer"] = instance.tgl_transfer.strftime("%Y-%m-%dT%H:%M")
        return rep