from django import forms
from django.contrib.auth.models import User
from .models import Patient, PatientParameters

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, label='Логин')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')


class RegistrationForm(forms.Form):
    # БЕЗ поля role - автоматически будет patient
    username = forms.CharField(max_length=100, label='Логин')
    email = forms.EmailField(max_length=150, label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Подтверждение пароля')
    
    first_name = forms.CharField(max_length=100, label='Имя')
    last_name = forms.CharField(max_length=100, label='Фамилия')
    middle_name = forms.CharField(max_length=100, required=False, label='Отчество')
    
    birth_date = forms.DateField(
        label='Дата рождения',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    gender = forms.ChoiceField(
        choices=[('M', 'Мужской'), ('F', 'Женский')],
        required=False,
        label='Пол'
    )
    
    phone = forms.CharField(max_length=30, required=False, label='Телефон')
    weight_kg = forms.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        required=False, 
        label='Вес (кг)'
    )
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует')
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        
        return cleaned_data


class PatientParametersForm(forms.ModelForm):
    """Форма для редактирования всех параметров модели Ховорка"""
    
    class Meta:
        model = PatientParameters
        fields = [
            # Основные параметры переноса
            'glucose_transfer_rate',                    # k12
            'insulin_absorption_rate',                  # скорость абсорбции инсулина
            
            # Параметры деактивации (действия инсулина)
            'glucose_deactivation_distribution',        # распределение
            'glucose_deactivation_utilization',         # утилизация
            'glucose_deactivation_liver',               # печень
            
            # Параметры чувствительности к инсулину
            'insulin_absorption_coefficient',           # kb1
            'insulin_distribution_rate',                # kb2
            'insulin_effect_on_glucose_liver',          # kb3
            
            # Метаболические параметры
            'liver_glucose_production_rate',            # EGP0
            'glucose_consumption_rate',                 # F01
            
            # Объемы распределения
            'glucose_distribution_volume',              # VG
            'insulin_distribution_volume',              # VI
            
            # Параметры абсорбции
            'bioavailability',                          # AG
            'meal_absorption_time',                     # tau_D
            'insulin_absorption_time',                  # tau_s
            'insulin_elimination_rate',                 # ke
            
            # Начальные условия
            'initial_D1',
            'initial_D2',
            'initial_Q1',
            'initial_Q2',
            'initial_S1',
            'initial_S2',
            'initial_I',
            'initial_x1',
            'initial_x2',
            'initial_x3',
        ]
        
        labels = {
            # Основные параметры переноса
            'glucose_transfer_rate': 'Скорость переноса глюкозы (k12)',
            'insulin_absorption_rate': 'Скорость абсорбции инсулина',
            
            # Параметры деактивации
            'glucose_deactivation_distribution': 'Деактивация распределения глюкозы',
            'glucose_deactivation_utilization': 'Деактивация утилизации глюкозы',
            'glucose_deactivation_liver': 'Деактивация продукции печени',
            
            # Параметры чувствительности к инсулину
            'insulin_absorption_coefficient': 'Коэффициент абсорбции инсулина (kb1)',
            'insulin_distribution_rate': 'Скорость распределения инсулина (kb2)',
            'insulin_effect_on_glucose_liver': 'Влияние инсулина на печень (kb3)',
            
            # Метаболические параметры
            'liver_glucose_production_rate': 'Продукция глюкозы печенью (EGP0)',
            'glucose_consumption_rate': 'Потребление глюкозы ЦНС (F01)',
            
            # Объемы распределения
            'glucose_distribution_volume': 'Объем распределения глюкозы (VG)',
            'insulin_distribution_volume': 'Объем распределения инсулина (VI)',
            
            # Параметры абсорбции
            'bioavailability': 'Биодоступность пищи (AG)',
            'meal_absorption_time': 'Время абсорбции пищи (tau_D)',
            'insulin_absorption_time': 'Время абсорбции инсулина (tau_s)',
            'insulin_elimination_rate': 'Скорость выведения инсулина (ke)',
            
            # Начальные условия
            'initial_D1': 'Начальная глюкоза в желудке (D1, ммоль)',
            'initial_D2': 'Начальная глюкоза в кишечнике (D2, ммоль)',
            'initial_Q1': 'Начальная глюкоза в крови (Q1, ммоль)',
            'initial_Q2': 'Начальная глюкоза в тканях (Q2, ммоль)',
            'initial_S1': 'Начальный инсулин в депо 1 (S1, mU)',
            'initial_S2': 'Начальный инсулин в депо 2 (S2, mU)',
            'initial_I': 'Начальный инсулин в крови (I, mU/L)',
            'initial_x1': 'Начальное действие x1',
            'initial_x2': 'Начальное действие x2',
            'initial_x3': 'Начальное действие x3',
        }
        
        help_texts = {
            'glucose_transfer_rate': 'По умолчанию: 0.066 | 1/мин. Скорость переноса глюкозы между отсеками',
            'insulin_absorption_rate': 'По умолчанию: зависит от пациента | Скорость всасывания инсулина',
            'glucose_deactivation_distribution': 'По умолчанию: 0.006 | Влияет на распределение глюкозы',
            'glucose_deactivation_utilization': 'По умолчанию: 0.06 | Влияет на утилизацию глюкозы',
            'glucose_deactivation_liver': 'По умолчанию: 0.03 | Влияет на продукцию глюкозы печенью',
            'insulin_absorption_coefficient': 'По умолчанию: 0.000307 | L/(мЕд·мин)',
            'insulin_distribution_rate': 'По умолчанию: 0.0000492 | L/(мЕд·мин)',
            'insulin_effect_on_glucose_liver': 'По умолчанию: 0.0016 | L/(мЕд·мин)',
            'liver_glucose_production_rate': 'По умолчанию: 0.079 × вес | ммоль/мин',
            'glucose_consumption_rate': 'По умолчанию: 0.089 × вес | ммоль/мин',
            'glucose_distribution_volume': 'По умолчанию: 0.16 × вес | литры',
            'insulin_distribution_volume': 'По умолчанию: 0.12 × вес | литры',
            'bioavailability': 'По умолчанию: 0.8 | Доля усвоенных углеводов (0-1)',
            'meal_absorption_time': 'По умолчанию: 40 | минут. Время всасывания пищи',
            'insulin_absorption_time': 'По умолчанию: 55 | минут. Время действия инсулина',
            'insulin_elimination_rate': 'По умолчанию: 0.138 | 1/мин',
            'initial_D1': 'По умолчанию: 0 | Начало расчета',
            'initial_D2': 'По умолчанию: 0 | Начало расчета',
            'initial_Q1': 'По умолчанию: 65 | Количество глюкозы в крови',
            'initial_Q2': 'По умолчанию: 10 | Количество глюкозы в тканях',
            'initial_S1': 'По умолчанию: 0 | Инсулин в депо 1',
            'initial_S2': 'По умолчанию: 0 | Инсулин в депо 2',
            'initial_I': 'По умолчанию: 0 | Концентрация инсулина в крови',
            'initial_x1': 'По умолчанию: 0.0634 | Базальное действие на транспорт',
            'initial_x2': 'По умолчанию: 0.0005 | Базальное действие на утилизацию',
            'initial_x3': 'По умолчанию: 0.3138 | Базальное действие на продукцию',
        }
        
        widgets = {
            'glucose_transfer_rate': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'insulin_absorption_rate': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'glucose_deactivation_distribution': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'glucose_deactivation_utilization': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'glucose_deactivation_liver': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'insulin_absorption_coefficient': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'insulin_distribution_rate': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'insulin_effect_on_glucose_liver': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'liver_glucose_production_rate': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'glucose_consumption_rate': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'glucose_distribution_volume': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'insulin_distribution_volume': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'bioavailability': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'meal_absorption_time': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'insulin_absorption_time': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'insulin_elimination_rate': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'initial_D1': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'initial_D2': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'initial_Q1': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'initial_Q2': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'initial_S1': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'initial_S2': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'initial_I': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'initial_x1': forms.NumberInput(attrs={'step': '0.0001', 'class': 'form-control'}),
            'initial_x2': forms.NumberInput(attrs={'step': '0.0001', 'class': 'form-control'}),
            'initial_x3': forms.NumberInput(attrs={'step': '0.0001', 'class': 'form-control'}),
        }

class ChangeUserRoleForm(forms.Form):
    """Форма для изменения роли пользователя (только для суперпользователя)"""
    ROLE_CHOICES = [
        ('patient', 'Пациент'),
        ('doctor', 'Врач'),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Роль пользователя')
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['weight_kg']  # Только поле веса доступно для редактирования
        widgets = {
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '20',
                'max': '500'
            })
        }
        labels = {
            'weight_kg': 'Вес (кг)'
        }