from flask import Flask, request, jsonify
from flask_cors import CORS
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

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

def calculate_paces(average_pace: str, cycle: int) -> dict:
    minutes, seconds = map(int, average_pace.split(':'))
    base_seconds = minutes * 60 + seconds
    
    # Adjust pace based on the cycle
    adjustment = (cycle - 1) * 10
    base_seconds = max(base_seconds - adjustment, 180)  # Ensure it doesn't go below 3:00 min/km
    
    paces = {
        'very_fast': max(base_seconds - 30, 180),  # Not less than 3:00 min/km
        'fast': max(base_seconds, 210),  # Not less than 3:30 min/km
        'threshold': base_seconds + 30,
        'easy': base_seconds + 60
    }
    return {k: f"{int(v // 60)}:{int(v % 60):02d}" for k, v in paces.items()}

def adjust_pace(base_pace: str, adjustment: int) -> str:
    minutes, seconds = map(int, base_pace.split(':'))
    total_seconds = minutes * 60 + seconds + adjustment
    return f"{int(total_seconds // 60)}:{int(total_seconds % 60):02d}"

def generate_regenerative_session(date: str, distance: float) -> TrainingSession:
    return TrainingSession("Regenerativo", date, [
        Activity("Correr", distance=f"{distance:.1f}km", intensity="Leve")
    ])

def generate_interval_session(paces: dict, week: int, date: str, distance_factor: float) -> TrainingSession:
    week = (week - 1) % 6 + 1  # Adjust week to repeat every 6 weeks
    if week == 1:
        return TrainingSession("Intervalado", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 5x", repetitions=5, activities=[
                Activity("Correr", distance=f"{1 * distance_factor:.1f}km", pace=f"{paces['fast']} a {adjust_pace(paces['fast'], 5)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ])
    # ... (other weeks follow the same pattern)
    else:  # week 6
        return TrainingSession("Intervalado", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 2x", repetitions=2, activities=[
                Activity("Correr", distance=f"{1 * distance_factor:.1f}km", pace=f"{adjust_pace(paces['fast'], 5)} a {adjust_pace(paces['fast'], 10)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Repetir 3x", repetitions=3, activities=[
                Activity("Correr", distance=f"{0.5 * distance_factor:.1f}km", pace=f"{adjust_pace(paces['fast'], -15)} a {adjust_pace(paces['fast'], -10)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Repetir 5x", repetitions=5, activities=[
                Activity("Correr", distance=f"{0.2 * distance_factor:.1f}km", intensity="Muito forte"),
                Activity("Descansar", duration="1min30seg", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ])

def generate_threshold_session(paces: dict, week: int, date: str, distance_factor: float) -> TrainingSession:
    week = (week - 1) % 6 + 1  # Adjust week to repeat every 6 weeks
    if week == 1:
        return TrainingSession("Progressivo", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 5x", repetitions=5, activities=[
                Activity("Correr", distance=f"{1 * distance_factor:.1f}km", pace=f"{paces['fast']} a {adjust_pace(paces['fast'], 5)} min/km"),
                Activity("Descansar", duration="2min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ])
    # ... (other weeks follow the same pattern)
    else:  # week 6
        return TrainingSession("Limiar", date, [
            Activity("Aquecer", duration="8min", intensity="Trote leve"),
            Activity("Descansar", duration="3min", intensity="Livre"),
            Activity("Repetir 2x", repetitions=2, activities=[
                Activity("Correr", distance=f"{3.5 * distance_factor:.1f}km", pace=f"{adjust_pace(paces['fast'], 25)} a {adjust_pace(paces['fast'], 30)} min/km"),
                Activity("Descansar", duration="4min", intensity="Livre")
            ]),
            Activity("Desaquecer", duration="6min", intensity="Livre")
        ])

def calculate_base_long_run_distance(average_pace: str) -> float:
    minutes, seconds = map(int, average_pace.split(':'))
    pace_seconds = minutes * 60 + seconds
    
    if pace_seconds < 300:  # Less than 5:00 min/km
        return 12
    elif pace_seconds < 360:  # Less than 6:00 min/km
        return 10
    elif pace_seconds < 420:  # Less than 7:00 min/km
        return 8
    else:
        return 6

def calculate_long_run_distance(base_distance: float, week: int) -> float:
    increase_rate = 0.5  # 0.5 km per week
    max_increase = 5  # Maximum total increase (5 km)

    increased_distance = base_distance + (week - 1) * increase_rate
    capped_distance = min(increased_distance, base_distance + max_increase)
    
    return capped_distance

def generate_long_run_session(average_pace: str, week: int, date: str) -> TrainingSession:
    base_distance = calculate_base_long_run_distance(average_pace)
    distance = calculate_long_run_distance(base_distance, week)

    return TrainingSession("Longo", date, [
        Activity("Correr", distance=f"{distance:.1f}km", intensity="Livre")
    ])

def generate_training_plan(average_pace: str, start_date: str, num_weeks: int) -> dict:
    plan = {}
    current_date = datetime.strptime(start_date, "%d/%m/%Y")
    
    for week in range(1, num_weeks + 1):
        cycle = (week - 1) // 6 + 1
        paces = calculate_paces(average_pace, cycle)
        
        base_distance = calculate_base_long_run_distance(average_pace)
        long_run_distance = calculate_long_run_distance(base_distance, week)
        distance_factor = long_run_distance / base_distance

        week_sessions = []
        for day in range(4):  # 4 sessions per week
            date_str = current_date.strftime("%d/%m")
            if day == 0:
                week_sessions.append(generate_regenerative_session(date_str, 7 * distance_factor))
            elif day == 1:
                week_sessions.append(generate_interval_session(paces, week, date_str, distance_factor))
            elif day == 2:
                week_sessions.append(generate_threshold_session(paces, week, date_str, distance_factor))
            else:
                week_sessions.append(generate_long_run_session(average_pace, week, date_str))
            current_date += timedelta(days=2)  # Add 2 days for next session
        
        plan[f"Semana {week}"] = week_sessions
    
    return plan

@app.route('/calculate', methods=['POST', 'OPTIONS'])
def calculate():
    if request.method == "OPTIONS":
        return {"message": "OK"}, 200
    
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    required_fields = ['time5k', 'startDate', 'numWeeks']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        time_5k = int(data['time5k'])
        start_date = data['startDate']
        num_weeks = int(data['numWeeks'])
    except ValueError:
        return jsonify({"error": "Invalid data types. 'time5k' and 'numWeeks' should be integers"}), 400

    if time_5k <= 0 or num_weeks <= 0:
        return jsonify({"error": "'time5k' and 'numWeeks' should be positive integers"}), 400

    try:
        datetime.strptime(start_date, "%d/%m/%Y")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use DD/MM/YYYY"}), 400

    average_pace = f"{time_5k // 60}:{time_5k % 60:02d}"
    training_plan = generate_training_plan(average_pace, start_date, num_weeks)

    return jsonify(training_plan)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

if __name__ == '__main__':
    app.run(debug=True, port=8000)