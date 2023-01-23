from django.db import models
from django.contrib.auth.models import  User
from django.utils import timezone
import uuid

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
    initial_deposit = models.PositiveBigIntegerField(null=False, default=0, blank=False)

    def __str__(self):
        return self.name

class Kategori(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    icon = models.TextField()
    id_user = models.ForeignKey(User,on_delete=models.CASCADE)

class UtangPiutang(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    due_date = models.DateTimeField(null=False, blank=False, default=timezone.now)
    person_in_charge = models.CharField(max_length=30, null=True,
                                        blank=True)  # Penerima atau pemberi duit, bisa orang atau organisasi
    type = models.CharField(max_length=1, null=False, choices=TIPE_UTANG_PIUTANG)
    nominal = models.PositiveBigIntegerField(null=False, default=0)
    user = models.ForeignKey(User, models.CASCADE)
    is_done = models.BooleanField(default=False, null=False, blank=False)

class Transaksi(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pelaku = models.CharField(max_length=30, null=True, blank=True) #Penerima atau pemberi duit, bisa orang atau organisasi
    trc_name = models.CharField(max_length=50, null=False, blank=False)
    price = models.PositiveBigIntegerField(null=False, blank=False)
    rekening = models.ForeignKey(Rekening, on_delete=models.CASCADE)
    trc_type = models.IntegerField(choices=TIPE)
    trc_date = models.DateTimeField(default=timezone.now, null=False, blank=False)
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pelunasan_utangpiutang = models.ForeignKey(UtangPiutang, on_delete=models.CASCADE,null=True)
    isTransfer = models.BooleanField(default=False,null=True,blank=True)


    def __str__(self):
        return self.trc_name