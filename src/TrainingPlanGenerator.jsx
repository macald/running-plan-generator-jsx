import React, { useState } from 'react';

const formatDistance = (distance) => {
  if (typeof distance === 'string' && distance.includes('km')) {
    const km = parseFloat(distance);
    if (km < 1) {
      return `${Math.round(km * 1000)}m`;
    } else if (Number.isInteger(km)) {
      return `${km.toFixed(0)}km`;
    } else {
      return `${km.toFixed(1)}km`;
    }
  }
  return distance;
};

const ActivityDisplay = ({ activity }) => (
  <li className="mb-1">
    {activity.description}
    {activity.distance && ` - ${formatDistance(activity.distance)}`}
    {activity.duration && ` - ${activity.duration}`}
    {activity.pace && ` - Pace: ${activity.pace}`}
    {activity.intensity && ` - Intensidade: ${activity.intensity}`}
    {activity.repetitions && (
      <ul className="list-disc pl-5 mt-1">
        {activity.activities.map((subActivity, index) => (
          <ActivityDisplay key={index} activity={subActivity} />
        ))}
      </ul>
    )}
  </li>
);

const TrainingSessionDisplay = ({ session }) => (
  <div className="mb-4">
    <h4 className="font-semibold text-lg">{session.type}</h4>
    <ul className="list-disc pl-5">
      {session.activities.map((activity, index) => (
        <ActivityDisplay key={index} activity={activity} />
      ))}
    </ul>
  </div>
);

const TrainingPlanDisplay = ({ plan }) => {
  // Função para extrair o número da semana
  const getWeekNumber = (weekString) => {
    return parseInt(weekString.match(/\d+/)[0]);
  };

  // Ordenar as semanas com base no número
  const sortedWeeks = Object.entries(plan).sort((a, b) => {
    return getWeekNumber(a[0]) - getWeekNumber(b[0]);
  });

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Plano de Treinamento Sugerido:</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {sortedWeeks.map(([week, sessions]) => (
          <div key={week} className="mb-6 p-4 bg-white border border-gray-200 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-2">{week}</h3>
            {sessions.map((session, index) => (
              <TrainingSessionDisplay key={index} session={session} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

const TrainingPlanGenerator = () => {
  const [pace, setPace] = useState('');
  const [plan, setPlan] = useState({});
  const [weeks, setWeeks] = useState(6);
  const [baseDistance, setBaseDistance] = useState(10);
  const [submittedWeeks, setSubmittedWeeks] = useState(null);
  const [submittedBaseDistance, setSubmittedBaseDistance] = useState(null);
  const [time, setTime] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const timeValue = formData.get('time');
    const [minutes, seconds] = timeValue.split(':').map(Number);
    const numberOfWeeks = formData.get('weeks');
    const baseDistanceValue = formData.get('baseDistance');

    setSubmittedWeeks(numberOfWeeks);
    setSubmittedBaseDistance(baseDistanceValue);

    try {
      const response = await fetch('http://localhost:5001/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          minutes, 
          seconds, 
          num_weeks: numberOfWeeks,
          base_distance: baseDistanceValue
        }),
      });
      const data = await response.json();
      setPace(data.pace);
      setPlan(data.plan);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const handleTimeChange = (e) => {
    let value = e.target.value;
    
    // Remove qualquer caractere que não seja número ou dois-pontos
    value = value.replace(/[^\d:]/g, '');
    
    // Garante que haja apenas um dois-pontos
    const colonCount = (value.match(/:/g) || []).length;
    if (colonCount > 1) {
      value = value.replace(/:/g, (match, offset) => offset === value.indexOf(':') ? match : '');
    }
    
    // Formata para mm:ss
    if (value.length > 2 && !value.includes(':')) {
      value = value.slice(0, -2) + ':' + value.slice(-2);
    }
    
    // Limita os minutos e segundos a 59
    const [minutes, seconds] = value.split(':');
    if (minutes && parseInt(minutes) > 59) {
      value = '59' + (value.includes(':') ? value.slice(2) : '');
    }
    if (seconds && parseInt(seconds) > 59) {
      value = value.slice(0, -2) + '59';
    }
    
    setTime(value);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Gerador de Planilha de Treino</h1>
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="mb-4">
          <label htmlFor="time" className="block mb-2">Tempo (mm:ss):</label>
          <input 
            type="text" 
            id="time" 
            name="time" 
            required
            value={time}
            onChange={handleTimeChange}
            placeholder="05:00"
            pattern="^[0-5]?[0-9]:[0-5][0-9]$"
            className="w-full p-2 border border-gray-300 rounded" 
          />
        </div>
        <div className="mb-4">
          <label htmlFor="weeks" className="block mb-2">Número de Semanas:</label>
          <input type="number" id="weeks" name="weeks" required
                 min="1" max="52" value={weeks} onChange={(e) => setWeeks(parseInt(e.target.value))}
                 className="w-full p-2 border border-gray-300 rounded" />
        </div>
        <div className="mb-4">
          <label htmlFor="baseDistance" className="block mb-2">Distância Base (km):</label>
          <input type="number" id="baseDistance" name="baseDistance" required
                 min="1" step="0.1" value={baseDistance} onChange={(e) => setBaseDistance(parseFloat(e.target.value))}
                 className="w-full p-2 border border-gray-300 rounded" />
        </div>
        <button type="submit" 
                className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
          Gerar Plano de Treino
        </button>
      </form>
      
      {pace && submittedWeeks && submittedBaseDistance && (
        <div className="mb-6">
          <h2 className="text-2xl font-semibold mb-2">Informações do Plano:</h2>
          <p className="text-lg">Pace Médio: {pace}</p>
          <p className="text-lg">Número de Semanas: {submittedWeeks}</p>
          <p className="text-lg">Distância Base: {submittedBaseDistance} km</p>
        </div>
      )}
      
      {Object.keys(plan).length > 0 && <TrainingPlanDisplay plan={plan} />}
    </div>
  );
};

export default TrainingPlanGenerator;