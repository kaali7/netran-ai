import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Bell, Settings, User, Layers, History, Target, LogOut, ChevronDown, Sparkles, LayoutDashboard, BarChart2 } from 'lucide-react';
import useAuth from '../../hooks/useAuth';

export const Navbar = ({ userName }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Determine display name from prop, user email, or fallback
  const displayName =
    userName ||
    (user?.email ? user.email.split('@')[0] : 'Soni');

  const userEmail = user?.email || 'soni.candidate@netran.ai';

  const handleLogout = () => {
    setIsMenuOpen(false);
    logout();
    navigate('/login', { replace: true });
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <header
      style={{
        width: '100%',
        padding: '16px 0',
        marginBottom: '24px',
        borderBottom: '1px solid rgba(101, 89, 123, 0.08)',
        position: 'relative',
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: '100%',
          margin: '0 auto',
          padding: '0 36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand Logo & Title */}
        <div
          onClick={() => navigate('/dashboard')}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
        >
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #65597b 0%, #426651 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 3px 10px rgba(101, 89, 123, 0.25)',
            }}
          >
            <span style={{ color: '#ffffff', fontWeight: 800, fontSize: '17px' }}>N</span>
          </div>
          <span style={{ fontSize: '19px', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--on-surface)' }}>
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
          {/* Dashboard */}
          <a
            href="/dashboard"
            onClick={(e) => {
              e.preventDefault();
              navigate('/dashboard');
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px',
              fontWeight: location.pathname === '/dashboard' ? 700 : 600,
              color: location.pathname === '/dashboard' ? 'var(--primary)' : 'var(--on-surface-variant)',
              transition: 'all 150ms ease',
              textDecoration: 'none',
              paddingBottom: '4px',
              borderBottom: location.pathname === '/dashboard' ? '2px solid #65597b' : '2px solid transparent',
            }}
          >
            <LayoutDashboard size={16} />
            <span>Dashboard</span>
          </a>

          {/* Analytics */}
          <a
            href="/analytics"
            onClick={(e) => {
              e.preventDefault();
              navigate('/analytics');
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px',
              fontWeight: location.pathname === '/analytics' ? 700 : 600,
              color: location.pathname === '/analytics' ? '#65597b' : 'var(--on-surface-variant)',
              transition: 'all 150ms ease',
              textDecoration: 'none',
              paddingBottom: '4px',
              borderBottom: location.pathname === '/analytics' ? '2px solid #65597b' : '2px solid transparent',
            }}
          >
            <BarChart2 size={16} />
            <span>Analytics</span>
          </a>

          {/* History */}
          <a
            href="/history"
            onClick={(e) => {
              e.preventDefault();
              navigate('/history');
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px',
              fontWeight: location.pathname === '/history' ? 700 : 600,
              color: location.pathname === '/history' ? '#65597b' : 'var(--on-surface-variant)',
              transition: 'all 150ms ease',
              textDecoration: 'none',
              paddingBottom: '4px',
              borderBottom: location.pathname === '/history' ? '2px solid #65597b' : '2px solid transparent',
            }}
          >
            <History size={16} />
            <span>History</span>
          </a>
        </nav>

        {/* Right User Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {/* Notification Bell */}
          <button
            aria-label="Notifications"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              border: 'none',
              background: 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--on-surface-variant)',
              cursor: 'pointer',
              transition: 'background 150ms ease',
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = '#edeef0')}
            onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <Bell size={18} />
          </button>

          {/* User Profile Pill & Dropdown Container */}
          <div ref={menuRef} style={{ position: 'relative' }}>
            <button
              onClick={() => setIsMenuOpen((prev) => !prev)}
              aria-label="User Menu"
              aria-expanded={isMenuOpen}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: isMenuOpen ? '#e6d6ff' : '#f0f1f3',
                padding: '6px 12px 6px 8px',
                borderRadius: 'var(--radius-full)',
                border: isMenuOpen ? '1px solid #c3a5fc' : '1px solid #e1e3e4',
                cursor: 'pointer',
                transition: 'all 150ms ease',
                boxShadow: isMenuOpen ? '0 2px 10px rgba(101, 89, 123, 0.15)' : 'none',
              }}
              onMouseOver={(e) => {
                if (!isMenuOpen) {
                  e.currentTarget.style.background = '#e9eaed';
                  e.currentTarget.style.borderColor = '#d5d7dc';
                }
              }}
              onMouseOut={(e) => {
                if (!isMenuOpen) {
                  e.currentTarget.style.background = '#f0f1f3';
                  e.currentTarget.style.borderColor = '#e1e3e4';
                }
              }}
            >
              {/* Avatar circle */}
              <div
                style={{
                  width: '26px',
                  height: '26px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #65597b 0%, #4d4162 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#ffffff',
                }}
              >
                <User size={14} />
              </div>

              {/* Display Name */}
              <span
                style={{
                  fontSize: '14px',
                  fontWeight: 700,
                  color: 'var(--on-surface)',
                  textTransform: 'capitalize',
                }}
              >
                {displayName}
              </span>

              {/* Chevron icon indicator */}
              <ChevronDown
                size={15}
                style={{
                  color: 'var(--on-surface-variant)',
                  transform: isMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 200ms ease',
                }}
              />
            </button>

            {/* Profile Dropdown Sub-Menu */}
            {isMenuOpen && (
              <div
                className="animate-entrance"
                style={{
                  position: 'absolute',
                  top: 'calc(100% + 10px)',
                  right: 0,
                  width: '240px',
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  borderRadius: '16px',
                  border: '1px solid rgba(255, 255, 255, 0.9)',
                  boxShadow: '0 12px 36px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(101, 89, 123, 0.06)',
                  padding: '8px',
                  zIndex: 100,
                }}
              >
                {/* User Header Section */}
                <div style={{ padding: '10px 12px 8px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                    <div
                      style={{
                        width: '34px',
                        height: '34px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #65597b 0%, #426651 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#ffffff',
                        fontWeight: 700,
                        fontSize: '14px',
                      }}
                    >
                      {displayName.charAt(0).toUpperCase()}
                    </div>
                    <div style={{ overflow: 'hidden' }}>
                      <p
                        style={{
                          margin: 0,
                          fontSize: '14px',
                          fontWeight: 700,
                          color: 'var(--on-surface)',
                          textTransform: 'capitalize',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {displayName}
                      </p>
                      <p
                        style={{
                          margin: 0,
                          fontSize: '11px',
                          color: 'var(--outline)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {userEmail}
                      </p>
                    </div>
                  </div>
                  <div
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      background: '#e6d6ff',
                      color: '#4d4162',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '10px',
                      fontWeight: 700,
                      marginTop: '4px',
                    }}
                  >
                    <Sparkles size={10} />
                    <span>Candidate Track</span>
                  </div>
                </div>

                <div style={{ height: '1px', background: '#f0f1f3', margin: '6px 0' }} />

                {/* Sub-Menu Action 1: Settings */}
                <button
                  onClick={() => {
                    setIsMenuOpen(false);
                    alert('Opening Account & Platform Settings...');
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 12px',
                    borderRadius: '10px',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--on-surface)',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'background 150ms ease',
                    textAlign: 'left',
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.background = '#f4f5f7')}
                  onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <Settings size={16} style={{ color: 'var(--primary)' }} />
                  <span>Account Settings</span>
                </button>

                {/* Sub-Menu Action 2: Past Mocks & Analytics */}
                <button
                  onClick={() => {
                    setIsMenuOpen(false);
                    navigate('/dashboard#mocks');
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 12px',
                    borderRadius: '10px',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--on-surface)',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'background 150ms ease',
                    textAlign: 'left',
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.background = '#f4f5f7')}
                  onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <History size={16} style={{ color: 'var(--secondary)' }} />
                  <span>My Mocks & Telemetry</span>
                </button>

                <div style={{ height: '1px', background: '#f0f1f3', margin: '6px 0' }} />

                {/* Sub-Menu Action 3: Sign Out */}
                <button
                  onClick={handleLogout}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 12px',
                    borderRadius: '10px',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: '#ba1a1a',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'background 150ms ease',
                    textAlign: 'left',
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.background = '#ffdad6')}
                  onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <LogOut size={16} style={{ color: '#ba1a1a' }} />
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
