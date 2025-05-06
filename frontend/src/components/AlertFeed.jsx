import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';

const AlertFeed = () => {
  const [alerts, setAlerts] = useState([]);
  
  useEffect(() => {
    const socket = io('http://localhost:8000');
    socket.on('alert', (data) => {
      setAlerts(a => [...a, data]);
    });
  }, []);

  return (
    <div>
      {alerts.map((alert, i) => <div key={i}>Alerte à {alert.time}</div>)}
    </div>
  );
};