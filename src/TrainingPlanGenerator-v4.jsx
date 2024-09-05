import React, { useState } from 'react';

const ActivityDisplay = ({ activity }) => (
  <li className="mb-1">
    {activity.description}
    {activity.distance && ` - ${activity.distance}`}
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

const TrainingPlanDisplay = ({ plan }) => (
  <div>
    <h2 className="text-2xl font-semibold mb-4">Plano de Treinamento Sugerido:</h2>
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {Object.entries(plan).map(([week, sessions]) => (
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

const TrainingPlanGenerator = () => {
  const [plan, setPlan] = useState({});
  const [error, setError] = useState('');
  const [weeks, setWeeks] = useState(6);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    const formData = new FormData(event.target);
    const minutes = parseInt(formData.get('minutes'), 10);
    const seconds = parseInt(formData.get('seconds'), 10);
    const numberOfWeeks = parseInt(formData.get('weeks'), 10);

    // Validação básica
    if (isNaN(minutes) || isNaN(seconds) || isNaN(numberOfWeeks)) {
      setError('Por favor, preencha todos os campos com números válidos.');
      return;
    }

    if (seconds < 0 || seconds >= 60) {
      setError('Os segundos devem estar entre 0 e 59.');
      return;
    }

    // Calculate total seconds for 5k
    const time5k = minutes * 60 + seconds;

    // Get current date in DD/MM/YYYY format
    const today = new Date();
    const startDate = `${today.getDate().toString().padStart(2, '0')}/${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getFullYear()}`;

    try {
      const response = await fetch('http://localhost:8000/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ 
          time5k: time5k, 
          startDate: startDate, 
          numWeeks: numberOfWeeks 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'An error occurred while generating the training plan.');
      }

      const data = await response.json();
      setPlan(data);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError(error.message);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Gerador de Planilha de Treino</h1>
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="mb-4">
          <label htmlFor="minutes" className="block mb-2">Minutos:</label>
          <input type="number" id="minutes" name="minutes" required
                 className="w-full p-2 border border-gray-300 rounded" />
        </div>
        <div className="mb-4">
          <label htmlFor="seconds" className="block mb-2">Segundos:</label>
          <input type="number" id="seconds" name="seconds" required
                 className="w-full p-2 border border-gray-300 rounded" />
        </div>
        <div className="mb-4">
          <label htmlFor="weeks" className="block mb-2">Número de Semanas:</label>
          <input type="number" id="weeks" name="weeks" required
                 min="1" max="52" value={weeks} onChange={(e) => setWeeks(e.target.value)}
                 className="w-full p-2 border border-gray-300 rounded" />
        </div>
        <button type="submit" 
                className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
          Gerar Plano de Treino
        </button>
      </form>
      
      {error && (
        <div className="mb-6 text-red-500">
          <p>{error}</p>
        </div>
      )}
      
      {Object.keys(plan).length > 0 && <TrainingPlanDisplay plan={plan} />}
    </div>
  );
};

export default TrainingPlanGenerator;