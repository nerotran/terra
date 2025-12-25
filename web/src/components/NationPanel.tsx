import { useEffect, useState } from 'react';
import type { Nation, NationDetails } from '../types';
import { yearToDisplay } from '../types';

interface NationPanelProps {
  nation: Nation | null;
  snapshotId: number;
  year: number;  // Signed: negative for BC, positive for AD
  isOpen: boolean;
  onClose: () => void;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export function NationPanel({ nation, snapshotId, year, isOpen, onClose }: NationPanelProps) {
  const [details, setDetails] = useState<NationDetails | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!nation || !isOpen) {
      setDetails(null);
      return;
    }

    const fetchDetails = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/nations/${nation.id}/snapshot/${snapshotId}`);
        if (res.ok) {
          setDetails(await res.json());
        }
      } catch (err) {
        console.error('Failed to fetch nation details:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [nation?.id, snapshotId, isOpen]);

  if (!nation) return null;

  return (
    <div style={{
      ...styles.overlay,
      opacity: isOpen ? 1 : 0,
      pointerEvents: isOpen ? 'auto' : 'none',
    }}>
      <div style={{
        ...styles.panel,
        transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
      }}>
        {/* Header */}
        <div style={styles.header}>
          <button style={styles.closeButton} onClick={onClose}>
            &times;
          </button>
          <div style={styles.headerContent}>
            <h2 style={styles.nationName}>
              {nation.wiki_url ? (
                <a href={nation.wiki_url} target="_blank" rel="noopener noreferrer" style={styles.link}>
                  {nation.display_name || nation.name}
                </a>
              ) : (
                nation.display_name || nation.name
              )}
            </h2>
            <span style={styles.yearBadge}>{yearToDisplay(year)}</span>
          </div>
        </div>

        {/* Ruler Section */}
        {details?.ruler && (
          <div style={styles.section}>
            <div style={styles.rulerContainer}>
              {details.ruler.portrait_url ? (
                <img
                  src={`${API_BASE.replace('/api', '')}${details.ruler.portrait_url}`}
                  alt={details.ruler.name}
                  style={styles.portrait}
                />
              ) : (
                <div style={styles.portraitPlaceholder}>
                  <span style={styles.portraitIcon}>👤</span>
                </div>
              )}
              <div style={styles.rulerInfo}>
                {details.ruler.title && (
                  <span style={styles.rulerTitle}>{details.ruler.title}</span>
                )}
                <span style={styles.rulerName}>
                  {details.ruler.wiki_url ? (
                    <a href={details.ruler.wiki_url} target="_blank" rel="noopener noreferrer" style={styles.link}>
                      {details.ruler.name}
                    </a>
                  ) : (
                    details.ruler.name
                  )}
                </span>
                <span style={styles.reignDates}>
                  Reign: {yearToDisplay(details.ruler.reign_start)} - {details.ruler.reign_end !== null ? yearToDisplay(details.ruler.reign_end) : 'present'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Info Grid */}
        <div style={styles.section}>
          {loading ? (
            <span style={styles.loadingText}>Loading details...</span>
          ) : details ? (
            <div style={styles.infoGrid}>
              {details.founded_year !== null && (
                <div style={styles.infoItem}>
                  <span style={styles.infoLabel}>Founded</span>
                  <span style={styles.infoValue}>{yearToDisplay(details.founded_year)}</span>
                </div>
              )}
              {details.capital && (
                <div style={styles.infoItem}>
                  <span style={styles.infoLabel}>Capital</span>
                  <span style={styles.infoValue}>{details.capital}</span>
                </div>
              )}
              {details.language && (
                <div style={styles.infoItem}>
                  <span style={styles.infoLabel}>Language</span>
                  <span style={styles.infoValue}>{details.language}</span>
                </div>
              )}
              {details.religion && (
                <div style={styles.infoItem}>
                  <span style={styles.infoLabel}>Religion</span>
                  <span style={styles.infoValue}>{details.religion}</span>
                </div>
              )}
              {details.population && (
                <div style={styles.infoItem}>
                  <span style={styles.infoLabel}>Population</span>
                  <span style={styles.infoValue}>{details.population}</span>
                </div>
              )}
            </div>
          ) : (
            <span style={styles.loadingText}>Could not load details</span>
          )}
        </div>

        {/* Description */}
        {details?.description && (
          <div style={styles.section}>
            <div style={styles.descriptionContainer}>
              <p style={styles.description}>{details.description}</p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={styles.footer}>
          <span style={styles.footerIcon}>ℹ</span>
          <span style={styles.footerText}>Data updates with time slider</span>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    right: 0,
    bottom: 0,
    width: '360px',
    zIndex: 1000,
    transition: 'opacity 0.3s ease-in-out',
  },
  panel: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    width: '100%',
    background: '#1a1a2e',
    color: '#e8e8e8',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.3)',
    transition: 'transform 0.3s ease-in-out',
  },
  header: {
    padding: '16px',
    borderBottom: '1px solid #2d2d44',
    position: 'relative',
  },
  closeButton: {
    position: 'absolute',
    top: '12px',
    left: '12px',
    background: 'none',
    border: 'none',
    color: '#888',
    fontSize: '24px',
    cursor: 'pointer',
    padding: '4px 8px',
    lineHeight: 1,
  },
  headerContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginLeft: '32px',
  },
  nationName: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 600,
  },
  yearBadge: {
    background: '#2d2d44',
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '14px',
    color: '#aaa',
  },
  section: {
    padding: '16px',
    borderBottom: '1px solid #2d2d44',
  },
  rulerContainer: {
    display: 'flex',
    gap: '16px',
    alignItems: 'center',
  },
  portraitPlaceholder: {
    width: '72px',
    height: '72px',
    borderRadius: '50%',
    background: '#2d2d44',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  portrait: {
    width: '72px',
    height: '72px',
    borderRadius: '50%',
    objectFit: 'cover',
    flexShrink: 0,
  },
  portraitIcon: {
    fontSize: '32px',
    opacity: 0.5,
  },
  rulerInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  rulerTitle: {
    fontSize: '12px',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  rulerName: {
    fontSize: '18px',
    fontWeight: 500,
  },
  reignDates: {
    fontSize: '13px',
    color: '#888',
  },
  infoGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
  },
  infoItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  infoLabel: {
    fontSize: '11px',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  infoValue: {
    fontSize: '14px',
  },
  descriptionContainer: {
    maxHeight: '150px',
    overflowY: 'auto',
  },
  description: {
    margin: 0,
    fontSize: '14px',
    lineHeight: 1.6,
    color: '#ccc',
  },
  footer: {
    marginTop: 'auto',
    padding: '12px 16px',
    borderTop: '1px solid #2d2d44',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: '#666',
    fontSize: '12px',
  },
  footerIcon: {
    fontSize: '14px',
  },
  footerText: {
    fontStyle: 'italic',
  },
  link: {
    color: '#6db3f2',
    textDecoration: 'none',
  },
  loadingText: {
    color: '#888',
    fontStyle: 'italic',
  },
};
