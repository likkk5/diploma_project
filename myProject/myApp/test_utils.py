# myApp/test_utils.py
from django.db import connection
from datetime import date

class TestDataCreator:
    """Класс для создания тестовых данных через raw SQL"""
    
    @staticmethod
    def create_role(role_name):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO roles (role_name) VALUES (%s) RETURNING id",
                [role_name]
            )
            return cursor.fetchone()[0]
    
    @staticmethod
    def create_patient(user_id, role_id, first_name, last_name, birth_date, weight_kg, email):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO patient (user_id, role_id, first_name, last_name, 
                                   birth_date, weight_kg, email, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, [user_id, role_id, first_name, last_name, birth_date, weight_kg, email])
            return cursor.fetchone()[0]
    
    @staticmethod
    def create_doctor(user_id, role_id, first_name, last_name, email):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO doctor (user_id, role_id, first_name, last_name, email, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, [user_id, role_id, first_name, last_name, email])
            return cursor.fetchone()[0]
    
    @staticmethod
    def create_food_intake(patient_id, record_date, start_time, duration, carbs_weight):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO food_intake (patient_id, record_date, start_time, 
                                        duration, carbs_weight, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, [patient_id, record_date, start_time, duration, carbs_weight])
            return cursor.fetchone()[0]