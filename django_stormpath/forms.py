"""Example forms that can be used for CRUD actions in applications.
"""

from django import forms
from django.contrib.auth import get_user_model
from stormpath.client import Client
from stormpath.error import Error
from django.conf import settings
from django.forms.forms import NON_FIELD_ERRORS


CLIENT = None
APPLICATION = None


def get_client():
    global CLIENT
    if not CLIENT:
        CLIENT = Client(api_key={'id': settings.STORMPATH_ID,
            'secret': settings.STORMPATH_SECRET})

    return CLIENT


def get_application():
    global APPLICATION
    if not APPLICATION:
        APPLICATION = get_client().applications.get(
            settings.STORMPATH_APPLICATION)

    return APPLICATION


class UserCreateForm(forms.ModelForm):
    """User creation form.

    Creates a new user on Stormpath and locally.
    """

    password = forms.CharField(label='Password',
        widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation',
        widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ("username", "email",
            "first_name", "last_name", "password", "password2")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        accounts = get_application().accounts.search({
            'username': username})
        if not len(accounts):
            get_user_model().objects.filter(username=username).delete()
        return username

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            msg = "Passwords don't match"
            raise forms.ValidationError(msg)
        return password2

    def clean(self):
        data = self.cleaned_data
        stormpath_data = {}

        stormpath_data['username'] = data['username']
        stormpath_data['given_name'] = data['first_name']
        stormpath_data['surname'] = data['last_name']
        stormpath_data['email'] = data['email']
        stormpath_data['password'] = data['password']

        try:
            self.account = get_application().accounts.create(stormpath_data)
        except Error as e:
            raise forms.ValidationError(str(e))
        return data


class UserUpdateForm(forms.ModelForm):
    """Update Stormpath user form.
    """

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")

    def clean(self):
        data = self.cleaned_data
        try:
            self.account = get_client().accounts.get(self.instance.url)
            self.account.given_name = data['first_name']
            self.account.surname = data['last_name']
            self.account.email = data['email']
            self.account.save()
        except Error as e:
            raise forms.ValidationError(str(e))
        return data


class PasswordResetEmailForm(forms.Form):
    """Form for password reset email.
    """

    email = forms.CharField(max_length=255)

    def clean(self):
        try:
            get_application().send_password_reset_email(
                self.cleaned_data['email'])
        except Error as e:
            raise forms.ValidationError(str(e))
        return self.cleaned_data


class PasswordResetForm(forms.Form):
    """Form for new password input.
    """

    new_password1 = forms.CharField(label="New password",
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="New password confirmation",
                                    widget=forms.PasswordInput)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two passwords didn't match.")
        return password2

    def save(self, token):
        try:
            self.account = get_application().verify_password_reset_token(token)
            self.account.password = self.cleaned_data['new_password1']
            self.account.save()
        except Error as e:
            self._errors[NON_FIELD_ERRORS] = self.error_class([str(e)])
            return None
        return self.account
