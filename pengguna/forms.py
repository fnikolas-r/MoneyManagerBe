from django import  forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserCreate(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1","password2"
        )

    def save(self,commit=True):
        user = super(UserCreate,self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user