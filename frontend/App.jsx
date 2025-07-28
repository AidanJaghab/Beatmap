import React, { useState, useEffect } from 'react';

function App() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/events');
      const data = await response.json();
      setEvents(data.data || []);
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading events...</div>;
  }

  return (
    <div className="App">
      <header>
        <h1>EDM Events NYC</h1>
        <p>Today's electronic music events in New York City</p>
      </header>
      
      <main>
        {events.length === 0 ? (
          <p>No events found for today.</p>
        ) : (
          <div className="events-list">
            {events.map((event, index) => (
              <div key={index} className="event-card">
                <h3>{event.event_name || 'EDM Event'}</h3>
                <p><strong>Artist:</strong> {event.artist}</p>
                <p><strong>Venue:</strong> {event.venue}</p>
                <p><strong>Date:</strong> {event.date}</p>
                <p><strong>Time:</strong> {event.time}</p>
                <p><strong>Age:</strong> {event.age}</p>
                <p><strong>Location:</strong> {event.location}</p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

11