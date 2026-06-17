from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime
import json
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt


from .forms import LoginForm, PatientParametersForm, PatientProfileForm, RegistrationForm
from .models import (
    Calculation, Charts, Doctor, GlucoseMeasurement, Patient, 
    FoodIntake, InsulinInjection, PatientHistory, PatientParameters, Roles, DoctorPatient
)
from .hovorka_model import HovorkaModel


def home(request):
    context = {}
    
    if request.user.is_authenticated:
        is_patient = hasattr(request.user, 'patient_profile')
        is_doctor = hasattr(request.user, 'doctor_profile')
        
        context['is_patient'] = is_patient
        context['is_doctor'] = is_doctor
        
        if is_patient:
            patient = request.user.patient_profile
            context['patient_id'] = patient.id
            context['patient_weight'] = patient.weight_kg
            context['first_name'] = patient.first_name
            context['last_name'] = patient.last_name
            
            if patient.role:
                context['role_name'] = patient.role.role_name
            
            context['meals_count'] = FoodIntake.objects.filter(patient=patient).count()
            context['injections_count'] = InsulinInjection.objects.filter(patient=patient).count()
            context['calculations_count'] = Calculation.objects.filter(patient=patient).count()
            
        elif is_doctor:
            doctor = request.user.doctor_profile
            context['first_name'] = doctor.first_name
            context['last_name'] = doctor.last_name
            
            if doctor.role:
                context['role_name'] = doctor.role.role_name
            
            patients = Patient.objects.filter(doctorpatient__doctor=doctor, doctorpatient__is_active=True)
            context['patients_count'] = patients.count()
            context['total_calculations'] = Calculation.objects.filter(patient__in=patients).count()
    
    return render(request, "myApp/home.html", context)

def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Вы успешно вошли')
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')

    return render(request, 'myApp/login.html', {'form': form})


def register_view(request):
    form = RegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name']
        )

        patient_role = Roles.objects.get(role_name='patient')

        Patient.objects.create(
            user=user,
            role=patient_role, 
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            middle_name=form.cleaned_data.get('middle_name', ''),
            birth_date=form.cleaned_data['birth_date'],
            gender=form.cleaned_data.get('gender', ''),
            email=user.email,
            phone=form.cleaned_data.get('phone', ''),
            weight_kg=form.cleaned_data.get('weight_kg'),
            created_at=datetime.now()
        )

        messages.success(request, 'Регистрация успешна! Теперь войдите.')
        return redirect('login')

    return render(request, 'myApp/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('login')


def is_doctor(user):
    return hasattr(user, 'doctor_profile')

def is_patient(user):
    return hasattr(user, 'patient_profile')

def parse_time_to_minutes(time_str):
    """
    Конвертирует время из формата HH:MM или HH:MM:SS в минуты
    """
    if time_str is None:
        return 0
    
    # Если уже число (минуты)
    try:
        return int(time_str)
    except (ValueError, TypeError):
        pass
    
    # Если строка с двоеточием (HH:MM или HH:MM:SS)
    if isinstance(time_str, str) and ':' in time_str:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours * 60 + minutes
    
    return 0

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    if is_patient(request.user) and request.user.patient_profile.id != patient.id:
        messages.error(request, 'Нет доступа к данным этого пациента')
        return redirect('home')
    
    # Получаем выбранную дату (по умолчанию сегодня)
    selected_date_str = request.GET.get('date', date.today().isoformat())
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except:
        selected_date = date.today()
    
    # Получаем данные за выбранную дату
    meals = FoodIntake.objects.filter(patient=patient, record_date=selected_date).order_by('start_time')
    injections = InsulinInjection.objects.filter(patient=patient, record_date=selected_date).order_by('start_time')
    
    # Получаем все даты, за которые есть данные
    meal_dates = FoodIntake.objects.filter(patient=patient).values_list('record_date', flat=True).distinct()
    injection_dates = InsulinInjection.objects.filter(patient=patient).values_list('record_date', flat=True).distinct()
    all_dates = sorted(set(list(meal_dates) + list(injection_dates)), reverse=True)
    
    calculations = Calculation.objects.filter(patient=patient).order_by('-calculation_time')[:10]
    
    context = {
        'patient': patient,
        'meals': meals,
        'injections': injections,
        'calculations': calculations,
        'selected_date': selected_date,
        'available_dates': all_dates,
        'prev_date': selected_date - timedelta(days=1),
        'next_date': selected_date + timedelta(days=1),
    }
    
    return render(request, 'myApp/patient_detail.html', context)


@login_required
def edit_patient_parameters(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    if is_patient(request.user) and request.user.patient_profile.id != patient.id:
        messages.error(request, 'Нет прав для редактирования')
        return redirect('home')
    
    params, created = PatientParameters.objects.get_or_create(patient=patient)
    
    if request.method == 'POST':
        form = PatientParametersForm(request.POST, instance=params)
        print("=== ОТЛАДКА ФОРМЫ ===")
        print("POST данные:", request.POST)
        print("Форма валидна?", form.is_valid())
        if not form.is_valid():
            print("Ошибки формы:", form.errors)
        else:
            form.save()
            messages.success(request, 'Параметры модели сохранены')
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientParametersForm(instance=params)
    
    return render(request, 'myApp/edit_parameters.html', {
        'form': form,
        'patient': patient
    })


@login_required
def add_food_intake(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Проверка доступа: пациент или врач, которому назначен пациент
    has_access = False
    
    if is_patient(request.user) and request.user.patient_profile.id == patient.id:
        has_access = True
    elif is_doctor(request.user):
        doctor = request.user.doctor_profile
        if DoctorPatient.objects.filter(doctor=doctor, patient=patient, is_active=True).exists():
            has_access = True
    
    if not has_access:
        messages.error(request, 'Нет прав для редактирования')
        return redirect('home')
    
    if request.method == 'POST':
        record_date_str = request.POST.get('record_date', date.today().isoformat())
        try:
            record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date()
        except:
            record_date = date.today()
        
        start_time_raw = request.POST.get('start_time', '0')
        start_time = parse_time_to_minutes(start_time_raw)

        FoodIntake.objects.create(
            patient=patient,
            record_date=record_date,
            start_time=start_time,
            duration=int(request.POST.get('duration', 15)),
            carbs_weight=request.POST.get('carbs_weight')
        )
        messages.success(request, 'Прием пищи добавлен')
        
        # Перенаправление в зависимости от роли
        if is_doctor(request.user):
            return redirect(f'/doctor/patient/{patient_id}/?date={record_date}')
        else:
            return redirect(f'/patient/{patient_id}/?date={record_date}')
    
    current_date = request.GET.get('date', date.today().isoformat())
    return render(request, 'myApp/add_food_intake.html', {'patient': patient, 'current_date': current_date})


@login_required
def add_insulin_injection(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Проверка доступа: пациент или врач, которому назначен пациент
    has_access = False
    
    if is_patient(request.user) and request.user.patient_profile.id == patient.id:
        has_access = True
    elif is_doctor(request.user):
        doctor = request.user.doctor_profile
        if DoctorPatient.objects.filter(doctor=doctor, patient=patient, is_active=True).exists():
            has_access = True
    
    if not has_access:
        messages.error(request, 'Нет прав для редактирования')
        return redirect('home')
    
    if request.method == 'POST':
        record_date_str = request.POST.get('record_date', date.today().isoformat())
        try:
            record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date()
        except:
            record_date = date.today()
        
        start_time_raw = request.POST.get('start_time', '0')
        start_time = parse_time_to_minutes(start_time_raw)

        InsulinInjection.objects.create(
            patient=patient,
            record_date=record_date,
            start_time=start_time,
            duration=int(request.POST.get('duration', 1)),
            volume=request.POST.get('volume')
        )
        messages.success(request, 'Инъекция инсулина добавлена')
        
        # Перенаправление в зависимости от роли
        if is_doctor(request.user):
            return redirect(f'/doctor/patient/{patient_id}/?date={record_date}')
        else:
            return redirect(f'/patient/{patient_id}/?date={record_date}')
    
    current_date = request.GET.get('date', date.today().isoformat())
    return render(request, 'myApp/add_insulin_injection.html', {'patient': patient, 'current_date': current_date})

@login_required
def run_calculation(request, patient_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        patient = Patient.objects.get(id=patient_id)
        
        if is_patient(request.user) and request.user.patient_profile.id != patient.id:
            return JsonResponse({'error': 'Нет доступа к данным пациента'}, status=403)
        
        try:
            patient_params = PatientParameters.objects.get(patient=patient)
            params_dict = {
                'glucose_transfer_rate': patient_params.glucose_transfer_rate,
                'insulin_absorption_coefficient': patient_params.insulin_absorption_coefficient,
                'insulin_distribution_rate': patient_params.insulin_distribution_rate,
                'insulin_effect_on_glucose_liver': patient_params.insulin_effect_on_glucose_liver,
                'liver_glucose_production_rate': patient_params.liver_glucose_production_rate,
                'glucose_consumption_rate': patient_params.glucose_consumption_rate,
                'meal_absorption_time': patient_params.meal_absorption_time,
                'insulin_absorption_time': patient_params.insulin_absorption_time,
                'glucose_deactivation_distribution': patient_params.glucose_deactivation_distribution,
                'glucose_deactivation_utilization': patient_params.glucose_deactivation_utilization,
                'glucose_deactivation_liver': patient_params.glucose_deactivation_liver,
                'glucose_distribution_volume': patient_params.glucose_distribution_volume,
                'insulin_distribution_volume': patient_params.insulin_distribution_volume,
                'bioavailability': patient_params.bioavailability,
                'insulin_elimination_rate': patient_params.insulin_elimination_rate,
        
                # Начальные условия
                'initial_D1': patient_params.initial_D1,
                'initial_D2': patient_params.initial_D2,
                'initial_Q1': patient_params.initial_Q1,
                'initial_Q2': patient_params.initial_Q2,
                'initial_S1': patient_params.initial_S1,
                'initial_S2': patient_params.initial_S2,
                'initial_I': patient_params.initial_I,
                'initial_x1': patient_params.initial_x1,
                'initial_x2': patient_params.initial_x2,
                'initial_x3': patient_params.initial_x3,
            }
        except PatientParameters.DoesNotExist:
            params_dict = {}
        
        model = HovorkaModel(patient.weight_kg, params_dict)
        
        # Получаем дату из POST запроса (если нет - сегодня)
        selected_date_str = request.POST.get('selected_date', date.today().isoformat())
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except:
            selected_date = date.today()
        
        # Фильтруем данные ТОЛЬКО за выбранную дату
        meals = FoodIntake.objects.filter(patient=patient, record_date=selected_date)
        injections = InsulinInjection.objects.filter(patient=patient, record_date=selected_date)
        
        # Проверяем, есть ли данные
        if not meals.exists() and not injections.exists():
            return JsonResponse({'error': f'Нет данных для расчета за {selected_date}. Добавьте приемы пищи или инъекции инсулина.'}, status=400)
        
        meals_list = [{'start': m.start_time, 'duration': m.duration, 'weight': float(m.carbs_weight)} for m in meals]
        injections_list = [{'start': i.start_time, 'duration': i.duration, 'dose': float(i.volume)*1000} for i in injections]
        
        start_time = request.POST.get('start_time', 420)
        end_time = request.POST.get('end_time', 1440)
        time_step = request.POST.get('time_step', 0.1)
        
        # Конвертируем время если пришло в формате HH:MM
        if isinstance(start_time, str) and ':' in start_time:
            h, m = map(int, start_time.split(':'))
            start_time = h * 60 + m
        if isinstance(end_time, str) and ':' in end_time:
            h, m = map(int, end_time.split(':'))
            end_time = h * 60 + m
        
        result = model.calculate_glucose(
            meals=meals_list,
            injections=injections_list,
            start_time=int(start_time),
            end_time=int(end_time),
            time_step=float(time_step)
        )
        
        if result and result.get('glucose') and len(result['glucose']) > 0:
            calculation = Calculation.objects.create(
                patient=patient,
                calculation_time=datetime.now(),
                glucose_forecast=result['glucose'][-1],
                insulin_effect=0,
                carbs_utilized=sum(m['weight'] for m in meals_list),
                created_at=datetime.now()
            )
            
            Charts.objects.create(
                patient=patient,
                calculation=calculation,
                chart_type='glucose_forecast',
                data=json.dumps({
                    'times': result['times'],
                    'glucose': result['glucose'],
                    'insulin': result['insulin'],
                    'D1': result.get('D1', []),
                    'D2': result.get('D2', []),
                    'Q1': result.get('Q1', []),
                    'Q2': result.get('Q2', []),
                    'S1': result.get('S1', []),
                    'S2': result.get('S2', []),
                    'x1': result.get('x1', []),
                    'x2': result.get('x2', []),
                    'x3': result.get('x3', []),
                    'UG': result.get('UG', []),
                    'food_rate': result.get('food_rate', []),
                    'insulin_rate': result.get('insulin_rate', []),
                    'D_t': result.get('D_t', []),
                }),
                created_at=datetime.now()
            )
            
            return JsonResponse({'success': True, 'calculation_id': calculation.id, 'result': result})
        else:
            return JsonResponse({'error': 'Ошибка при расчете модели: нет данных глюкозы'}, status=500)
            
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Пациент не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def get_calculation_result(request, calculation_id):
    try:
        calculation = Calculation.objects.get(id=calculation_id)
        
        if is_patient(request.user) and calculation.patient.user.id != request.user.id:
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        
        chart = Charts.objects.filter(calculation=calculation, chart_type='glucose_forecast').first()
        
        if chart:
            data = json.loads(chart.data)
            return JsonResponse({
                'calculation_time': calculation.calculation_time,
                'glucose_forecast': calculation.glucose_forecast,
                'times': data.get('times', []),
                'glucose': data.get('glucose', []),
                'insulin': data.get('insulin', []),
                'D1': data.get('D1', []),
                'D2': data.get('D2', []),
                'Q1': data.get('Q1', []),
                'Q2': data.get('Q2', []),
                'S1': data.get('S1', []),
                'S2': data.get('S2', []),
                'x1': data.get('x1', []),
                'x2': data.get('x2', []),
                'x3': data.get('x3', []),
                'UG': data.get('UG', []),
                'food_rate': data.get('food_rate', []),
                'insulin_rate': data.get('insulin_rate', []),
                'D_t': data.get('D_t', []),
            })
        else:
            return JsonResponse({'error': 'Данные расчета не найдены'}, status=404)
            
    except Calculation.DoesNotExist:
        return JsonResponse({'error': 'Расчет не найден'}, status=404)


@login_required
def change_user_role(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Доступ только для администратора')
        return redirect('home')
    
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_role_name = request.POST.get('role')
        
        try:
            new_role = Roles.objects.get(role_name=new_role_name)
        except Roles.DoesNotExist:
            messages.error(request, 'Роль не найдена')
            return redirect('home')
        
        if new_role_name == 'doctor':
            if not hasattr(target_user, 'doctor_profile'):
                if hasattr(target_user, 'patient_profile'):
                    target_user.patient_profile.delete()
                
                Doctor.objects.create(
                    user=target_user,
                    role=new_role,
                    first_name=target_user.first_name,
                    last_name=target_user.last_name,
                    email=target_user.email,
                    created_at=datetime.now()
                )
                messages.success(request, f'Пользователь {target_user.username} теперь врач')
            else:
                target_user.doctor_profile.role = new_role
                target_user.doctor_profile.save()
                messages.success(request, f'Роль обновлена')
                
        elif new_role_name == 'patient':
            if not hasattr(target_user, 'patient_profile'):
                if hasattr(target_user, 'doctor_profile'):
                    target_user.doctor_profile.delete()
                
                messages.warning(request, 'Для создания пациента нужна дата рождения')
                return redirect('home')
            else:
                target_user.patient_profile.role = new_role
                target_user.patient_profile.save()
                messages.success(request, f'Роль обновлена')
        
        return redirect('home')
    
    current_role = None
    if hasattr(target_user, 'patient_profile') and target_user.patient_profile.role:
        current_role = target_user.patient_profile.role.role_name
    elif hasattr(target_user, 'doctor_profile') and target_user.doctor_profile.role:
        current_role = target_user.doctor_profile.role.role_name
    
    roles = Roles.objects.all()
    
    return render(request, 'myApp/change_role.html', {
        'user': target_user,
        'current_role': current_role,
        'roles': roles
    })
@login_required
def manage_users(request):
    if not request.user.is_superuser:
        messages.error(request, 'Доступ только для администратора')
        return redirect('home')
    
    users = User.objects.all()
    return render(request, 'myApp/manage_users.html', {'users': users})

@login_required
def edit_food_intake(request, patient_id, item_id):
    patient = get_object_or_404(Patient, id=patient_id)
    item = get_object_or_404(FoodIntake, id=item_id, patient=patient)
    
    # Проверка доступа: пациент или врач, которому назначен пациент
    has_access = False
    
    if is_patient(request.user) and request.user.patient_profile.id == patient.id:
        has_access = True
    elif is_doctor(request.user):
        doctor = request.user.doctor_profile
        if DoctorPatient.objects.filter(doctor=doctor, patient=patient, is_active=True).exists():
            has_access = True
    
    if not has_access:
        return JsonResponse({'error': 'Нет прав'}, status=403)
    
    if request.method == 'POST':
        start_time_raw = request.POST.get('start_time', '0')
        item.start_time = parse_time_to_minutes(start_time_raw)
        item.duration = int(request.POST.get('duration', item.duration))
        item.carbs_weight = request.POST.get('carbs_weight', item.carbs_weight)
        item.save()
        messages.success(request, 'Прием пищи обновлен')
        
        # Перенаправление в зависимости от роли
        if is_doctor(request.user):
            return redirect(f'/doctor/patient/{patient_id}/?date={item.record_date}')
        else:
            return redirect(f'/patient/{patient_id}/?date={item.record_date}')
    
    return render(request, 'myApp/edit_food_intake.html', {'patient': patient, 'item': item})


@login_required
def edit_insulin_injection(request, patient_id, item_id):
    patient = get_object_or_404(Patient, id=patient_id)
    item = get_object_or_404(InsulinInjection, id=item_id, patient=patient)
    
    # Проверка доступа: пациент или врач, которому назначен пациент
    has_access = False
    
    if is_patient(request.user) and request.user.patient_profile.id == patient.id:
        has_access = True
    elif is_doctor(request.user):
        doctor = request.user.doctor_profile
        if DoctorPatient.objects.filter(doctor=doctor, patient=patient, is_active=True).exists():
            has_access = True
    
    if not has_access:
        return JsonResponse({'error': 'Нет прав'}, status=403)
    
    if request.method == 'POST':
        start_time_raw = request.POST.get('start_time', '0')
        item.start_time = parse_time_to_minutes(start_time_raw)
        item.duration = int(request.POST.get('duration', item.duration))
        item.volume = request.POST.get('volume', item.volume)
        item.save()
        messages.success(request, 'Инъекция инсулина обновлена')
        
        # Перенаправление в зависимости от роли
        if is_doctor(request.user):
            return redirect(f'/doctor/patient/{patient_id}/?date={item.record_date}')
        else:
            return redirect(f'/patient/{patient_id}/?date={item.record_date}')
    
    return render(request, 'myApp/edit_insulin_injection.html', {'patient': patient, 'item': item})


@login_required
def delete_food_intake(request, patient_id, item_id):
    patient = get_object_or_404(Patient, id=patient_id)
    item = get_object_or_404(FoodIntake, id=item_id, patient=patient)
    
    # Проверка доступа: пациент или врач, которому назначен пациент
    has_access = False
    
    if is_patient(request.user) and request.user.patient_profile.id == patient.id:
        has_access = True
    elif is_doctor(request.user):
        doctor = request.user.doctor_profile
        if DoctorPatient.objects.filter(doctor=doctor, patient=patient, is_active=True).exists():
            has_access = True
    
    if not has_access:
        return JsonResponse({'error': 'Нет прав'}, status=403)
    
    record_date = item.record_date
    item.delete()
    messages.success(request, 'Прием пищи удален')
    
    # Перенаправление в зависимости от роли
    if is_doctor(request.user):
        return redirect(f'/doctor/patient/{patient_id}/?date={record_date}')
    else:
        return redirect(f'/patient/{patient_id}/?date={record_date}')


@login_required
def delete_insulin_injection(request, patient_id, item_id):
    patient = get_object_or_404(Patient, id=patient_id)
    item = get_object_or_404(InsulinInjection, id=item_id, patient=patient)
    
    # Проверка доступа: пациент или врач, которому назначен пациент
    has_access = False
    
    if is_patient(request.user) and request.user.patient_profile.id == patient.id:
        has_access = True
    elif is_doctor(request.user):
        doctor = request.user.doctor_profile
        if DoctorPatient.objects.filter(doctor=doctor, patient=patient, is_active=True).exists():
            has_access = True
    
    if not has_access:
        return JsonResponse({'error': 'Нет прав'}, status=403)
    
    record_date = item.record_date
    item.delete()
    messages.success(request, 'Инъекция инсулина удалена')
    
    # Перенаправление в зависимости от роли
    if is_doctor(request.user):
        return redirect(f'/doctor/patient/{patient_id}/?date={record_date}')
    else:
        return redirect(f'/patient/{patient_id}/?date={record_date}')

@login_required
def doctor_patients(request):
    if not is_doctor(request.user):
        messages.error(request, 'Доступ только для врачей')
        return redirect('home')
    
    doctor = request.user.doctor_profile
    patients = Patient.objects.filter(doctorpatient__doctor=doctor, doctorpatient__is_active=True)
    
    patients_data = []
    for patient in patients:
        patients_data.append({
            'patient': patient,
            'age': (date.today() - patient.birth_date).days // 365,
            'meals_count': FoodIntake.objects.filter(patient=patient).count(),
            'injections_count': InsulinInjection.objects.filter(patient=patient).count(),
            'calculations_count': Calculation.objects.filter(patient=patient).count(),
        })
    
    context = {
        'patients': patients_data,
    }
    return render(request, 'myApp/doctor_patients.html', context)


@login_required
def doctor_patient_detail(request, patient_id):
    if not is_doctor(request.user):
        messages.error(request, 'Доступ только для врачей')
        return redirect('home')
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Проверяем, что пациент привязан к этому врачу
    doctor = request.user.doctor_profile
    if not DoctorPatient.objects.filter(doctor=doctor, patient=patient, is_active=True).exists():
        messages.error(request, 'Пациент не привязан к вам')
        return redirect('doctor_patients')
    
    selected_date_str = request.GET.get('date', date.today().isoformat())
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except:
        selected_date = date.today()
    
    meals = FoodIntake.objects.filter(patient=patient, record_date=selected_date).order_by('start_time')
    injections = InsulinInjection.objects.filter(patient=patient, record_date=selected_date).order_by('start_time')
    
    all_dates = sorted(set(
        list(FoodIntake.objects.filter(patient=patient).values_list('record_date', flat=True)) +
        list(InsulinInjection.objects.filter(patient=patient).values_list('record_date', flat=True))
    ), reverse=True)
    
    calculations = Calculation.objects.filter(patient=patient).order_by('-calculation_time')[:10]
    
    context = {
        'patient': patient,
        'meals': meals,
        'injections': injections,
        'calculations': calculations,
        'selected_date': selected_date,
        'available_dates': all_dates,
        'prev_date': selected_date - timedelta(days=1),
        'next_date': selected_date + timedelta(days=1),
    }
    return render(request, 'myApp/doctor_patient_detail.html', context)



@login_required
def manage_doctor_patients(request):
    if not request.user.is_superuser:
        messages.error(request, 'Доступ только для администратора')
        return redirect('home')
    
    doctors = Doctor.objects.all()
    patients = Patient.objects.all()
    assignments = DoctorPatient.objects.filter(is_active=True)
    
    context = {
        'doctors': doctors,
        'patients': patients,
        'assignments': assignments,
    }
    return render(request, 'myApp/manage_doctor_patients.html', context)


@login_required
def assign_patient_to_doctor(request):
    if not request.user.is_superuser:
        messages.error(request, 'Доступ только для администратора')
        return redirect('home')
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        patient_id = request.POST.get('patient_id')
        
        doctor = get_object_or_404(Doctor, id=doctor_id)
        patient = get_object_or_404(Patient, id=patient_id)
        
        existing = DoctorPatient.objects.filter(doctor=doctor, patient=patient, is_active=True).first()
        if existing:
            messages.warning(request, f'Пациент уже назначен врачу {doctor.user.username}')
        else:
            DoctorPatient.objects.create(
                doctor=doctor,
                patient=patient,
                assigned_date=date.today(),
                is_active=True
            )
            messages.success(request, f'Пациент {patient.last_name} {patient.first_name} назначен врачу {doctor.user.username}')
        
        return redirect('manage_doctor_patients')
    
    return redirect('manage_doctor_patients')


@login_required
def remove_patient_from_doctor(request, assignment_id):
    if not request.user.is_superuser:
        messages.error(request, 'Доступ только для администратора')
        return redirect('home')
    
    assignment = get_object_or_404(DoctorPatient, id=assignment_id)
    assignment.is_active = False
    assignment.end_date = date.today()
    assignment.save()
    
    messages.success(request, 'Назначение удалено')
    return redirect('manage_doctor_patients')
@login_required
def patient_profile(request, patient_id):
    # Получаем пациента
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Проверка прав доступа
    has_access = False
    user_role = None
    
    if hasattr(request.user, 'patient_profile') and request.user.patient_profile == patient:
        has_access = True
        user_role = 'patient'
    elif hasattr(request.user, 'doctor_profile'):
        # Проверяем, привязан ли врач к этому пациенту
        is_assigned = DoctorPatient.objects.filter(
            doctor=request.user.doctor_profile,
            patient=patient,
            is_active=True
        ).exists()
        if is_assigned:
            has_access = True
            user_role = 'doctor'
    
    if not has_access:
        messages.error(request, 'У вас нет доступа к профилю этого пациента')
        return redirect('home')
    
    # Обработка POST запроса (только изменение веса)
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            old_weight = patient.weight_kg
            form.save()
            new_weight = patient.weight_kg
            
            # Записываем историю изменения веса
            PatientHistory.objects.create(
                patient=patient,
                doctor=request.user.doctor_profile if user_role == 'doctor' else None,
                user_role=user_role,
                action_type='weight_update',
                action_time=timezone.now(),
                description=f'Вес изменен с {old_weight} кг на {new_weight} кг',
                user=request.user
            )
            
            messages.success(request, f'Вес успешно обновлен! Новый вес: {new_weight} кг')
            return redirect('patient_profile', patient_id=patient.id)
    else:
        form = PatientProfileForm(instance=patient)
    
    # Контекст для шаблона
    context = {
        'patient': patient,
        'form': form,
        'user_role': user_role,
        'can_edit_weight': True,  # Всегда можно редактировать вес
    }
    
    return render(request, 'myApp/patient_profile.html', context)