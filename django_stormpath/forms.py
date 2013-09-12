"""Example forms that can be used for CRUD actions in applications.
"""

from django import forms
from django.contrib.auth import get_user_model
from stormpath.client import Client
from stormpath.error import Error
from django.conf import settings


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

    def clean_password2(self):
        """Check if passwords match.
        """
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")

        if password != password2:
            msg = "Passwords don't match"
            raise forms.ValidationError(msg)

        return password2

    def clean_username(self):
        """Check if username exists on Stormpath.

        We don't want the form to validate if a user with the same username
        exists on Stormpath. We ignore the status of the local user because we
        delete ther user on save to keep in sync with Stormpath.
        """
        try:
            accounts = get_application().accounts.search({
                'username': self.cleaned_data['username']})
            if len(accounts):
                msg = "User with that username already exists."
                raise forms.ValidationError(msg)
        except Error as e:
            raise forms.ValidationError(str(e))
        return self.cleaned_data['username']

    def clean_email(self):
        """Check if email exists on Stormpath.

        The email address is unique across all Stormpath applications.
        The username is only unique within a Stormpath application.
        """
        try:
            accounts = get_application().accounts.search({
                'email': self.cleaned_data['email']})
            if len(accounts):
                msg = "User with that email already exists."
                raise forms.ValidationError(msg)
        except Error as e:
            raise forms.ValidationError(str(e))
        return self.cleaned_data['email']

    def save(self, commit=False):
        """Create Stormpath user.

        Creates the Stormpath user and local user. Because the form validated,
        which means the user doesn't exist on Stormpath, we delete the local
        user without checking. It's important to set the url of the user.
        """
        data = self.cleaned_data
        stormpath_data = {}

        stormpath_data['username'] = data['username']
        stormpath_data['given_name'] = data['first_name']
        stormpath_data['surname'] = data['last_name']
        stormpath_data['email'] = data['email']
        stormpath_data['password'] = data['password']

        self.account = get_application().accounts.create(stormpath_data)
        get_user_model().objects.filter(username=data['username']).delete()
        user = super(UserCreateForm, self).save(commit=False)
        user.url = self.account.href
        user.password = "STORMPATH"
        user.save()


class UserUpdateForm(forms.ModelForm):
    """Update Stormpath user form.

    The form must have the instance object of the user set in order to read
    the url of the Stormpath user.
    """

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")

    def save(self):
        """Update user information.
        """
        data = self.cleaned_data
        self.account = get_client().accounts.get(self.instance.url)
        self.account.given_name = data['first_name']
        self.account.surname = data['last_name']
        self.account.email = data['email']
        self.account.save()


class PasswordResetEmailForm(forms.Form):
    """Form for password reset email.
    """

    email = forms.CharField(max_length=255)

    def clean(self):
        try:
            self.cleaned_data['email']
            return self.cleaned_data
        except KeyError:
            raise forms.ValidationError("Please provide an email address.")

    def save(self):
        get_application().send_password_reset_email(self.cleaned_data['email'])


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
        account = get_application().verify_password_reset_token(token)
        account.password = self.cleaned_data['new_password1']
        account.save()
