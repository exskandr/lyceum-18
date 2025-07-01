from django import forms
from .models import User, Profile # Імпортуємо ваші моделі


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        # Поля, які користувач може редагувати (залежить від ролі, але це базові)
        fields = ['first_name', 'last_name', 'phone_number']
        # Якщо ви хочете дозволити зміну email або username, додайте їх сюди.
        # Але зазвичай email та username не змінюються користувачами без особливих дозволів.


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        # Всі поля профілю, які можуть бути редаговані
        fields = [
            'photo', 'patronymic', 'year_of_birth', 'description',
            'admission_year', 'start_work_year', 'position', 'achievements'
        ]
        # Ви можете додати 'widgets' для кращого контролю над HTML-елементами,
        # наприклад, для textarea:
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'achievements': forms.Textarea(attrs={'rows': 6}),
        }