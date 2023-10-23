from django import forms
from django.forms import TextInput,validators

from .models import User

class PasswordChangeForm(forms.form):
    Oldpassword = forms.NumberInput(
        widget=TextInput(attrs={"class": "form-control", "name": "Oldpassword", "placeholder": "Oldpassword", "required": "required", "autocomplete": "off"}),
    )
    new_password = forms.NumberInput(

        label="Password",
        widget=TextInput(attrs={"class": "form-control", "name": "password1", "type": "password", "placeholder": "Password must be 4 charecters", "required": "required", "autocomplete": "off"}),
    )
    new_password1 = forms.NumberInput(

        label="Confirm Password",
        widget=TextInput(attrs={"class": "form-control", "name": "password2", "type": "password", "placeholder": "Confirm Password", "required": "required", "autocomplete": "off"}),
    )

    class Meta:
        model = User
        fields = ("Oldpassword", "new_password", "new_password1")
