import React, { useState, useEffect } from 'react';
import './DemoBanner.css';

const DemoBanner = ({ isDemo }) => {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const isDismissed = localStorage.getItem('demoBannerDismissed');
    if (isDismissed === 'true') {
      setDismissed(true);
    }
  }, []);

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem('demoBannerDismissed', 'true');
  };

  if (dismissed) return null;

  return (
    <div className="demo-banner">
      <div className="demo-banner-content">
        <span className="demo-banner-icon">⚠️</span>
        <span className="demo-banner-text">
          {isDemo
            ? 'Demo environment – data is synthetic; no live sensors are connected.'
            : 'Development environment – using demo data generator.'}
        </span>
        <button className="demo-banner-dismiss" onClick={handleDismiss} aria-label="Dismiss">
          ✕
        </button>
      </div>
    </div>
  );
};

export default DemoBanner;
