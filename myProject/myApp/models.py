from django.db import models
from datetime import date

from django.contrib.auth.models import User

class Calculation(models.Model):
    patient = models.ForeignKey('Patient', models.DO_NOTHING)
    calculation_time = models.DateTimeField()
    glucose_forecast = models.DecimalField(max_digits=5, decimal_places=2)
    insulin_effect = models.DecimalField(max_digits=10, decimal_places=5)
    carbs_utilized = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'calculation'


class Charts(models.Model):
    patient = models.ForeignKey('Patient', models.DO_NOTHING)
    calculation = models.ForeignKey(Calculation, models.DO_NOTHING, blank=True, null=True)
    chart_type = models.CharField(max_length=50)
    data = models.JSONField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'charts'


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    role = models.ForeignKey('Roles', on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(unique=True, max_length=150)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doctor'
    
    def save(self, *args, **kwargs):
        self.email = self.user.email
        self.first_name = self.user.first_name
        self.last_name = self.user.last_name
        super().save(*args, **kwargs)

class DoctorPatient(models.Model):
    doctor = models.ForeignKey(Doctor, models.DO_NOTHING)
    patient = models.ForeignKey('Patient', models.DO_NOTHING)
    assignment_type = models.CharField(max_length=50, blank=True, null=True)
    assigned_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doctor_patient'
        unique_together = (('doctor', 'patient'),)


class FoodIntake(models.Model):
    patient = models.ForeignKey('Patient', models.DO_NOTHING)
    record_date = models.DateField(default=date.today)
    start_time = models.IntegerField()
    duration = models.IntegerField()
    carbs_weight = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'food_intake'


class GlucoseMeasurement(models.Model):
    patient = models.ForeignKey('Patient', models.DO_NOTHING)
    measurement_time = models.DateTimeField()
    glucose_level = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'glucose_measurement'


class InsulinInjection(models.Model):
    patient = models.ForeignKey('Patient', models.DO_NOTHING)
    record_date = models.DateField(default=date.today)
    start_time = models.IntegerField()
    duration = models.IntegerField()
    volume = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'insulin_injection'


class ModelConstants(models.Model):
    name = models.CharField(unique=True, max_length=150)
    value = models.DecimalField(max_digits=20, decimal_places=10)
    unit = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'model_constants'

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    role = models.ForeignKey('Roles', on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    birth_date = models.DateField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    email = models.CharField(unique=True, max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'patient'
    
    def save(self, *args, **kwargs):
        self.email = self.user.email
        self.first_name = self.user.first_name
        self.last_name = self.user.last_name
        super().save(*args, **kwargs)

class PatientHistory(models.Model):
    patient = models.ForeignKey(Patient, models.DO_NOTHING)
    doctor = models.ForeignKey(Doctor, models.DO_NOTHING, blank=True, null=True)
    user_role = models.CharField(max_length=20)
    action_type = models.CharField(max_length=100)
    action_time = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    doctor_patient = models.ForeignKey(DoctorPatient, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'patient_history'


class PatientParameters(models.Model):
    patient = models.OneToOneField(Patient, models.DO_NOTHING)
    bioavailability = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    glucose_transfer_rate = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    insulin_absorption_rate = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    glucose_deactivation_distribution = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    glucose_deactivation_utilization = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    glucose_deactivation_liver = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    meal_absorption_time = models.IntegerField(blank=True, null=True)
    glucose_distribution_volume = models.DecimalField(max_digits=5, decimal_places=3, blank=True, null=True)
    insulin_distribution_volume = models.DecimalField(max_digits=5, decimal_places=3, blank=True, null=True)
    insulin_absorption_time = models.IntegerField(blank=True, null=True)
    insulin_distribution_rate = models.DecimalField(max_digits=12, decimal_places=10, blank=True, null=True)
    insulin_absorption_coefficient = models.DecimalField(max_digits=12, decimal_places=10, blank=True, null=True)
    insulin_effect_on_glucose_liver = models.DecimalField(max_digits=12, decimal_places=10, blank=True, null=True)
    liver_glucose_production_rate = models.DecimalField(max_digits=7, decimal_places=5, blank=True, null=True)
    glucose_consumption_rate = models.DecimalField(max_digits=7, decimal_places=5, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    based_on_constant = models.ForeignKey(ModelConstants, models.DO_NOTHING, blank=True, null=True)

    insulin_elimination_rate = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    
    initial_D1 = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    initial_D2 = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    initial_Q1 = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    initial_Q2 = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    initial_S1 = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    initial_S2 = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    initial_I = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    initial_x1 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    initial_x2 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    initial_x3 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'patient_parameters'


class Roles(models.Model):
    role_name = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'roles'
