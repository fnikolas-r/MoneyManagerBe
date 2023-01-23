from django.shortcuts import render
from rest_framework import viewsets,response,generics,status
from .serializer import RekeningSerializer
from .auth_serializer import RegisterSerializer
from keuangan.models import Rekening
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.contrib.auth.models import User


# Create your views here.

class RekeningViewSet(viewsets.ModelViewSet):
    serializer_class = RekeningSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        try:
            user = self.request.user
            return Rekening.objects.filter(user=user)
        except:
            return []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return response.Response({"message"})

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer