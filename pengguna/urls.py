from django.urls import path,include
from django.contrib.auth import views
from .views import register

urlpatterns = [
    path('login/',views.LoginView.as_view(template_name='login.html'),name='login'),
    path('register/', register, name='register'),

]