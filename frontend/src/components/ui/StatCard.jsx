import React from 'react';
import ProgressBar from './ProgressBar';
import { Flame } from 'lucide-react';

export const StatCard = ({
  title,
  value,
  subtitle,
  type = 'default', // 'readiness' | 'streak' | 'strong' | 'focus'
  progress,
  icon: Icon,
  className = '',
  loading = false,
}) => {
  let cardTypeClass = 'stat-card-base';
  if (type === 'focus') cardTypeClass += ' stat-card-focus';
  if (type === 'strong') cardTypeClass += ' stat-card-strong';
  if (type === 'streak') cardTypeClass += ' stat-card-streak';

  if (loading) {
    return (
      <div className={`${cardTypeClass} ${className}`}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="skeleton-shimmer" style={{ width: '100px', height: '12px' }} />
          <span className="skeleton-shimmer" style={{ width: '16px', height: '16px', borderRadius: '50%' }} />
        </div>
        <div style={{ margin: '12px 0 6px 0' }}>
          <div className="skeleton-shimmer" style={{ width: '120px', height: '28px', borderRadius: '4px' }} />
        </div>
        <div className="skeleton-shimmer" style={{ width: '150px', height: '12px', marginTop: '6px' }} />
      </div>
    );
  }

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
          {type === 'streak' && <Flame size={22} style={{ color: '#f97316', flexShrink: 0 }} />}
          <div
            className="text-stats"
            style={{
              color: type === 'focus' ? '#ba1a1a' : type === 'strong' ? '#65597b' : 'var(--on-surface)',
              fontSize: type === 'strong' ? '20px' : '30px',
              fontWeight: 800,
              lineHeight: 1.2,
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
