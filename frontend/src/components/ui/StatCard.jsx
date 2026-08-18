import React from 'react';
import ProgressBar from './ProgressBar';

export const StatCard = ({
  title,
  value,
  subtitle,
  type = 'default', // 'readiness' | 'streak' | 'strong' | 'focus'
  progress,
  icon: Icon,
  className = '',
}) => {
  let cardTypeClass = 'stat-card-base';
  if (type === 'focus') cardTypeClass += ' stat-card-focus';
  if (type === 'strong') cardTypeClass += ' stat-card-strong';
  if (type === 'streak') cardTypeClass += ' stat-card-streak';

  return (
    <div className={`${cardTypeClass} ${className}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="text-label-xs" style={{ color: type === 'focus' ? '#ba1a1a' : 'var(--on-surface-variant)' }}>
          {title}
        </span>
        {Icon && <Icon size={16} color={type === 'focus' ? '#ba1a1a' : 'var(--primary)'} />}
      </div>

      <div style={{ margin: '8px 0 4px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {type === 'streak' && <span style={{ fontSize: '24px' }}>🔥</span>}
          <div
            className="text-stats"
            style={{
              color: type === 'focus' ? '#ba1a1a' : type === 'strong' ? '#65597b' : 'var(--on-surface)',
              fontSize: type === 'strong' ? '22px' : '30px',
              fontWeight: 800,
            }}
          >
            {value}
          </div>
          {type === 'readiness' && (
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#426651', display: 'inline-block' }} />
          )}
        </div>

        {progress !== undefined && <ProgressBar progress={progress} />}
      </div>

      <div
        className="text-body-sm"
        style={{
          fontSize: '12px',
          color: type === 'focus' ? '#7f3030' : 'var(--on-surface-variant)',
          marginTop: '6px',
        }}
      >
        {subtitle}
      </div>
    </div>
  );
};

export default StatCard;
