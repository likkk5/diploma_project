def user_context(request):
    context = {
        'is_patient': False,
        'is_doctor': False,
        'patient_id': None,
    }
    
    if request.user.is_authenticated:
        # Проверяем, является ли пользователь пациентом
        if hasattr(request.user, 'patient_profile'):
            context['is_patient'] = True
            context['patient_id'] = request.user.patient_profile.id
        
        # Проверяем, является ли пользователем врачом
        elif hasattr(request.user, 'doctor_profile'):
            context['is_doctor'] = True
    
    return context