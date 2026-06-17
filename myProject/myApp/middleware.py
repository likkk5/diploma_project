from django.shortcuts import redirect

class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Список путей, доступных без авторизации
        public_paths = ['/', '/login/', '/register/']
        
        current_path = request.path
        
        # Проверяем, является ли путь публичным
        is_public = any(current_path.startswith(path) for path in public_paths)
        
        # Если путь не публичный и пользователь не авторизован
        if not is_public and 'user_id' not in request.session:
            return redirect('login')
        
        response = self.get_response(request)
        return response