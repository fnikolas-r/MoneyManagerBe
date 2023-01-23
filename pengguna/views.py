from django.shortcuts import render
from .forms import  UserCreate

# Create your views here.
def register(request):
    form = UserCreate()
    if request.method == "POST":
        form = UserCreate(request)
        if form.is_valid():
            form.save()

    return render(request, 'register.html',context={"form":form})
