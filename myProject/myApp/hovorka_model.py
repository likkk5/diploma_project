import numpy as np
from scipy.integrate import odeint
import math


class HovorkaModel:
    """
    Переменные состояния: [D1, D2, Q1, Q2, S1, S2, I, x1, x2, x3]
    """
    
    def __init__(self, patient_weight=60.0, custom_params=None):
        self.W = float(patient_weight)
        
        # Константы модели
        self.k12 = 0.066      # скорость переноса глюкозы (1/мин)
        self.ka1 = 0.006      # скорость действия x1 (1/мин)
        self.ka2 = 0.06       # скорость действия x2 (1/мин)
        self.ka3 = 0.03       # скорость действия x3 (1/мин)
        self.ke = 0.138       # скорость выведения инсулина (1/мин)
        
        # Параметры чувствительности к инсулину
        self.kb1 = 0.000307   # 3.07e-4 (L/(mU*min))
        # self.kb1 = 0.000049024   # 3.07e-4 (L/(mU*min))
        self.kb2 = 0.0000492  # 4.92e-5 (L/(mU*min))
        # self.kb2 = 0.000007216  # 4.92e-5 (L/(mU*min))
        self.kb3 = 0.0016     # 1.6e-3 (L/(mU*min))
        # self.kb3 = 0.0015     # 1.6e-3 (L/(mU*min))
        
        # Базовые скорости (зависят от веса)
        self.EGP0 = 0.0   # эндогенная продукция глюкозы (ммоль/мин)
        self.F01 = 0.0    # потребление глюкозы ЦНС (ммоль/мин)
        
        # Объемы распределения
        self.VG = 0.16     # объем глюкозы (литры)
        self.VI = 0.12     # объем инсулина (литры)
        
        # Параметры абсорбции пищи
        self.tau_D = 40.0             # τD - время абсорбции (мин)
        self.AG = 0.8                 # параметр биоактивности углеводной пищи
        
        # Молекулярная масса глюкозы
        self.MwG = 180.0              # г/ммоль
        
        # Время абсорбции инсулина 
        self.tau_s = 55.0
        
        # Базальный инсулин 
        self.I_basal = 20.0           # мкЕд/мл

        self.initial_D1 = 0.0
        self.initial_D2 = 0.0
        self.initial_Q1 = 65.0
        self.initial_Q2 = 10.0
        self.initial_S1 = 0.0
        self.initial_S2 = 0.0
        self.initial_I = 0.0
        self.initial_x1 = 0.0634
        self.initial_x2 = 0.0005
        self.initial_x3 = 0.3138

        print("\n--- БАЗОВЫЕ ПАРАМЕТРЫ (ДО ПРИМЕНЕНИЯ ПОЛЬЗОВАТЕЛЬСКИХ) ---")
        print(f"k12 (скорость переноса глюкозы) = {self.k12}")
        print(f"ka1 = {self.ka1}, ka2 = {self.ka2}, ka3 = {self.ka3}")
        print(f"ke = {self.ke}")
        print(f"kb1 = {self.kb1}, kb2 = {self.kb2}, kb3 = {self.kb3}")
        print(f"EGP0 = {self.EGP0}")
        print(f"F01 = {self.F01}")
        print(f"VG = {self.VG}")
        print(f"VI = {self.VI}")
        print(f"tau_D = {self.tau_D}")
        print(f"tau_s = {self.tau_s}")
        print(f"I_basal = {self.I_basal}")

        if custom_params:
            print("\n--- ПОЛЬЗОВАТЕЛЬСКИЕ ПАРАМЕТРЫ (из БД) ---")
            for key, value in custom_params.items():
                print(f"{key} = {value}")
            
            if custom_params.get('glucose_transfer_rate'):
                self.k12 = float(custom_params['glucose_transfer_rate'])
                print(f"  -> k12 изменен на {self.k12}")
            if custom_params.get('insulin_absorption_coefficient'):
                self.kb1 = float(custom_params['insulin_absorption_coefficient'])
                print(f"  -> kb1 изменен на {self.kb1}")
            if custom_params.get('insulin_distribution_rate'):
                self.kb2 = float(custom_params['insulin_distribution_rate'])
                print(f"  -> kb2 изменен на {self.kb2}")
            if custom_params.get('insulin_effect_on_glucose_liver'):
                self.kb3 = float(custom_params['insulin_effect_on_glucose_liver'])
                print(f"  -> kb3 изменен на {self.kb3}")
            if custom_params.get('liver_glucose_production_rate'):
                self.EGP0 = float(custom_params['liver_glucose_production_rate'])
                print(f"  -> EGP0 изменен на {self.EGP0}")
            if custom_params.get('glucose_consumption_rate'):
                self.F01 = float(custom_params['glucose_consumption_rate'])
                print(f"  -> F01 изменен на {self.F01}")
            if custom_params.get('meal_absorption_time'):
                self.tau_D = float(custom_params['meal_absorption_time'])
                print(f"  -> tau_D изменен на {self.tau_D}")
            if custom_params.get('insulin_absorption_time'):
                self.tau_s = float(custom_params['insulin_absorption_time'])
                print(f"  -> tau_s изменен на {self.tau_s}")
            if custom_params.get('glucose_deactivation_distribution') is not None:
                self.ka1 = float(custom_params['glucose_deactivation_distribution'])
            if custom_params.get('glucose_deactivation_utilization') is not None:
                self.ka2 = float(custom_params['glucose_deactivation_utilization'])
            if custom_params.get('glucose_deactivation_liver') is not None:
                self.ka3 = float(custom_params['glucose_deactivation_liver'])
            if custom_params.get('glucose_distribution_volume') is not None:
                self.VG = float(custom_params['glucose_distribution_volume'])
            if custom_params.get('insulin_distribution_volume') is not None:
                self.VI = float(custom_params['insulin_distribution_volume'])
            if custom_params.get('bioavailability') is not None:
                self.AG = float(custom_params['bioavailability'])  
            if custom_params.get('insulin_elimination_rate') is not None:
                self.ke = float(custom_params['insulin_elimination_rate'])
                print(f"  -> ke = {self.ke}")
            
            if custom_params.get('initial_D1') is not None:
                self.initial_D1 = float(custom_params['initial_D1'])
                print(f"  -> initial_D1 = {self.initial_D1}")
            if custom_params.get('initial_D2') is not None:
                self.initial_D2 = float(custom_params['initial_D2'])
                print(f"  -> initial_D2 = {self.initial_D2}")
            if custom_params.get('initial_Q1') is not None:
                self.initial_Q1 = float(custom_params['initial_Q1'])
                print(f"  -> initial_Q1 = {self.initial_Q1}")
            if custom_params.get('initial_Q2') is not None:
                self.initial_Q2 = float(custom_params['initial_Q2'])
                print(f"  -> initial_Q2 = {self.initial_Q2}")
            if custom_params.get('initial_S1') is not None:
                self.initial_S1 = float(custom_params['initial_S1'])
                print(f"  -> initial_S1 = {self.initial_S1}")
            if custom_params.get('initial_S2') is not None:
                self.initial_S2 = float(custom_params['initial_S2'])
                print(f"  -> initial_S2 = {self.initial_S2}")
            if custom_params.get('initial_I') is not None:
                self.initial_I = float(custom_params['initial_I'])
                print(f"  -> initial_I = {self.initial_I}")
            if custom_params.get('initial_x1') is not None:
                self.initial_x1 = float(custom_params['initial_x1'])
                print(f"  -> initial_x1 = {self.initial_x1}")
            if custom_params.get('initial_x2') is not None:
                self.initial_x2 = float(custom_params['initial_x2'])
                print(f"  -> initial_x2 = {self.initial_x2}")
            if custom_params.get('initial_x3') is not None:
                self.initial_x3 = float(custom_params['initial_x3'])
                print(f"  -> initial_x3 = {self.initial_x3}")      
        else:
            print("\n--- ПОЛЬЗОВАТЕЛЬСКИХ ПАРАМЕТРОВ НЕТ (custom_params = None) ---")

        # Базальные значения x1, x2, x3 (при I = I_basal, dx/dt = 0)
        self.x1_basal = self.kb1 * self.I_basal / self.ka1
        self.x2_basal = self.kb2 * self.I_basal / self.ka2
        self.x3_basal = self.kb3 * self.I_basal / self.ka3
    
    #  ФУНКЦИЯ ПРИЕМА ПИЩИ
    def food_intake_rate(self, t, meals):
        """
        Скорость приема углеводной пищи v(t) (г/мин)
        По формуле food2 (треугольная форма)
        """
        rate = 0.0
        for meal in meals:
            tau = meal['start']       # начало приема (мин)
            a = meal['duration']      # длительность (мин)
            m = float(meal['weight']) # вес углеводов (г)
            
            if tau <= t <= tau + a:
                half = a / 2.0
                if t <= tau + half:
                    # Нарастающая фаза
                    rate += (4 * m * (t - tau)) / (a * a)
                else:
                    # Спадающая фаза
                    rate += (2* m / a) - (4 * m * (t - tau - half)) / (a * a)
        return rate
    # def food_intake_rate(self, t, meals):
    #     """Скорость приема пищи v(t) - ФОРМА food1 (прямоугольная)"""
    #     rate = 0.0
    #     for meal in meals:
    #         tau = meal['start']
    #         a = meal['duration']
    #         m = float(meal['weight'])
    #         if tau <= t <= tau + a:
    #             rate += m / a      
    #     return rate

    #  СКОРОСТЬ ВВОДА УГЛЕВОДОВ D(t) 
    def D_t(self, t, meals):
        """Скорость ввода углеводной пищи D(t) (ммоль/мин)"""
        v_t = self.food_intake_rate(t, meals)
        return 1000.0 * v_t / self.MwG
    
    # ИНЪЕКЦИИ ИНСУЛИНА 
    def insulin_injection_rate(self, t, injections):
        """
        Скорость введения инсулина u(t) (mU/мин)
        По формуле μ(t, ξ, β, l) (треугольная форма)
        Дозы в mU (1 единица = 1000 mU)
        """
        rate = 0.0
        for inj in injections:
            xi = inj['start']         # начало инъекции (мин)
            beta = inj['duration']    # продолжительность (мин)
            l = float(inj['dose'])    # доза в mU
            
            if xi <= t <= xi + beta:
                half = beta / 2.0
                if t <= xi + half:
                    # Нарастающая фаза
                    rate += (4 * l * (t - xi)) / (beta * beta)
                else:
                    # Спадающая фаза
                    rate += (2 * l / beta) - (4 * l * (t - xi - half)) / (beta * beta)
    
        return rate  # возвращает mU/мин
    
    # ПОЧЕЧНАЯ РЕАБСОРБЦИЯ 
    def renal_glucose_uptake(self, G):
        """Скорость поглощения глюкозы почками FR(t) (ммоль/мин)"""
        if G >= 9.0:
            return 0.003 * (G - 9.0) * self.VG * self.W 
        return 0.0
    
    def system_equations(self, state, t, meals, injections):
        """
        Система ОДУ модели Ховорка (10 переменных состояния)
        state = [D1, D2, Q1, Q2, S1, S2, I, x1, x2, x3]
        """
        
        # Распаковка состояния
        D1, D2, Q1, Q2, S1, S2, I, x1, x2, x3 = state
        
        # Входные воздействия
        D_val = self.D_t(t, meals)                    # D(t) - ммоль/мин
        u_val = self.insulin_injection_rate(t, injections)  # u(t) - mU/мин
        
        # ПОДСИСТЕМА ГЛЮКОЗЫ ИЗ ПИЩИ (2.12)
        dD1_dt = self.AG * D_val - D1 / self.tau_D
        dD2_dt = (D1 - D2) / self.tau_D
        
        # Скорость всасывания глюкозы UG(t)
        UG = D2 / self.tau_D
        
        # ПОДСИСТЕМА РАСПРОСТРАНЕНИЯ ГЛЮКОЗЫ
        # Потребление глюкозы ЦНС F01^c(t)
        G_conc = Q1 / (self.VG * self.W)  # концентрация глюкозы в крови
        if G_conc >= 4.5:
            F01_c = (self.F01 * self.W)
        else:
            F01_c = (self.F01 * self.W) * G_conc / 4.5
        
        # Почечная реабсорбция FR(t)
        FR = self.renal_glucose_uptake(G_conc)
        
        # Эндогенная продукция глюкозы EGP(t)
        EGP = self.EGP0 * self.W * (1 - x3)
        
        # Уравнение dQ1/dt
        dQ1_dt = UG - F01_c - FR - x1 * Q1 + self.k12 * Q2 + EGP
        
        # Уравнение dQ2/dt
        dQ2_dt = x1 * Q1 - (self.k12 + x2) * Q2
        
        # ПОДСИСТЕМА ИНСУЛИНА 
        # Скорость поступления инсулина в плазму UI(t)
        UI = S2 / self.tau_s
        
        dS1_dt = -S1 / self.tau_s + u_val
        dS2_dt = (S1 - S2) / self.tau_s
        dI_dt = UI / (self.VI * self.W) - self.ke * I
        
        # ПОДСИСТЕМА ДЕЙСТВИЯ ИНСУЛИНА
        dx1_dt = -self.ka1 * x1 + self.kb1 * I
        dx2_dt = -self.ka2 * x2 + self.kb2 * I
        dx3_dt = -self.ka3 * x3 + self.kb3 * I
        
        return [dD1_dt, dD2_dt, dQ1_dt, dQ2_dt, dS1_dt, dS2_dt, dI_dt, dx1_dt, dx2_dt, dx3_dt]
    
    def calculate_glucose(self, meals, injections, start_time=420, end_time=1440, time_step=0.1):
        """
        Расчет профиля глюкозы на заданном временном интервале
        start_time = произвольное
        end_time = 1440 минут (24:00)
        time_step = 0.1 минут (маленький шаг для точности)
        """
        
        times = np.arange(start_time, end_time + time_step, time_step)
        
        # print(f"Расчет начальных условий с 0 до {start_time} мин...")
        # times_init = np.arange(0, start_time + 1, 1.0)
        

        initial_state_init = [
            self.initial_D1,   # D1 - глюкоза в желудке (ммоль)
            self.initial_D2,   # D2 - глюкоза в кишечнике (ммоль)
            self.initial_Q1,   # Q1 - глюкоза в крови (ммоль)
            self.initial_Q2,   # Q2 - глюкоза в тканях (ммоль)
            self.initial_S1,   # S1 - депо инсулина 1 (mU)
            self.initial_S2,   # S2 - депо инсулина 2 (mU)
            self.initial_I,    # I - концентрация инсулина (mU/L)
            self.initial_x1,   # x1 - базальное действие инсулина
            self.initial_x2,   # x2 - базальное действие инсулина
            self.initial_x3,   # x3 - базальное действие инсулина
        ]
        # пример акулич 2
        # initial_state_init = [
        #     0.0,                    # D1 - глюкоза в желудке (ммоль)
        #     0.0,                   # D2 - глюкоза в кишечнике (ммоль)
        #     65.0,             # Q1 - глюкоза в крови (ммоль)
        #     10.0,                    # Q2 - глюкоза в тканях (ммоль)
        #     0.0,                    # S1 - депо инсулина 1 (mU)
        #     0.0,                  # S2 - депо инсулина 2 (mU)
        #     0.0,                   # I - концентрация инсулина (mU/L)
        #     0.0634,      # x1 - базальное действие инсулина
        #     0.0005,       # x2 - базальное действие инсулина
        #     0.3138,      # x3 - базальное действие инсулина
        # ]
        #пример акулич 3
        # initial_state_init = [
        #             0.0,                    # D1 - глюкоза в желудке (ммоль)
        #             0.0,                   # D2 - глюкоза в кишечнике (ммоль)
        #             70.0,             # Q1 - глюкоза в крови (ммоль)
        #             7.0,                    # Q2 - глюкоза в тканях (ммоль)
        #             0.0,                    # S1 - депо инсулина 1 (mU)
        #             0.0,                  # S2 - депо инсулина 2 (mU)
        #             0.0,                   # I - концентрация инсулина (mU/L)
        #             0.055,      # x1 - базальное действие инсулина
        #             0.0008,       # x2 - базальное действие инсулина
        #             0.0005,      # x3 - базальное действие инсулина
        #         ]
        # #пример 1 маллазия
        # initial_state_init = [
        #             30.0,                    # D1 - глюкоза в желудке (ммоль)
        #             7.0,                   # D2 - глюкоза в кишечнике (ммоль)
        #             70.0,             # Q1 - глюкоза в крови (ммоль)
        #             20.0,                    # Q2 - глюкоза в тканях (ммоль)
        #             0.0,                    # S1 - депо инсулина 1 (mU)
        #             0.0,                  # S2 - депо инсулина 2 (mU)
        #             0.0,                   # I - концентрация инсулина (mU/L)
        #             0.0,      # x1 - базальное действие инсулина
        #             0.0,       # x2 - базальное действие инсулина
        #             0.0,      # x3 - базальное действие инсулина
        #         ]
        # # Решение для начального периода
        # solution_init = odeint(
        #     self.system_equations,
        #     initial_state_init,
        #     times_init,
        #     args=(meals, injections),
        #     rtol=1e-8,
        #     atol=1e-10,
        #     hmax=0.5 
        # )
        
        # Берем последнее состояние как начальное для основного периода
        # initial_state = solution_init[-1, :]
        initial_state = initial_state_init
        print(f"Начальные условия в {start_time} мин: I = {initial_state[6]:.2f} mU/L, G = {initial_state[2]/(self.VG * self.W):.2f} mmol/L")
        
        # Решение системы ОДУ для основного периода с малым шагом
        print(f"Расчет основного периода с {start_time} до {end_time} мин, шаг {time_step} мин...")
        solution = odeint(
            self.system_equations,
            initial_state,
            times,
            args=(meals, injections),
            rtol=1e-8,
            atol=1e-10,
            hmax=0.5  # максимальный шаг 0.5 мин
        )
        
        # Концентрация глюкозы: G(t) = Q1(t) / VG
        glucose_conc = solution[:, 2] / (self.VG * self.W)
        food_rate = [self.food_intake_rate(t, meals) for t in times]
        insulin_rate = [self.insulin_injection_rate(t, injections) for t in times]

        print("\n--- ВЫБОРКА ЗНАЧЕНИЙ ГЛЮКОЗЫ ЗА ВСЕ ВРЕМЯ (10 случайных точек) ---")
        num_points = len(glucose_conc)
        random_indices = np.random.choice(num_points, size=min(10, num_points), replace=False)
        random_indices.sort()
        for idx in random_indices:
            time_hours = times[idx] / 60.0
            print(f"  Время: {time_hours:.1f} ч ({times[idx]:.0f} мин) -> Глюкоза: {glucose_conc[idx]:.2f} ммоль/л")
        print(f"Мин глюкоза: {min(glucose_conc):.2f} ммоль/л")
        print(f"Макс глюкоза: {max(glucose_conc):.2f} ммоль/л")
        print(f"Средняя глюкоза: {np.mean(glucose_conc):.2f} ммоль/л")
   

        return {
            'times': times.tolist(),
            'glucose': glucose_conc.tolist(),           # ммоль/л
            'insulin': solution[:, 6].tolist(),         # I (mU/L)
            'food_rate': food_rate,                     # г/мин
            'insulin_rate': insulin_rate,               # mU/мин
            'D1': solution[:, 0].tolist(),
            'D2': solution[:, 1].tolist(),
            'Q1': solution[:, 2].tolist(),
            'Q2': solution[:, 3].tolist(),
            'S1': solution[:, 4].tolist(),
            'S2': solution[:, 5].tolist(),
            'x1': solution[:, 7].tolist(),
            'x2': solution[:, 8].tolist(),
            'x3': solution[:, 9].tolist(),
            'UG': (solution[:, 1] / self.tau_D).tolist(),
            'D_t': [self.D_t(t, meals) for t in times],
        }
