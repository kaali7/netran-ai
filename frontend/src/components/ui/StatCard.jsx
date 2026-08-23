import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import ProgressBar from './ProgressBar';
import { Flame, TrendingUp, Award, Target, Sparkles, CheckCircle2, X } from 'lucide-react';

export const StatCard = ({
  title,
  value,
  subtitle,
  fullDetail,
  type = 'default', // 'readiness' | 'streak' | 'strong' | 'focus'
  progress,
  icon: Icon,
  className = '',
  loading = false,
}) => {
  const [showDetailModal, setShowDetailModal] = useState(false);

  let cardTypeClass = 'stat-card-base';
  let badgeBg = 'rgba(101, 89, 123, 0.08)';
  let iconColor = '#65597b';
  let titleColor = '#6b7280';
  let valueColor = '#111827';
  let subtitleColor = '#6b7280';

  if (type === 'focus') {
    cardTypeClass += ' stat-card-focus';
    badgeBg = 'rgba(186, 26, 26, 0.08)';
    iconColor = '#ba1a1a';
    titleColor = '#ba1a1a';
    valueColor = '#991b1b';
    subtitleColor = '#7f3030';
  } else if (type === 'strong') {
    cardTypeClass += ' stat-card-strong';
    badgeBg = 'rgba(101, 89, 123, 0.1)';
    iconColor = '#65597b';
    titleColor = '#65597b';
    valueColor = '#4c3f63';
    subtitleColor = '#574c6e';
  } else if (type === 'streak') {
    cardTypeClass += ' stat-card-streak';
    badgeBg = 'rgba(249, 115, 22, 0.1)';
    iconColor = '#f97316';
    titleColor = '#6b7280';
    valueColor = '#111827';
    subtitleColor = '#6b7280';
  } else if (type === 'readiness') {
    cardTypeClass += ' stat-card-readiness';
    badgeBg = 'rgba(16, 185, 129, 0.1)';
    iconColor = '#059669';
    titleColor = '#6b7280';
    valueColor = '#111827';
    subtitleColor = '#6b7280';
  }

  const detailedText = fullDetail || subtitle;
  const isExpandable =
    (type === 'strong' || type === 'focus') &&
    detailedText &&
    detailedText.length > 45;

  let displaySubtitle = subtitle;
  if (isExpandable && subtitle) {
    displaySubtitle = subtitle.replace(/\.{2,}$/, '').trim();
    if (displaySubtitle.length > 60) {
      displaySubtitle = displaySubtitle.slice(0, 58).trim();
    }
  }

  if (loading) {
    return (
      <div className={`${cardTypeClass} ${className}`}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="skeleton-shimmer" style={{ width: '90px', height: '12px' }} />
          <span className="skeleton-shimmer" style={{ width: '28px', height: '28px', borderRadius: '8px' }} />
        </div>
        <div style={{ margin: '14px 0 8px 0' }}>
          <div className="skeleton-shimmer" style={{ width: '110px', height: '26px', borderRadius: '4px' }} />
        </div>
        <div className="skeleton-shimmer" style={{ width: '140px', height: '12px', marginTop: 'auto' }} />
      </div>
    );
  }

  return (
    <>
      <div className={`${cardTypeClass} ${className}`}>
        {/* Header: Title + Icon Badge */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span
            className="stat-card-title-text"
            style={{
              color: titleColor,
              fontWeight: 800,
              fontSize: '11px',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            {title}
          </span>
          {Icon && (
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '8px',
                background: badgeBg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <Icon size={15} color={iconColor} />
            </div>
          )}
        </div>

        {/* Main Metric / Value */}
        <div style={{ margin: '10px 0 6px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {type === 'streak' && (
              <Flame size={20} style={{ color: '#f97316', flexShrink: 0 }} />
            )}
            <div
              className="stat-card-value-text"
              style={{
                color: valueColor,
                fontWeight: 800,
                fontSize: type === 'strong' || type === 'focus' ? '15.5px' : '26px',
                lineHeight: 1.25,
                wordBreak: 'break-word',
                display: '-webkit-box',
                WebkitLineClamp: type === 'strong' || type === 'focus' ? 2 : 1,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
              title={typeof value === 'string' ? value : undefined}
            >
              {value}
            </div>
            {type === 'readiness' && (
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: progress >= 70 ? '#10b981' : progress >= 40 ? '#f59e0b' : '#ef4444',
                  display: 'inline-block',
                  flexShrink: 0,
                }}
              />
            )}
          </div>

          {progress !== undefined && (
            <div style={{ marginTop: '8px' }}>
              <ProgressBar
                progress={progress}
                color={progress >= 70 ? '#10b981' : progress >= 40 ? '#f59e0b' : '#ef4444'}
              />
            </div>
          )}
        </div>

        {/* Subtitle / Telemetry Detail with inline more... button */}
        <div
          className="stat-card-subtitle-text"
          style={{
            color: subtitleColor,
            fontSize: '12px',
            fontWeight: 500,
            lineHeight: 1.35,
            marginTop: 'auto',
            paddingTop: '6px',
            wordBreak: 'break-word',
          }}
        >
          <span>
            {displaySubtitle}
            {isExpandable && (
              <>
                {' '}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowDetailModal(true);
                  }}
                  title="View complete feedback narrative"
                  style={{
                    display: 'inline',
                    background: 'transparent',
                    border: 'none',
                    color: type === 'focus' ? '#ba1a1a' : '#65597b',
                    fontWeight: 800,
                    fontSize: '11.5px',
                    cursor: 'pointer',
                    padding: 0,
                    margin: 0,
                    textDecoration: 'underline',
                    verticalAlign: 'baseline',
                  }}
                >
                  more...
                </button>
              </>
            )}
          </span>
        </div>
      </div>

      {/* Centered Portal Popup Modal (Desktop + Mobile Responsive) */}
      {showDetailModal && typeof document !== 'undefined' && createPortal(
        <div
          onClick={(e) => {
            e.stopPropagation();
            setShowDetailModal(false);
          }}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            width: '100vw',
            height: '100vh',
            background: 'rgba(15, 12, 24, 0.45)',
            backdropFilter: 'blur(5px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 99999,
            padding: '16px',
            boxSizing: 'border-box',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '420px',
              background: '#ffffff',
              borderRadius: '22px',
              padding: '22px 24px',
              boxShadow: '0 25px 60px rgba(0, 0, 0, 0.22), 0 4px 16px rgba(0, 0, 0, 0.08)',
              border: `1px solid ${type === 'focus' ? '#fee2e2' : '#ede6f8'}`,
              boxSizing: 'border-box',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '10px',
                    background: badgeBg,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  {Icon && <Icon size={16} color={iconColor} />}
                </div>
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: titleColor, letterSpacing: '0.04em', display: 'block' }}>
                    {title}
                  </span>
                  <h4 style={{ fontSize: '15.5px', fontWeight: 800, color: valueColor, margin: 0 }}>
                    {value}
                  </h4>
                </div>
              </div>
              <button
                onClick={() => setShowDetailModal(false)}
                title="Close"
                style={{
                  background: '#f3f4f6',
                  border: 'none',
                  borderRadius: '50%',
                  width: '28px',
                  height: '28px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#6b7280',
                  cursor: 'pointer',
                  flexShrink: 0,
                }}
              >
                <X size={15} />
              </button>
            </div>

            {/* Diagnostic Feedback Narrative Box */}
            <div
              style={{
                background: type === 'focus' ? '#fff8f8' : '#fbf9fe',
                borderRadius: '14px',
                padding: '14px 16px',
                border: `1px solid ${type === 'focus' ? '#fecaca' : '#ede6f8'}`,
                fontSize: '13px',
                lineHeight: '1.55',
                color: '#374151',
                margin: '8px 0 18px 0',
                maxHeight: '45vh',
                overflowY: 'auto',
                wordBreak: 'break-word',
              }}
            >
              {detailedText}
            </div>

            {/* Action Footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowDetailModal(false)}
                style={{
                  background: type === 'focus' ? '#ba1a1a' : '#65597b',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '9999px',
                  padding: '9px 24px',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: `0 4px 12px ${type === 'focus' ? 'rgba(186, 26, 26, 0.25)' : 'rgba(101, 89, 123, 0.25)'}`,
                }}
              >
                Got it
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
};

export default StatCard;
