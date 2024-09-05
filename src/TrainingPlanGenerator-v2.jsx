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
  const [pace, setPace] = useState('');
  const [plan, setPlan] = useState({});

  const handleSubmit = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const minutes = formData.get('minutes');
    const seconds = formData.get('seconds');

    try {
      const response = await fetch('http://localhost:5001/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ minutes, seconds }),
      });
      const data = await response.json();
      setPace(data.pace);
      setPlan(data.plan);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  
    // Utility function to enforce mm:ss format
    const handleTimeInput = (event) => {
        let value = event.target.value.replace(/[^0-9:]/g, '');
        const parts = value.split(':');
        if (parts[0].length > 2) parts[0] = parts[0].substring(0, 2);
        if (parts[1] && parts[1].length > 2) parts[1] = parts[1].substring(0, 2);
        event.target.value = parts.join(':');
        setTime(event.target.value);
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
        <button type="submit" 
                className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
          Gerar Plano de Treino
        </button>
      </form>
      
      {pace && (
        <div className="mb-6">
          <h2 className="text-2xl font-semibold mb-2">Pace Médio:</h2>
          <p className="text-lg">{pace}</p>
        </div>
      )}
      
      {Object.keys(plan).length > 0 && <TrainingPlanDisplay plan={plan} />}
    </div>
  );
};

export default TrainingPlanGenerator;