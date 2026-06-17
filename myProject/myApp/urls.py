from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    path('change-role/<int:user_id>/', views.change_user_role, name='change_user_role'),
    
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patient/<int:patient_id>/parameters/', views.edit_patient_parameters, name='edit_patient_parameters'),
    path('patient/<int:patient_id>/add-food/', views.add_food_intake, name='add_food_intake'),
    path('patient/<int:patient_id>/add-insulin/', views.add_insulin_injection, name='add_insulin_injection'),
    path('patient/<int:patient_id>/edit_food/<int:item_id>/', views.edit_food_intake, name='edit_food_intake'),
    path('patient/<int:patient_id>/edit_insulin/<int:item_id>/', views.edit_insulin_injection, name='edit_insulin_injection'),
    path('patient/<int:patient_id>/delete_food/<int:item_id>/', views.delete_food_intake, name='delete_food_intake'),
    path('patient/<int:patient_id>/delete_insulin/<int:item_id>/', views.delete_insulin_injection, name='delete_insulin_injection'),
    path('patient/<int:patient_id>/profile/', views.patient_profile, name='patient_profile'),

    path('api/calculate/<int:patient_id>/', views.run_calculation, name='run_calculation'),
    path('api/calculation/<int:calculation_id>/', views.get_calculation_result, name='get_calculation_result'),

    path('manage_users/', views.manage_users, name='manage_users'),

    path('doctor/patients/', views.doctor_patients, name='doctor_patients'),
    path('doctor/patient/<int:patient_id>/', views.doctor_patient_detail, name='doctor_patient_detail'),

    path('manage-doctor-patients/', views.manage_doctor_patients, name='manage_doctor_patients'),
    path('assign-patient/', views.assign_patient_to_doctor, name='assign_patient_to_doctor'),
    path('remove-patient/<int:assignment_id>/', views.remove_patient_from_doctor, name='remove_patient_from_doctor'),
]