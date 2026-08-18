import React from 'react';

export const ProgressBar = ({ progress = 0, color = '#426651' }) => {
  const safeProgress = Math.min(100, Math.max(0, progress));
  return (
    <div className="progress-track">
      <div
        className="progress-fill"
        style={{ width: `${safeProgress}%`, backgroundColor: color }}
        role="progressbar"
        aria-valuenow={safeProgress}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
};

export default ProgressBar;
