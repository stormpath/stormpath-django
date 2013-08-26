from django import forms
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from stormpath.client import Client
from stormpath.error import Error
from django.conf import settings
from django.forms.forms import NON_FIELD_ERRORS
from django.forms import ValidationError

class HorizontalRadioRenderer(forms.RadioSelect.renderer):
  def render(self):
    return mark_safe(u'\n'.join(u'%s\n' % w for w in self))

CLIENT = Client(api_key={'id': settings.STORMPATH_ID,
    'secret': settings.STORMPATH_SECRET})
APPLICATION = CLIENT.applications.get(settings.STORMPATH_APPLICATION)


class UserCreateForm(forms.ModelForm):

    ACC_CHOICES = (('Admins', 'Administrator',),
        ('Premiums', 'Premium',),
        ('Basics', 'Basic'))

    password = forms.CharField(label='Password',
        widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation',
        widget=forms.PasswordInput)
    account_type = forms.ChoiceField(
        widget=forms.RadioSelect(renderer=HorizontalRadioRenderer),
        choices=ACC_CHOICES,
        initial='Basics')

    class Meta:
        model = get_user_model()
        fields = ("username", "email",
            "first_name", "last_name", "password", "password2",
            "account_type")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        accounts = APPLICATION.accounts.search({
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

    def save(self, commit=True):
        data = self.cleaned_data
        account_type = data['account_type']
        stormpath_data = {}

        stormpath_data['username'] = data['username']
        stormpath_data['given_name'] = data['first_name']
        stormpath_data['surname'] = data['last_name']
        stormpath_data['email'] = data['email']
        stormpath_data['password'] = data['password']

        try:
            account = APPLICATION.accounts.create(stormpath_data)
        except Error as e:
            self._errors[NON_FIELD_ERRORS] = self.error_class([e.message])
            raise ValidationError(e.message)

        if account_type == 'Admins':
            admin_group = CLIENT.groups.get(settings.STORMPATH_ADMINISTRATORS)
            account.add_group(admin_group)
            account.save()
        elif account_type == 'Premiums':
            premium_group = CLIENT.groups.get(settings.STORMPATH_PREMIUMS)
            account.add_group(premium_group)
            account.save()


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")

    def save(self):
        data = self.cleaned_data
        try:
            account = CLIENT.accounts.get(self.instance.url)
            account.given_name = data['first_name']
            account.surname = data['last_name']
            account.email = data['email']
            account.save()
        except Error as e:
            self._errors[NON_FIELD_ERRORS] = self.error_class([e.message])
            raise ValidationError(e.message)

        super(UserUpdateForm, self).save()


class PasswordResetEmailForm(forms.Form):
    email = forms.CharField(max_length=255)

    def save(self):
        try:
            APPLICATION.send_password_reset_email(self.cleaned_data['email'])
        except Error as e:
            self._errors[NON_FIELD_ERRORS] = self.error_class([e.message])
            raise ValidationError(e.message)


class PasswordResetForm(forms.Form):

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
            account = APPLICATION.verify_password_reset_token(token)
            account.password = self.cleaned_data['new_password1']
            account.save()
        except:
            message = "Invalid credentials!"
            self._errors[NON_FIELD_ERRORS] = self.error_class([message])
            raise ValidationError(message)
