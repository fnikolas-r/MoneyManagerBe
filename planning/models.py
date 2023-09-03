import uuid
from django.utils import timezone
from django.db import models
from keuangan.models import Kategori,Rekening,TransaksiAbstract
from django.contrib.auth.models import User

# Create your models here.
class Anggaran(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    saldo_awal = models.PositiveBigIntegerField(null=False, default=0)
    tanggal_mulai = models.DateTimeField(null=False,default=timezone.now)
    tanggal_selesai = models.DateTimeField(null=False,default=timezone.now)
    user = models.ForeignKey(User,on_delete=models.CASCADE)


class AnggaranPerKategori(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nominal = models.PositiveBigIntegerField(null=False,default=0)
    kategori = models.ForeignKey(Kategori,on_delete=models.CASCADE)
    anggaran = models.ForeignKey(Anggaran,on_delete=models.CASCADE,related_name='anggaran_by_kategori')

class AlokasiDana(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nominal = models.PositiveBigIntegerField(null=False,default=0)
    is_tabungan = models.BooleanField(null=False,default=False)
    rekening = models.ForeignKey(Rekening, on_delete=models.CASCADE)
    anggaran = models.ForeignKey(Anggaran,on_delete=models.CASCADE,related_name='alokasi_dana')



class DaftarBelanja(TransaksiAbstract):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anggaran = models.ForeignKey(Anggaran,on_delete=models.CASCADE,related_name='daftar_belanja',null=True)
    is_done = models.BooleanField(default=False)

