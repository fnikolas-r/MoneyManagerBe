from django.db import models
from django.contrib.auth.models import  User
from django.utils import timezone
import uuid

# SOME CONSTANT
TIPE = (
    (1,"Pendapatan"),
    (-1,"Pengeluaran"),
)

TIPE_UTANG_PIUTANG = (
    ("U","Utang"),
    ("P","Piutang"),
)
# Create your models here.

class Akun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama = models.CharField(max_length=50,null=False,blank=False)
    isHidden = models.BooleanField(default=False)
    tanggal_dibuat = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    saldo_awal = models.PositiveBigIntegerField(null=False,default=0,blank=False)

    def __str__(self):
        return self.nama

class Kategori(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama = models.CharField(max_length=50,null=False,blank=False)
    parent = models.ForeignKey('self',null=True, on_delete=models.SET_NULL)

class Transfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keterangan = models.CharField(max_length=100,null=True,blank=True)
    tanngal = models.DateTimeField(auto_now_add=True)



class UtangPiutang(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    jatuh_tempo = models.DateTimeField(null=False, blank=False, default=timezone.now)
    pelaku = models.CharField(max_length=30, null=True,
                              blank=True)  # Penerima atau pemberi duit, bisa orang atau organisasi
    tipe = models.CharField(max_length=1,null=False,choices=TIPE_UTANG_PIUTANG)
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True)
    nominal = models.PositiveBigIntegerField(null=False, default=0)
    user = models.ForeignKey(User, models.CASCADE)
    isLunas = models.BooleanField(default=False,null=False,blank=False)


class Transaksi(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pelaku = models.CharField(max_length=30, null=True, blank=True) #Penerima atau pemberi duit, bisa orang atau organisasi
    nama_transaksi = models.CharField(max_length=50, null=False, blank=False)
    harga = models.PositiveBigIntegerField(null=False, blank=False)
    akun = models.ForeignKey(Akun, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(null=False, default=1)
    tipe = models.IntegerField(choices=TIPE)
    tanggal = models.DateTimeField(default=timezone.now, null=False, blank=False)
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pelunasan_utangpiutang = models.ForeignKey(UtangPiutang, on_delete=models.CASCADE,null=True)
    transfer_id = models.ForeignKey(Transfer, on_delete=models.CASCADE,null=True)


    def __str__(self):
        return self.nama_transaksi