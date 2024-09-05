from flask import Flask, request, jsonify
from flask_cors import CORS
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

@dataclass
class Activity:
    description: str
    distance: Optional[str] = None
    duration: Optional[str] = None
    pace: Optional[str] = None
    intensity: Optional[str] = None
    repetitions: Optional[int] = None
    activities: Optional[List['Activity']] = None

    def __post_init__(self):
        if self.activities is None:
            self.activities = []

@dataclass
class TrainingSession:
    type: str
    date: str
    activities: List[Activity]
    base_distance: float  # Adicionado campo para distância base

def calculate_paces(average_pace: str) -> dict:
    minutes, seconds = map(int, average_pace.split(':'))
    base_seconds = minutes * 60 + seconds
    
    paces = {
        'very_fast': max(base_seconds - 30, 180),  # Não menor que 3:00 min/km
        'fast': max(base_seconds, 210),  # Não menor que 3:30 min/km
        'threshold': base_seconds + 30,
        'easy': base_seconds + 60
    }
    return {k: f"{int(v // 60)}:{int(v % 60):02d}" for k, v in paces.items()}

def adjust_pace(base_pace: str, adjustment: int) -> str:
    minutes, seconds = map(int, base_pace.split(':'))
    total_seconds = minutes * 60 + seconds + adjustment
    return f"{int(total_seconds // 60)}:{int(total_seconds % 60):02d}"

def generate_regenerative_session(date: str, week: int, base_distance: float) -> TrainingSession:
    distance_multiplier = calculate_distance_multiplier(week)
    base_regenerative_distance = base_distance * 0.7  # 70% da distância base

    return TrainingSession("Regenerativo", date, [
        Activity("Correr", distance=f"{base_regenerative_distance * distance_multiplier:.1f}km", intensity="Leve")
    ], base_distance)

def calculate_distance_multiplier(week: int) -> float:
    cycle = (week - 1) // 6  # Determina em qual ciclo de 6 semanas estamos
    return 1 + (0.2 * cycle)  # 20% de aumento a cada ciclo

def km_to_minutes(km):
    return int(km * 1)  # Assumindo um ritmo médio de 1 min/km

def generate_interval_session(paces: dict, week: int, date: str, base_distance: float) -> TrainingSession:
    distance_multiplier = calculate_distance_multiplier(week)
    
    if week % 6 == 1:
        interval_distance = base_distance * 0.1  # 10% da distância base
        return TrainingSession("Intervalado", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 5x", repetitions=5, activities=[
                Activity("Correr", distance=f"{interval_distance * distance_multiplier:.1f}km", pace=f"{paces['fast']} a {adjust_pace(paces['fast'], 5)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    elif week % 6 == 2:
        interval_distance = base_distance * 0.05  # 5% da distância base
        return TrainingSession("Intervalado", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 3x", repetitions=3, activities=[
                Activity("Correr", distance=f"{0.5 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 5)} a {adjust_pace(paces['fast'], 10)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Repetir 3x", repetitions=3, activities=[
                Activity("Correr", distance=f"{0.4 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], -5)} a {paces['fast']} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    elif week % 6 == 3:
        interval_distance = base_distance * 0.12  # 12% da distância base
        return TrainingSession("Intervalado", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 3x", repetitions=3, activities=[
                Activity("Correr", distance=f"{0.12 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 15)} a {adjust_pace(paces['fast'], 20)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre"),
                Activity("Correr", distance=f"{0.06 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], -15)} a {adjust_pace(paces['fast'], -10)} min/km")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    elif week % 6 == 4:
        interval_distance = base_distance * 0.04  # 4% da distância base
        return TrainingSession("Intervalado", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 12x", repetitions=12, activities=[
                Activity("Correr", distance=f"{0.04 * base_distance * distance_multiplier:.1f}km", pace=f"{paces['very_fast']} a {adjust_pace(paces['very_fast'], 5)} min/km"),
                Activity("Descansar", duration="1min30seg", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    elif week % 6 == 5:
        interval_distance = base_distance * 0.08  # 8% da distância base
        return TrainingSession("Intervalado", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 6x", repetitions=6, activities=[
                Activity("Correr", distance=f"{0.08 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], -5)} a {paces['fast']} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    else:  # week % 6 == 0
        interval_distance = base_distance * 0.02  # 2% da distância base
        return TrainingSession("Intervalado", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 2x", repetitions=2, activities=[
                Activity("Correr", distance=f"{0.1 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 5)} a {adjust_pace(paces['fast'], 10)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Repetir 3x", repetitions=3, activities=[
                Activity("Correr", distance=f"{0.05 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], -15)} a {adjust_pace(paces['fast'], -10)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Repetir 5x", repetitions=5, activities=[
                Activity("Correr", distance=f"{0.02 * base_distance * distance_multiplier:.1f}km", intensity="Muito forte"),
                Activity("Descansar", duration="1min30seg", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)

def generate_threshold_session(paces: dict, week: int, date: str, base_distance: float) -> TrainingSession:
    distance_multiplier = calculate_distance_multiplier(week)
    
    if week % 6 == 1:
        threshold_distance = base_distance * 0.1  # 10% da distância base
        return TrainingSession("Progressivo", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 5x", repetitions=5, activities=[
                Activity("Correr", distance=f"{threshold_distance * distance_multiplier:.1f}km", pace=f"{paces['fast']} a {adjust_pace(paces['fast'], 5)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    elif week % 6 == 2:
        threshold_distance = base_distance * 0.15  # 15% da distância base
        return TrainingSession("Limiar", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 2x", repetitions=2, activities=[
                Activity("Correr", distance=f"{0.15 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 35)} a {adjust_pace(paces['fast'], 40)} min/km"),
                Activity("Descansar", duration="2min30seg", intensity="Livre")
            ]),
            Activity("Repetir 2x", repetitions=2, activities=[
                Activity("Correr", distance=f"{0.12 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 25)} a {adjust_pace(paces['fast'], 30)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    elif week % 6 == 3:
        threshold_distance = base_distance * 0.07  # 7% da distância base
        return TrainingSession("Fartlek", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 6x", repetitions=6, activities=[
                Activity("Correr", distance=f"{0.07 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 25)} a {adjust_pace(paces['fast'], 30)} min/km"),
                Activity("Correr", distance=f"{0.03 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['easy'], 5)} a {adjust_pace(paces['easy'], 10)} min/km")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    elif week % 6 == 4:
        threshold_distance = base_distance * 0.4  # 40% da distância base
        return TrainingSession("Limiar", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Correr", distance=f"{0.4 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 35)} a {adjust_pace(paces['fast'], 40)} min/km"),
            Activity("Descansar", duration="4min", intensity="Livre"),
            Activity("Correr", distance=f"{0.2 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 25)} a {adjust_pace(paces['fast'], 30)} min/km"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Correr", distance=f"{0.1 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 25)} a {adjust_pace(paces['fast'], 30)} min/km"),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    elif week % 6 == 5:
        threshold_distance = base_distance * 0.5  # 50% da distância base
        return TrainingSession("Limiar", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Correr", distance=f"{0.5 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 35)} a {adjust_pace(paces['fast'], 40)} min/km"),
            Activity("Descansar", duration="4min", intensity="Livre"),
            Activity("Correr", distance=f"{0.2 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 25)} a {adjust_pace(paces['fast'], 30)} min/km"),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    else:  # week % 6 == 0
        threshold_distance = base_distance * 0.35  # 35% da distância base
        return TrainingSession("Limiar", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 2x", repetitions=2, activities=[
                Activity("Correr", distance=f"{0.35 * base_distance * distance_multiplier:.1f}km", pace=f"{adjust_pace(paces['fast'], 25)} a {adjust_pace(paces['fast'], 30)} min/km"),
                Activity("Descansar", duration="4min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ], base_distance)
    
def calculate_base_long_run_distance(average_pace: str, base_distance: float) -> float:
    minutes, seconds = map(int, average_pace.split(':'))
    pace_seconds = minutes * 60 + seconds
    
    # Ajuste a distância base de acordo com o pace
    if pace_seconds < 300:  # Menos de 5:00 min/km
        return base_distance * 1.2
    elif pace_seconds < 360:  # Menos de 6:00 min/km
        return base_distance
    elif pace_seconds < 420:  # Menos de 7:00 min/km
        return base_distance * 0.8
    else:
        return base_distance * 0.6

def calculate_long_run_distance(base_distance: float, week: int) -> float:
    cycle = (week - 1) // 6  # Determina em qual ciclo de 6 semanas estamos
    increase_factor = 1 + (0.2 * cycle)  # 20% de aumento a cada ciclo
    return round(base_distance * increase_factor, 1)

def generate_long_run_session(average_pace: str, week: int, date: str, base_distance: float) -> TrainingSession:
    base_long_run_distance = calculate_base_long_run_distance(average_pace, base_distance)
    distance = calculate_long_run_distance(base_long_run_distance, week)

    return TrainingSession("Longo", date, [
        Activity("Correr", distance=f"{distance:.1f}km", intensity="Livre")
    ], base_distance)

def generate_training_plan(average_pace: str, start_date: str, num_weeks: int, base_distance: float) -> dict:
    plan = {}
    paces = calculate_paces(average_pace)
    current_date = datetime.strptime(start_date, "%d/%m/%Y")
    
    for week in range(1, num_weeks + 1):
        cycle_week = (week - 1) % 6 + 1
        cycle_number = (week - 1) // 6 + 1
        
        adjusted_paces = {k: adjust_pace(v, -10 * (cycle_number - 1)) for k, v in paces.items()}
        
        week_sessions = []
        for day in range(4):
            date_str = current_date.strftime("%d/%m")
            if day == 0:
                week_sessions.append(generate_regenerative_session(date_str, week, base_distance))
            elif day == 1:
                week_sessions.append(generate_interval_session(adjusted_paces, week, date_str, base_distance))
            elif day == 2:
                week_sessions.append(generate_threshold_session(adjusted_paces, week, date_str, base_distance))
            else:
                week_sessions.append(generate_long_run_session(average_pace, week, date_str, base_distance))
            current_date += timedelta(days=2)
        
        plan[f"Semana {week}"] = week_sessions
    
    return plan

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    time_min = int(data['minutes'])
    time_sec = int(data['seconds'])
    average_pace = f"{time_min}:{time_sec:02d}"
    start_date = data.get('start_date', datetime.now().strftime("%d/%m/%Y"))
    num_weeks = int(data.get('num_weeks', 6))
    base_distance = float(data.get('base_distance', 10))  # Nova entrada para distância base
    
    plan = generate_training_plan(average_pace, start_date, num_weeks, base_distance)
    
    return jsonify({
        'pace': f"{average_pace} min/km",
        'base_distance': f"{base_distance} km",
        'plan': plan
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)