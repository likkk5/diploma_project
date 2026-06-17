from django.contrib import admin
from django.contrib.auth.models import User, Group

from .models import (
    Calculation, Charts, Doctor, DoctorPatient, FoodIntake,
    GlucoseMeasurement, InsulinInjection, ModelConstants,
    Patient, PatientHistory, PatientParameters, Roles
)

# Register your models here.
admin.site.register(Calculation)
admin.site.register(Charts)
admin.site.register(Doctor)
admin.site.register(DoctorPatient)
admin.site.register(FoodIntake)
admin.site.register(GlucoseMeasurement)
admin.site.register(InsulinInjection)
admin.site.register(ModelConstants)
admin.site.register(Patient)
admin.site.register(PatientHistory)
admin.site.register(PatientParameters)
admin.site.register(Roles)