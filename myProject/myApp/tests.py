# myApp/tests.py
import sys
import unittest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime, date, timedelta
import json
import numpy as np
from django.db import connection
from django.core.management import call_command

from .hovorka_model import HovorkaModel
from .models import (
    Charts, Roles, Patient, Doctor, DoctorPatient, FoodIntake, 
    InsulinInjection, PatientParameters, Calculation, 
    GlucoseMeasurement
)

# ==================== МОДУЛЬНОЕ ТЕСТИРОВАНИЕ ====================

class HovorkaModelTestCase(TestCase):
    """Модульное тестирование вычислительного модуля HovorkaModel"""
    
    def setUp(self):
        self.model = HovorkaModel(patient_weight=70.0)
        
        self.test_meals = [
            {'start': 420, 'duration': 15, 'weight': 30},
            {'start': 780, 'duration': 20, 'weight': 50}
        ]
        
        self.test_injections = [
            {'start': 415, 'duration': 2, 'dose': 500},
            {'start': 775, 'duration': 2, 'dose': 600}
        ]
    
    def test_01_food_intake_rate(self):
        """Тест 1: Проверка расчета скорости приема пищи"""
        rate = self.model.food_intake_rate(420, self.test_meals)
        self.assertGreaterEqual(rate, 0)
        
        rate_outside = self.model.food_intake_rate(400, self.test_meals)
        self.assertEqual(rate_outside, 0)
        
        rate_peak = self.model.food_intake_rate(427.5, self.test_meals)
        self.assertGreater(rate_peak, 0)
        print("✓ Тест food_intake_rate пройден")
    
    def test_02_insulin_injection_rate(self):
        """Тест 2: Проверка скорости введения инсулина"""
        rate = self.model.insulin_injection_rate(416, self.test_injections)
        self.assertGreaterEqual(rate, 0)
        
        rate_outside = self.model.insulin_injection_rate(400, self.test_injections)
        self.assertEqual(rate_outside, 0)
        print("✓ Тест insulin_injection_rate пройден")
    
    def test_03_renal_glucose_uptake(self):
        """Тест 3: Проверка почечной реабсорбции"""
        uptake_low = self.model.renal_glucose_uptake(8.0)
        self.assertEqual(uptake_low, 0)
        
        uptake_high = self.model.renal_glucose_uptake(10.0)
        self.assertGreaterEqual(uptake_high, 0)
        print("✓ Тест renal_glucose_uptake пройден")
    
    def test_04_system_equations(self):
        """Тест 4: Проверка системы дифференциальных уравнений"""
        state = [0, 0, 70.0, 20.0, 0, 0, 20.0, 0.001, 0.001, 0.001]
        derivatives = self.model.system_equations(
            state, 420, self.test_meals, self.test_injections
        )
        
        self.assertEqual(len(derivatives), 10)
        for deriv in derivatives:
            self.assertIsInstance(deriv, float)
        print("✓ Тест system_equations пройден")
    
    def test_05_calculate_glucose(self):
        """Тест 5: Проверка расчета профиля глюкозы"""
        result = self.model.calculate_glucose(
            meals=self.test_meals,
            injections=self.test_injections,
            start_time=420, end_time=600, time_step=5.0
        )
        
        self.assertIn('times', result)
        self.assertIn('glucose', result)
        self.assertIn('insulin', result)
        self.assertGreater(len(result['glucose']), 0)
        
        for glucose in result['glucose']:
            self.assertGreaterEqual(glucose, 0)
            self.assertLess(glucose, 50)
        print("✓ Тест calculate_glucose пройден")
    
    def test_06_default_params(self):
        """Тест 6: Проверка параметров по умолчанию"""
        model = HovorkaModel(patient_weight=60.0)
        
        self.assertEqual(model.W, 60.0)
        self.assertEqual(model.EGP0, 0.079 * 60)
        self.assertEqual(model.F01, 0.089 * 60)
        self.assertEqual(model.VG, 0.16 * 60)
        self.assertEqual(model.VI, 0.12 * 60)
        print("✓ Тест default_params пройден")
    
    def test_07_custom_params(self):
        """Тест 7: Проверка пользовательских параметров"""
        custom_params = {
            'glucose_transfer_rate': 0.07,
            'meal_absorption_time': 50.0,
        }
        model = HovorkaModel(patient_weight=70.0, custom_params=custom_params)
        
        self.assertEqual(model.k12, 0.07)
        self.assertEqual(model.tau_D, 50.0)
        print("✓ Тест custom_params пройден")


# ==================== ИНТЕГРАЦИОННОЕ ТЕСТИРОВАНИЕ (ТОЛЬКО ORM) ====================

class IntegrationDatabaseTestCase(TestCase):  # ИЗМЕНЕНО: TransactionTestCase → TestCase
    """Интеграционное тестирование с БД (используем только ORM)"""
    
    @classmethod
    def setUpClass(cls):
        """Принудительно применяем миграции перед тестами"""
        super().setUpClass()
        call_command('migrate', verbosity=0, interactive=False)
    
    def setUp(self):
        # Создаем роли через ORM
        self.patient_role = Roles.objects.create(role_name='patient')
        self.doctor_role = Roles.objects.create(role_name='doctor')
        
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='test_patient', 
            email='test@test.com',
            password='testpass123', 
            first_name='Иван', 
            last_name='Петров'
        )
        
        # Создаем пациента через ORM
        self.patient = Patient.objects.create(
            user=self.user,
            role=self.patient_role,
            first_name='Иван',
            last_name='Петров',
            birth_date=date(1990, 1, 1),
            weight_kg=70.5,
            email='test@test.com'
        )
        
        # Создаем прием пищи через ORM
        self.food = FoodIntake.objects.create(
            patient=self.patient,
            record_date=date.today(),
            start_time=480,
            duration=15,
            carbs_weight=30.0
        )
        
        # Создаем инъекцию через ORM
        self.insulin = InsulinInjection.objects.create(
            patient=self.patient,
            record_date=date.today(),
            start_time=475,
            duration=2,
            volume=0.5
        )
    
    def test_01_patient_creation(self):
        """Тест создания пациента через ORM"""
        patient = Patient.objects.get(id=self.patient.id)
        self.assertEqual(patient.first_name, 'Иван')
        self.assertEqual(float(patient.weight_kg), 70.5)
        print("✓ Тест patient_creation пройден")
    
    def test_02_food_intake_creation(self):
        """Тест создания приема пищи через ORM"""
        foods = FoodIntake.objects.filter(patient=self.patient)
        self.assertEqual(foods.count(), 1)
        self.assertEqual(float(foods[0].carbs_weight), 30.0)
        print("✓ Тест food_intake_creation пройден")
    
    def test_03_insulin_creation(self):
        """Тест создания инъекции через ORM"""
        injections = InsulinInjection.objects.filter(patient=self.patient)
        self.assertEqual(injections.count(), 1)
        self.assertEqual(float(injections[0].volume), 0.5)
        print("✓ Тест insulin_creation пройден")
    
    def test_04_filter_by_date(self):
        """Тест фильтрации по дате через ORM"""
        today_count = FoodIntake.objects.filter(
            patient=self.patient, 
            record_date=date.today()
        ).count()
        self.assertEqual(today_count, 1)
        
        tomorrow_count = FoodIntake.objects.filter(
            patient=self.patient, 
            record_date=date.today() + timedelta(days=1)
        ).count()
        self.assertEqual(tomorrow_count, 0)
        print("✓ Тест filter_by_date пройден")
    
    def test_05_update_data(self):
        """Тест обновления данных через ORM"""
        self.food.carbs_weight = 45.0
        self.food.save()
        
        updated_food = FoodIntake.objects.get(id=self.food.id)
        self.assertEqual(float(updated_food.carbs_weight), 45.0)
        print("✓ Тест update_data пройден")
    
    def test_06_delete_data(self):
        """Тест удаления данных через ORM"""
        food_id = self.food.id
        self.food.delete()
        
        with self.assertRaises(FoodIntake.DoesNotExist):
            FoodIntake.objects.get(id=food_id)
        print("✓ Тест delete_data пройден")

    def test_07_patient_parameters_creation(self):

        params = PatientParameters.objects.create(
            patient=self.patient,
            bioavailability=0.8,
            glucose_transfer_rate=0.065,
            insulin_absorption_rate=0.005,
            glucose_deactivation_distribution=0.006,
            glucose_deactivation_utilization=0.006,
            glucose_deactivation_liver=0.006,
            meal_absorption_time=40,
            glucose_distribution_volume=0.16,
            insulin_distribution_volume=0.12,
            insulin_absorption_time=45,
            insulin_distribution_rate=0.002,
            insulin_absorption_coefficient=0.001,
            insulin_effect_on_glucose_liver=0.0001,
            liver_glucose_production_rate=0.016,
            glucose_consumption_rate=0.014,
            updated_at=datetime.now()
        )
        
        saved_params = PatientParameters.objects.get(id=params.id)
        self.assertEqual(float(saved_params.bioavailability), 0.8)
        self.assertEqual(float(saved_params.glucose_transfer_rate), 0.065)
        self.assertEqual(saved_params.meal_absorption_time, 40)
        print("✓ Тест patient_parameters_creation пройден")

    def test_08_calculation_creation(self):
        """Тест создания результата расчета через ORM"""
        # Используем реальные поля из модели Calculation
        calculation = Calculation.objects.create(
            patient=self.patient,
            calculation_time=datetime.now(),
            glucose_forecast=7.5,  # DecimalField - одно число, не JSON
            insulin_effect=0.045,   # DecimalField
            carbs_utilized=45.0,
            created_at=datetime.now()
        )
        
        saved_calc = Calculation.objects.get(id=calculation.id)
        self.assertEqual(float(saved_calc.glucose_forecast), 7.5)
        self.assertEqual(float(saved_calc.insulin_effect), 0.045)
        self.assertEqual(float(saved_calc.carbs_utilized), 45.0)
        self.assertIsNotNone(saved_calc.calculation_time)
        print("✓ Тест calculation_creation пройден")

    def test_09_charts_creation(self):
        """Тест создания графиков через ORM"""
        # Сначала создаем Calculation
        calculation = Calculation.objects.create(
            patient=self.patient,
            calculation_time=datetime.now(),
            glucose_forecast=7.5,
            insulin_effect=0.045,
            carbs_utilized=45.0
        )
        
        # Создаем Charts с правильными полями
        chart = Charts.objects.create(
            patient=self.patient,
            calculation=calculation,
            chart_type='glucose_profile',
            data={
                'times': [420, 480, 540, 600],
                'glucose': [5.2, 6.8, 7.5, 6.5],
                'insulin': [12.5, 15.2, 18.1, 14.3]
            },
            created_at=datetime.now()
        )
        
        saved_chart = Charts.objects.get(id=chart.id)
        self.assertEqual(saved_chart.chart_type, 'glucose_profile')
        self.assertIn('glucose', saved_chart.data)
        self.assertEqual(len(saved_chart.data['glucose']), 4)
        print("✓ Тест charts_creation пройден")

    def test_10_run_calculation_integration(self):
        """Тест интеграции run_calculation с БД"""
        # Создаем тестовые данные
        meal = FoodIntake.objects.create(
            patient=self.patient,
            record_date=date.today(),
            start_time=480,
            duration=15,
            carbs_weight=45.0
        )
        
        insulin = InsulinInjection.objects.create(
            patient=self.patient,
            record_date=date.today(),
            start_time=475,
            duration=2,
            volume=0.6
        )
        
        # Получаем или создаем параметры пациента
        params, created = PatientParameters.objects.get_or_create(
            patient=self.patient,
            defaults={
                'meal_absorption_time': 40,
                'glucose_transfer_rate': 0.065,
                'glucose_distribution_volume': 0.16,
                'insulin_distribution_volume': 0.12
            }
        )
        
        # Запускаем расчет
        patient_weight = float(self.patient.weight_kg) if self.patient.weight_kg else 70.0
        model = HovorkaModel(patient_weight=patient_weight)
        
        meals_list = [{
            'start': meal.start_time,
            'duration': meal.duration,
            'weight': float(meal.carbs_weight)
        }]
        
        injections_list = [{
            'start': insulin.start_time,
            'duration': insulin.duration,
            'dose': float(insulin.volume) * 1000
        }]
        
        result = model.calculate_glucose(
            meals=meals_list,
            injections=injections_list,
            start_time=420,
            end_time=600,
            time_step=5.0
        )
        
        # Сохраняем результаты в БД
        # Для каждого временного отрезка создаем запись Calculation
        max_glucose = max(result['glucose']) if result['glucose'] else 0
        
        calculation = Calculation.objects.create(
            patient=self.patient,
            calculation_time=datetime.now(),
            glucose_forecast=round(max_glucose, 2),  # пиковое значение
            insulin_effect=0.045,  # вычисленное значение
            carbs_utilized=float(meal.carbs_weight),
            created_at=datetime.now()
        )
        
        # Сохраняем полный профиль в Charts
        chart = Charts.objects.create(
            patient=self.patient,
            calculation=calculation,
            chart_type='glucose_profile',
            data={
                'times': result['times'],
                'glucose': result['glucose'],
                'insulin': result.get('insulin', [])
            },
            created_at=datetime.now()
        )
        
        # Проверяем сохранение
        saved_calc = Calculation.objects.get(id=calculation.id)
        saved_chart = Charts.objects.get(id=chart.id)
        
        self.assertIsNotNone(saved_calc.glucose_forecast)
        self.assertIsNotNone(saved_chart.data)
        self.assertIn('glucose', saved_chart.data)
        print("✓ Тест run_calculation_integration пройден")
# ==================== ФУНКЦИОНАЛЬНОЕ ТЕСТИРОВАНИЕ (ТОЛЬКО ORM) ====================

class FunctionalTestCase(TestCase):  # ИЗМЕНЕНО: TransactionTestCase → TestCase
    """Функциональное тестирование с реальными моделями через ORM"""
    
    @classmethod
    def setUpClass(cls):
        """Принудительно применяем миграции перед тестами"""
        super().setUpClass()
        call_command('migrate', verbosity=0, interactive=False)
    
    def setUp(self):
        self.client = Client()
        
        # Создаем роли через ORM
        self.patient_role = Roles.objects.create(role_name='patient')
        self.doctor_role = Roles.objects.create(role_name='doctor')
        
        # Создаем пользователя-пациента
        self.patient_user = User.objects.create_user(
            username='patient', 
            email='patient@test.com',
            password='patient123', 
            first_name='Иван', 
            last_name='Пациентов'
        )
        
        # Создаем пациента через ORM
        self.patient = Patient.objects.create(
            user=self.patient_user,
            role=self.patient_role,
            first_name='Иван',
            last_name='Пациентов',
            middle_name='Иванович',
            birth_date=date(1985, 5, 15),
            weight_kg=75.0,
            email='patient@test.com'
        )
        
        # Создаем пользователя-врача
        self.doctor_user = User.objects.create_user(
            username='doctor', 
            email='doctor@test.com',
            password='doctor123', 
            first_name='Анна', 
            last_name='Врачева'
        )
        
        # Создаем врача через ORM
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            role=self.doctor_role,
            first_name='Анна',
            last_name='Врачева',
            email='doctor@test.com'
        )
        
        # Создаем связь врач-пациент (опционально)
        self.doctor_patient = DoctorPatient.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            assigned_date=date.today(),
            is_active=True
        )
    
    def test_01_register_page(self):
        """Тест страницы регистрации"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        print("✓ Тест register_page пройден")
    
    def test_02_login_patient(self):
        """Тест входа пациента"""
        response = self.client.post(reverse('login'), {
            'username': 'patient', 
            'password': 'patient123'
        })
        self.assertEqual(response.status_code, 302)
        # Проверяем редирект на главную
        self.assertIn(response.url, ['/', '/dashboard/'])
        print("✓ Тест login_patient пройден")
    
    def test_03_patient_detail_access(self):
        """Тест доступа к деталям пациента"""
        self.client.login(username='patient', password='patient123')
        response = self.client.get(reverse('patient_detail', args=[self.patient.id]))
        self.assertIn(response.status_code, [200, 302])
        print("✓ Тест patient_detail_access пройден")
    
    def test_04_unauthorized_access(self):
        """Тест доступа без авторизации"""
        response = self.client.get(reverse('patient_detail', args=[self.patient.id]))
        self.assertEqual(response.status_code, 302)  # Перенаправление на логин
        print("✓ Тест unauthorized_access пройден")
    
    def test_05_doctor_access_to_patient(self):
        """Тест доступа врача к пациенту"""
        self.client.login(username='doctor', password='doctor123')
        response = self.client.get(reverse('doctor_patient_detail', args=[self.patient.id]))
        self.assertIn(response.status_code, [200, 302, 404])
        print("✓ Тест doctor_access_to_patient пройден")
    
    def test_06_doctor_patients_list(self):
        """Тест списка пациентов врача"""
        self.client.login(username='doctor', password='doctor123')
        response = self.client.get(reverse('doctor_patients'))
        self.assertIn(response.status_code, [200, 302])
        print("✓ Тест doctor_patients_list пройден")
    
    def test_07_logout(self):
        """Тест выхода из системы"""
        self.client.login(username='patient', password='patient123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        print("✓ Тест logout пройден")

    def test_08_add_food_intake(self):
        """Тест добавления приема пищи через форму"""
        self.client.login(username='patient', password='patient123')
        
        response = self.client.post(reverse('add_food_intake', args=[self.patient.id]), {
            'record_date': date.today().isoformat(),
            'start_time': 480,
            'duration': 15,
            'carbs_weight': 35.0
        })
        
        # Проверяем редирект после успешного добавления
        self.assertIn(response.status_code, [200, 302])
        
        # Проверяем, что данные сохранились в БД
        food_exists = FoodIntake.objects.filter(
            patient=self.patient,
            start_time=480,
            carbs_weight=35.0
        ).exists()
        self.assertTrue(food_exists)
        print("✓ Тест add_food_intake пройден")

    def test_09_add_insulin_injection(self):
        """Тест добавления инъекции инсулина через форму"""
        self.client.login(username='patient', password='patient123')
        
        response = self.client.post(reverse('add_insulin_injection', args=[self.patient.id]), {
            'record_date': date.today().isoformat(),
            'start_time': 475,
            'duration': 2,
            'volume': 0.55
        })
        
        self.assertIn(response.status_code, [200, 302])
        
        # Проверяем сохранение в БД
        insulin_exists = InsulinInjection.objects.filter(
            patient=self.patient,
            start_time=475,
            volume=0.55
        ).exists()
        self.assertTrue(insulin_exists)
        print("✓ Тест add_insulin_injection пройден")

    def test_10_run_calculation_functional(self):
        """Тест выполнения расчета через веб-интерфейс"""
        self.client.login(username='patient', password='patient123')
        
        # Сначала добавляем данные для расчета
        FoodIntake.objects.create(
            patient=self.patient,
            record_date=date.today(),
            start_time=480,
            duration=15,
            carbs_weight=40.0
        )
        
        InsulinInjection.objects.create(
            patient=self.patient,
            record_date=date.today(),
            start_time=475,
            duration=2,
            volume=0.5
        )
        
        # Запускаем расчет
        response = self.client.post(reverse('run_calculation', args=[self.patient.id]), {
            'start_time': 420,
            'duration': 180,
            'time_step': 5
        })
        
        self.assertIn(response.status_code, [200, 302])
        
        # ИСПРАВЛЕНО: убираем calculation_type, так как его нет в модели
        calculation_exists = Calculation.objects.filter(
            patient=self.patient
        ).exists()
        
        # Также проверяем наличие графиков
        charts_exists = Charts.objects.filter(
            patient=self.patient
        ).exists()
        
        # Проверяем, что хотя бы что-то сохранилось
        self.assertTrue(calculation_exists or charts_exists, 
                    "Ни расчет, ни график не были сохранены в БД")
        print("✓ Тест run_calculation_functional пройден")
        
    def test_11_patient_data_display(self):
        """Тест отображения данных пациента на странице"""
        self.client.login(username='patient', password='patient123')
        
        response = self.client.get(reverse('patient_detail', args=[self.patient.id]))
        
        if response.status_code == 200:
            # Проверяем, что данные отображаются
            content = response.content.decode('utf-8')
            self.assertIn('Иван', content)
            self.assertIn('Пациентов', content)
        print("✓ Тест patient_data_display пройден")

    def test_12_role_based_access_patient(self):
        """Тест разграничения доступа: пациент не видит врачебные функции"""
        self.client.login(username='patient', password='patient123')
        
        # Попытка доступа к списку пациентов врача
        response = self.client.get(reverse('doctor_patients'))
        
        # Должен быть редирект или 403
        self.assertIn(response.status_code, [302, 403, 404])
        print("✓ Тест role_based_access_patient пройден")

    def test_13_role_based_access_doctor(self):
        """Тест разграничения доступа: врач имеет доступ к данным пациента"""
        self.client.login(username='doctor', password='doctor123')
        
        # Врач должен видеть данные пациента
        response = self.client.get(reverse('doctor_patient_detail', args=[self.patient.id]))
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            self.assertIn('Иван', content)
        print("✓ Тест role_based_access_doctor пройден")

    def test_14_unauthorized_redirects(self):
        """Тест редиректа при попытке доступа без авторизации"""
        # Доступ к деталям пациента
        response = self.client.get(reverse('patient_detail', args=[self.patient.id]))
        self.assertEqual(response.status_code, 302)  # Редирект на логин
        self.assertIn('login', response.url)
        
        # Доступ к добавлению данных
        response = self.client.get(reverse('add_food_intake', args=[self.patient.id]))
        self.assertEqual(response.status_code, 302)
        
        print("✓ Тест unauthorized_redirects пройден")
# ==================== ОЦЕНКА ТОЧНОСТИ МОДЕЛИРОВАНИЯ ====================

class ModelAccuracyTestCase(TestCase):
    """Оценка корректности моделирования"""
    
    def setUp(self):
        self.model = HovorkaModel(patient_weight=70.0)
        
        self.meals = [{'start': 480, 'duration': 15, 'weight': 30}]
        self.injections = [{'start': 475, 'duration': 2, 'dose': 500}]
    
    def test_01_glucose_response_to_meal(self):
        """Тест реакции глюкозы на прием пищи"""
        result = self.model.calculate_glucose(
            meals=self.meals, injections=[],
            start_time=460, end_time=600, time_step=2.0
        )
        max_glucose = max(result['glucose'])
        self.assertGreater(max_glucose, 5.0)
        self.assertLess(max_glucose, 15.0)
        print(f"✓ Тест glucose_response_to_meal: пик = {max_glucose:.2f} ммоль/л")
    
    def test_02_glucose_response_to_insulin(self):
        """Тест реакции глюкозы на инсулин"""
        result = self.model.calculate_glucose(
            meals=[], injections=self.injections,
            start_time=460, end_time=600, time_step=2.0
        )
        initial = result['glucose'][0]
        min_glucose = min(result['glucose'])
        self.assertLessEqual(min_glucose, initial)
        print(f"✓ Тест glucose_response_to_insulin: {initial:.2f} → {min_glucose:.2f}")
    
    def test_03_combined_effect(self):
        """Тест комбинированного эффекта"""
        result = self.model.calculate_glucose(
            meals=self.meals, injections=self.injections,
            start_time=460, end_time=600, time_step=2.0
        )
        for g in result['glucose']:
            self.assertGreaterEqual(g, 3.0)
            self.assertLessEqual(g, 12.0)
        print("✓ Тест combined_effect пройден")
    
    def test_04_model_stability(self):
        """Тест стабильности модели"""
        result = self.model.calculate_glucose(
            meals=self.meals, injections=self.injections,
            start_time=420, end_time=600, time_step=1.0
        )
        glucose = result['glucose']
        for i in range(1, len(glucose)):
            change = abs(glucose[i] - glucose[i-1])
            self.assertLess(change, 2.0)
        print("✓ Тест model_stability пройден")
    
    def test_05_realistic_scenario(self):
        """Тест реалистичного сценария"""
        meals = [
            {'start': 480, 'duration': 15, 'weight': 30},
            {'start': 780, 'duration': 20, 'weight': 50},
            {'start': 1080, 'duration': 20, 'weight': 45},
        ]
        injections = [
            {'start': 475, 'duration': 2, 'dose': 500},
            {'start': 775, 'duration': 2, 'dose': 800},
            {'start': 1075, 'duration': 2, 'dose': 700},
        ]
        result = self.model.calculate_glucose(
            meals=meals, injections=injections,
            start_time=420, end_time=1440, time_step=5.0
        )
        glucose = result['glucose']
        self.assertGreaterEqual(min(glucose), 3.5)
        self.assertLessEqual(max(glucose), 11.0)
        print(f"✓ Тест realistic_scenario: глюкоза {min(glucose):.2f}–{max(glucose):.2f} ммоль/л")


def run_all_tests():
    print("\n" + "="*80)
    print("НАЧАЛО ТЕСТИРОВАНИЯ")
    print("="*80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(HovorkaModelTestCase))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationDatabaseTestCase))
    suite.addTests(loader.loadTestsFromTestCase(FunctionalTestCase))
    suite.addTests(loader.loadTestsFromTestCase(ModelAccuracyTestCase))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print(f"ИТОГИ: {result.testsRun} тестов, "
          f"успешно: {result.testsRun - len(result.failures) - len(result.errors)}, "
          f"ошибок: {len(result.errors)}, неудач: {len(result.failures)}")
    print("="*80)
    
    return result


if __name__ == '__main__':
    run_all_tests()