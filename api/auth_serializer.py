import json
import pathlib

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from pengguna.models import Profile
from keuangan.models import Kategori
from django.conf import settings

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    bio = serializers.CharField(source='profile.bio')
    photo = serializers.ImageField(source='profile.photo')

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name','bio','photo')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if (not self.partial) and attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        user.set_password(validated_data['password'])

        with open(str(pathlib.Path(__file__).parent.resolve()) + '\\default_category.json') as file:
            data: list = json.load(file)

            for kat in data:
                print(kat['name'])
                kat_obj = Kategori.objects.create(
                    user=user,
                    name=kat['name'],
                    icon=kat['icon'],
                    jenis= kat.get("jenis")
                )
                kat_obj.save()
        user.save()
        return user

    def update(self, instance:User, validated_data):
        instance = super(UserSerializer,self).update(instance, validated_data)
        instance.save()
        return instance

class LoginSerializer(TokenObtainPairSerializer):
    def to_representation(self, instance):
        data = super(LoginSerializer, self).to_representation(instance)
        print(data)
        data.update({'username': self.user.username})
        data.update({'first_name': self.user.first_name})
        data.update({'last_name': self.user.last_name})
        data.update({'email': self.user.email})
        return data

class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.CharField(source='user.email')
    username = serializers.CharField(source='user.username')
    user_id = serializers.UUIDField(source='user.id')

    class Meta:
        model = Profile
        exclude = ("user","google_id","id")

    def update(self, instance:Profile, validated_data):
        user_data = validated_data.get("user")
        user = User.objects.filter(id=instance.user.id).first()
        if user_data:

            user.email = user_data.get("email", instance.user.email)
            user.first_name = user_data.get("first_name", instance.user.first_name)
            user.last_name = user_data.get("last_name", instance.user.last_name)
            user.username = user_data.get("username", instance.user.username)
            user.save()
        instance.bio = validated_data.get("bio",instance.bio)
        instance.photo = validated_data.get("photo",instance.photo)
        instance.save()

        return Profile.objects.filter(user=user).first()

    def to_representation(self, instance):
        rep = super(ProfileSerializer,self).to_representation(instance)
        rep['photo'] = f"{settings.MEDIA_URL}{instance.photo}" if instance.photo else None
        return rep