import type { TimeSnapshot } from '../types';

interface TimeSliderProps {
  snapshots: TimeSnapshot[];
  currentIndex: number;
  onChange: (index: number) => void;
}

export function TimeSlider({ snapshots, currentIndex, onChange }: TimeSliderProps) {
  if (snapshots.length === 0) {
    return (
      <div style={{ padding: '1rem', background: '#16213e', color: '#fff', textAlign: 'center' }}>
        No data available
      </div>
    );
  }

  const current = snapshots[currentIndex];

  const formatYear = (year: number, era: 'BC' | 'AD') => {
    return era === 'BC' ? `${year} BC` : `${year} AD`;
  };

  return (
    <div style={{ padding: '1rem', background: '#16213e', color: '#fff' }}>
      <input
        type="range"
        min={0}
        max={snapshots.length - 1}
        value={currentIndex}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: '100%' }}
      />
      {current && (
        <div style={{ textAlign: 'center', marginTop: '0.5rem' }}>
          <strong>{formatYear(current.year, current.era)}</strong>
          <div style={{ fontSize: '0.875rem', opacity: 0.8 }}>{current.label}</div>
        </div>
      )}
    </div>
  );
}
