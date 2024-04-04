import uuid
from django.utils import timezone
from django.db import models
from keuangan.models import Kategori,Rekening,TransaksiAbstract,Transaksi
from django.contrib.auth.models import User


# Create your models here.
class KelompokAnggaran(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    limit_awal = models.PositiveBigIntegerField(null=False, default=0)
    sumber_dana = models.ForeignKey(Transaksi,on_delete=models.SET_NULL,null=True,blank=True)
    tanggal_mulai = models.DateTimeField(null=False,default=timezone.now)
    tanggal_selesai = models.DateTimeField(null=False,default=timezone.now)
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tanggal_mulai.strftime('%Y-%m-%d')} \
        - {self.tanggal_selesai.strftime('%Y-%m-%d')} (Rp.{self.limit_awal})"
class AnggaranPerKategori(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nominal = models.PositiveBigIntegerField(null=False,default=0)
    kategori = models.ForeignKey(Kategori,on_delete=models.CASCADE)
    kelompok_anggaran = models.ForeignKey(KelompokAnggaran,on_delete=models.CASCADE,related_name='daftar_limit_anggaran',null=True)

class TabunganDanInvestasi(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nominal = models.PositiveBigIntegerField(null=False,default=0)
    jenis = models.TextField(max_length=2,choices=(("T","Tabungan"),("I","Investasi")),null=False)
    asal_rekening = models.ForeignKey(Rekening,on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False,null=False)
    kelompok_anggaran = models.ForeignKey(KelompokAnggaran,on_delete=models.CASCADE,null=True,related_name="daftar_tabungan_dan_investasi")

class DaftarBelanja(TransaksiAbstract):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deskripsi = models.TextField(max_length=100,null=True,blank=True)
    kelompok_anggaran = models.ForeignKey(KelompokAnggaran,on_delete=models.CASCADE,related_name="daftar_rencana_belanja")
    is_done = models.BooleanField(default=False,null=False,blank=False)
    transaksi = models.ForeignKey(Transaksi,on_delete=models.SET_NULL,null=True)