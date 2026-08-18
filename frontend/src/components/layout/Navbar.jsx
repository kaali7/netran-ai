import React from 'react';
import { Bell, Settings, User, Layers, History, Target } from 'lucide-react';

export const Navbar = ({ userName = 'Arjun Sharma' }) => {
  return (
    <header
      style={{
        width: '100%',
        padding: '16px 0',
        marginBottom: '24px',
        borderBottom: '1px solid rgba(101, 89, 123, 0.08)',
      }}
    >
      <div
        style={{
          maxWidth: 'var(--container-max)',
          margin: '0 auto',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand Logo & Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #65597b 0%, #426651 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(101, 89, 123, 0.25)',
            }}
          >
            <span style={{ color: '#ffffff', fontWeight: 800, fontSize: '16px' }}>N</span>
          </div>
          <span style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--on-surface)' }}>
            Netran AI
          </span>
        </div>

        {/* Center Nav Links */}
        <nav
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '32px',
          }}
          className="desktop-nav"
        >
          <a
            href="#tracks"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px',
              fontWeight: 600,
              color: 'var(--on-surface-variant)',
              transition: 'color 150ms ease',
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = 'var(--primary)')}
            onMouseOut={(e) => (e.currentTarget.style.color = 'var(--on-surface-variant)')}
          >
            <Layers size={16} />
            <span>Practice Tracks</span>
          </a>

          <a
            href="#mocks"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px',
              fontWeight: 600,
              color: 'var(--on-surface-variant)',
              transition: 'color 150ms ease',
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = 'var(--primary)')}
            onMouseOut={(e) => (e.currentTarget.style.color = 'var(--on-surface-variant)')}
          >
            <History size={16} />
            <span>Past Mocks</span>
          </a>

          <a
            href="#weak-areas"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px',
              fontWeight: 600,
              color: 'var(--on-surface-variant)',
              transition: 'color 150ms ease',
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = 'var(--primary)')}
            onMouseOut={(e) => (e.currentTarget.style.color = 'var(--on-surface-variant)')}
          >
            <Target size={16} />
            <span>Weak Areas</span>
          </a>
        </nav>

        {/* Right User Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* User Profile Pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: '#f0f1f3',
              padding: '6px 14px 6px 10px',
              borderRadius: 'var(--radius-full)',
              border: '1px solid #e1e3e4',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: '#65597b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
              }}
            >
              <User size={14} />
            </div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--on-surface)' }}>
              {userName}
            </span>
          </div>

          {/* Notification Bell */}
          <button
            aria-label="Notifications"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--on-surface-variant)',
              transition: 'background 150ms ease',
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = '#edeef0')}
            onMouseOut={(e) => (e.currentTarget.style.background = 'none')}
          >
            <Bell size={18} />
          </button>

          {/* Settings Icon */}
          <button
            aria-label="Settings"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--on-surface-variant)',
              transition: 'background 150ms ease',
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = '#edeef0')}
            onMouseOut={(e) => (e.currentTarget.style.background = 'none')}
          >
            <Settings size={18} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
