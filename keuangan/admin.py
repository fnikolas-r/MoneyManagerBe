from django.contrib import admin
from .models import  UtangPiutang,Transaksi,Kategori,Rekening

# Register your models here.
admin.site.register(UtangPiutang)
admin.site.register(Transaksi)
admin.site.register(Kategori)
admin.site.register(Rekening)