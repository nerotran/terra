import { useState, useEffect } from 'react';
import { Map } from './components/Map';
import { TimeSlider } from './components/TimeSlider';
import { getAllTerritories } from './api/client';
import type { Territory } from './types';

function App() {
  const [territories, setTerritories] = useState<Territory[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAllTerritories()
      .then((data) => {
        setTerritories(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={styles.loading}>Loading...</div>;
  }

  if (error) {
    return <div style={styles.error}>Error: {error}</div>;
  }

  const currentTerritory = territories[currentIndex] || null;

  return (
    <div style={styles.container}>
      <div style={styles.map}>
        <Map territory={currentTerritory} />
      </div>
      <TimeSlider
        snapshots={territories}
        currentIndex={currentIndex}
        onChange={setCurrentIndex}
      />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#0f0f23',
  },
  map: {
    flex: 1,
    overflow: 'hidden',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    color: '#fff',
    background: '#0f0f23',
  },
  error: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    color: '#ff6b6b',
    background: '#0f0f23',
  },
};

export default App;
