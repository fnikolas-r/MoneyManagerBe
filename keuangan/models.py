import uuid

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

# SOME CONSTANT
TIPE = (
    (1,"Kredit"),
    (-1,"Debit"),
)

#Uang masuk kredit, uang keluar debit

TIPE_UTANG_PIUTANG = (
    ("U","Utang"),
    ("P","Piutang"),
)
# Create your models here.

class Rekening(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    is_hidden = models.BooleanField(default=False)
    initial_deposit = models.PositiveBigIntegerField(null=False, default=0, blank=False,validators=[
        MinValueValidator(0)
    ])
    trf_minimum = models.PositiveBigIntegerField(null=True,blank=True)
    is_pinned = models.BooleanField(null=True,blank=True,default=False)
    icon = models.CharField(max_length=30,null=True,blank=True)

    def __str__(self):
        return self.name

class Kategori(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    icon = models.TextField(null=True,blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    jenis = models.IntegerField(choices=TIPE,null=True)

    def __str__(self):
        return self.name

# Todo: Atur Normalisasi UtangPiutang ini
class UtangPiutang(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    due_date = models.DateTimeField(null=True, blank=True, default=timezone.now)
    person_in_charge = models.CharField(max_length=30, null=True,
                                        blank=True)  # Penerima atau pemberi duit, bisa orang atau organisasi
    type = models.CharField(max_length=1, null=False, choices=TIPE_UTANG_PIUTANG)
    tgl_transaksi = models.DateTimeField(default=timezone.now)
    nominal = models.PositiveBigIntegerField(null=False, default=0,validators=[
        MinValueValidator(0)
    ])
    user = models.ForeignKey(User, models.CASCADE)
    rekening = models.ForeignKey(Rekening,models.CASCADE)
    is_done = models.BooleanField(default=False, null=False, blank=False)
    keterangan = models.CharField(max_length=50,null=True,blank=True)

# Todo: Atur dan normalisasi data ini
class Transfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_account = models.ForeignKey(Rekening,on_delete=models.CASCADE,related_name='from_account')
    to_account  = models.ForeignKey(Rekening,on_delete=models.CASCADE,related_name='to_account')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    keterangan = models.CharField(max_length=10,null=True)
    tgl_transfer = models.DateTimeField(default=timezone.now)
    nominal = models.PositiveBigIntegerField(validators=[
        MinValueValidator(0)
    ])

    def __str__(self):
        return f"{self.from_account.name} --> {self.to_account.name} ({self.nominal})"

# TODO:Tambahkan Planning & Limit Saldo Nantinya

class TransaksiAbstract(models.Model):
    trc_name = models.CharField(max_length=100, null=False, blank=False)
    price = models.PositiveBigIntegerField(null=False, blank=False,validators=[MinValueValidator(0)])
    rekening = models.ForeignKey(Rekening, on_delete=models.CASCADE)
    trc_type = models.IntegerField(choices=TIPE)
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        abstract = True
class Transaksi(TransaksiAbstract):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_utang_piutang = models.ForeignKey(UtangPiutang, on_delete=models.CASCADE, null=True)
    id_transfer = models.ForeignKey(Transfer,on_delete=models.CASCADE,null=True,blank=True)
    trc_date = models.DateTimeField(default=timezone.now, null=False, blank=False)
    pelaku = models.CharField(max_length=30, null=True, blank=True) #Penerima atau pemberi duit, bisa orang atau organisasi
    is_protected = models.BooleanField(default=False)

    def __str__(self):
        return self.trc_name