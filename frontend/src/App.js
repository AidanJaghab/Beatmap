import React, { useEffect, useState } from "react";

function App() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    fetch("http://localhost:3001/api/events")
      .then((res) => res.json())
      .then((data) => setEvents(data.data))
      .catch((err) => console.error("Failed to fetch events:", err));
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>🎶 NYC EDM Events Today</h1>
      {events.length === 0 ? (
        <p>No events found. Check back later.</p>
      ) : (
        <ul>
          {events.map((event, idx) => (
            <li key={idx} style={{ marginBottom: "1rem" }}>
              <strong>{event.artist}</strong> at {event.venue} — {event.date}
              <br />
              <small>Time: {event.time} | Age: {event.age}</small>
              {event.event_name && (
                <>
                  <br />
                  <em>{event.event_name}</em>
                </>
              )}
              {event.url && (
                <>
                  <br />
                  <a href={event.url} target="_blank" rel="noreferrer">
                    Event Link
                  </a>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;