"""Example forms that can be used for CRUD actions in applications.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from stormpath.error import Error

from .models import APPLICATION


class StormpathUserCreationForm(forms.ModelForm):
    """User creation form.

    Creates a new user on Stormpath and locally.
    """

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'given_name', 'surname', 'password1', 'password2')

    def clean_password2(self):
        """Check if passwords match and are valid."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        try:
            directory = APPLICATION.default_account_store_mapping.account_store
            directory.password_policy.strength.validate_password(password2)
        except ValueError as e:
            raise forms.ValidationError(str(e))

        if password1 != password2:
            msg = "Passwords don't match."
            raise forms.ValidationError(msg)

        return password2

    def clean_username(self):
        """Check if username exists on Stormpath.

        We don't want the form to validate if a user with the same username
        exists on Stormpath. We ignore the status of the local user because we
        delete ther user on save to keep in sync with Stormpath.
        """
        try:
            accounts = APPLICATION.accounts.search({'username': self.cleaned_data['username']})
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
            accounts = APPLICATION.accounts.search({'email': self.cleaned_data['email']})
            if len(accounts):
                msg = 'User with that email already exists.'
                raise forms.ValidationError(msg)
        except Error as e:
            raise forms.ValidationError(str(e))

        return self.cleaned_data['email']

    def save(self, commit=True):
        user = super(StormpathUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class StormpathUserChangeForm(forms.ModelForm):
    """Update Stormpath user form."""

    class Meta:
        model = get_user_model()
        exclude = ('password',)

    password = ReadOnlyPasswordHashField(help_text=('Passwords are not stored in the local database but only on Stormpath. You can change the password using <a href="password/">this form</a>.'))


class PasswordResetEmailForm(forms.Form):
    """Form for password reset email."""

    email = forms.CharField(max_length=255)

    def clean(self):
        try:
            self.cleaned_data['email']
            return self.cleaned_data
        except KeyError:
            raise forms.ValidationError('Please provide an email address.')

    def save(self):
        APPLICATION.send_password_reset_email(self.cleaned_data['email'])


class PasswordResetForm(forms.Form):
    """Form for new password input."""

    new_password1 = forms.CharField(label='New password', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='New password confirmation', widget=forms.PasswordInput)

    def clean_new_password2(self):
        """Check if passwords match and are valid."""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        try:
            directory = APPLICATION.default_account_store_mapping.account_store
            directory.password_policy.strength.validate_password(password2)
        except ValueError as e:
            raise forms.ValidationError(str(e))

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two passwords didn't match.")

        return password2

    def save(self, token):
        APPLICATION.reset_account_password(token, self.cleaned_data['new_password1'])
