"""
Authentication forms.
"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from ..models import User


class LoginForm(AuthenticationForm):
    """Login form with email instead of username."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "autofocus": True,
            "placeholder": "you@example.com",
        }),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Your password",
        }),
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        label="Remember me",
    )

    error_messages = {
        "invalid_login": "Invalid email or password.",
        "inactive": "This account is inactive.",
        "locked": "This account has been locked due to too many failed attempts.",
    }

    def clean(self):
        email = self.cleaned_data.get("username", "").lower().strip()
        password = self.cleaned_data.get("password")

        if email and password:
            # Check if user exists and is locked
            try:
                user = User.objects.get(email=email)
                if user.status == User.Status.LOCKED:
                    raise forms.ValidationError(
                        self.error_messages["locked"],
                        code="locked",
                    )
            except User.DoesNotExist:
                pass

            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password,
            )

            if self.user_cache is None:
                # Record failed attempt
                try:
                    user = User.objects.get(email=email)
                    user.record_failed_login()
                except User.DoesNotExist:
                    pass

                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class RegisterForm(UserCreationForm):
    """Registration form."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "autofocus": True,
            "placeholder": "you@example.com",
        }),
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={
            "placeholder": "John",
        }),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={
            "placeholder": "Doe",
        }),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Create a strong password",
        }),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm your password",
        }),
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service and Privacy Policy",
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.status = User.Status.PENDING
        if commit:
            user.save()
        return user
