from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


# Create your views here.

def homeview(request):
    return render(request,'build/index.html')