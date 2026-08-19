import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Bell, Settings, User, Layers, History, Target, LogOut, ChevronDown, Sparkles, LayoutDashboard, BarChart2, CheckCircle2, Clock, Check, Menu, X } from 'lucide-react';
import useAuth from '../../hooks/useAuth';

export const Navbar = ({ userName }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const menuRef = useRef(null);
  const notifRef = useRef(null);


  const [notifications, setNotifications] = useState([
    {
      id: 1,
      title: 'Multimodal Evaluation Report Ready',
      message: 'Your latest mock interview evaluation and audio telemetry report is ready.',
      time: '10m ago',
      read: false,
      type: 'report',
    },
    {
      id: 2,
      title: 'Practice Track Initialized',
      message: 'Eva Stage 2 Question Tree generated for your Senior Fullstack track.',
      time: '1h ago',
      read: false,
      type: 'setup',
    },
    {
      id: 3,
      title: 'Welcome to Netran AI',
      message: 'Your candidate profile is active. Launch a practice mock to start.',
      time: '1d ago',
      read: true,
      type: 'welcome',
    },
  ]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleMarkAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  // Determine display name from prop, user email, or fallback
  const displayName =
    userName ||
    (user?.email ? user.email.split('@')[0] : 'Candidate');

  const userEmail = user?.email || 'candidate@netran.ai';

  const handleLogout = () => {
    setIsMenuOpen(false);
    logout();
    navigate('/login', { replace: true });
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setIsNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <>
      <header
        style={{
          width: '100%',
          padding: '16px 0',
          marginBottom: '24px',
          borderBottom: '1px solid rgba(101, 89, 123, 0.08)',
          position: 'relative',
          zIndex: 1000,
        }}
      >

        <div
          className="navbar-inner-container"
          style={{
            maxWidth: '100%',
            margin: '0 auto',
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
          <nav className="desktop-nav">
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
            {/* Notification Bell Dropdown Container */}
            <div ref={notifRef} style={{ position: 'relative' }}>
              <button
                onClick={() => setIsNotifOpen((prev) => !prev)}
                aria-label="Notifications"
                aria-expanded={isNotifOpen}
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '50%',
                  border: 'none',
                  background: isNotifOpen ? '#edeef0' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--on-surface-variant)',
                  cursor: 'pointer',
                  transition: 'background 150ms ease',
                  position: 'relative',
                }}
                onMouseOver={(e) => {
                  if (!isNotifOpen) e.currentTarget.style.background = '#edeef0';
                }}
                onMouseOut={(e) => {
                  if (!isNotifOpen) e.currentTarget.style.background = 'transparent';
                }}
              >
                <Bell size={18} />
                {unreadCount > 0 && (
                  <span
                    style={{
                      position: 'absolute',
                      top: '4px',
                      right: '4px',
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: '#ef4444',
                      border: '2px solid #ffffff',
                    }}
                  />
                )}
              </button>

              {/* Notification Dropdown Panel */}
              {isNotifOpen && (
                <div className="animate-entrance navbar-dropdown-notif">


                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', paddingBottom: '8px', borderBottom: '1px solid #f0f1f3' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Bell size={16} style={{ color: 'var(--primary)' }} />
                      <span style={{ fontSize: '14px', fontWeight: '800', color: 'var(--on-surface)' }}>Notifications</span>
                      {unreadCount > 0 && (
                        <span style={{ fontSize: '11px', fontWeight: '800', background: '#ede6f8', color: 'var(--primary)', padding: '2px 7px', borderRadius: '9999px' }}>
                          {unreadCount} new
                        </span>
                      )}
                    </div>
                    {unreadCount > 0 && (
                      <button
                        onClick={handleMarkAllRead}
                        style={{ fontSize: '11px', fontWeight: '700', color: 'var(--primary)', background: 'transparent', border: 'none', cursor: 'pointer' }}
                      >
                        Mark all read
                      </button>
                    )}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '280px', overflowY: 'auto' }}>
                    {notifications.map((n) => (
                      <div
                        key={n.id}
                        style={{
                          padding: '10px 12px',
                          borderRadius: '12px',
                          background: n.read ? '#ffffff' : '#f8f5fc',
                          border: n.read ? '1px solid #f0f1f3' : '1px solid #e9d8fd',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '4px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '13px', fontWeight: '700', color: '#111827' }}>{n.title}</span>
                          <span style={{ fontSize: '10px', color: '#9ca3af', fontWeight: '500' }}>{n.time}</span>
                        </div>
                        <p style={{ fontSize: '12px', color: '#6b7280', margin: 0, lineHeight: '1.4' }}>{n.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Profile Dropdown Menu */}
            <div ref={menuRef} style={{ position: 'relative' }}>
              <button
                onClick={() => setIsMenuOpen((prev) => !prev)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: isMenuOpen ? '#e9eaed' : '#f0f1f3',
                  padding: '6px 12px 6px 8px',
                  borderRadius: 'var(--radius-full)',
                  border: isMenuOpen ? '1px solid #c3a5fc' : '1px solid #e1e3e4',
                  cursor: 'pointer',
                  transition: 'all 150ms ease',
                  boxShadow: isMenuOpen ? '0 2px 10px rgba(101, 89, 123, 0.15)' : 'none',
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
                  className="desktop-nav-user-text"
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
                  className="desktop-nav-user-text"
                  style={{
                    color: 'var(--on-surface-variant)',
                    transform: isMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 200ms ease',
                  }}
                />
              </button>

              {/* Profile Dropdown Sub-Menu */}
              {isMenuOpen && (
                <div className="animate-entrance navbar-dropdown-profile">


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
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--on-surface)', textTransform: 'capitalize' }}>
                          {displayName}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--on-surface-variant)' }}>
                          {userEmail}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div style={{ height: '1px', background: '#f0f1f3', margin: '4px 0' }} />

                  {/* Sub-Menu Action 1: Settings */}
                  <button
                    onClick={() => {
                      setIsMenuOpen(false);
                      navigate('/settings');
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
                    <span>Candidate Settings</span>
                  </button>

                  {/* Sub-Menu Action 2: History */}
                  <button
                    onClick={() => {
                      setIsMenuOpen(false);
                      navigate('/history');
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


    {/* Mobile Fixed Bottom Navigation Bar (Phone Screens < 768px) */}
    <nav
      className="mobile-bottom-nav"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        background: 'rgba(255, 255, 255, 0.96)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderTop: '1px solid rgba(101, 89, 123, 0.12)',
        boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.05)',
        padding: '8px 8px 10px 8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
      }}
    >
      {/* Dashboard Tab */}
      <a
        href="/dashboard"
        onClick={(e) => {
          e.preventDefault();
          navigate('/dashboard');
        }}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '3px',
          fontSize: '11px',
          fontWeight: location.pathname === '/dashboard' ? 800 : 600,
          color: location.pathname === '/dashboard' ? '#65597b' : '#6b7280',
          textDecoration: 'none',
          padding: '8px 16px',
          borderRadius: '12px',
          background: location.pathname === '/dashboard' ? '#f3e8ff' : 'transparent',
          transition: 'all 150ms ease',
          flex: 1,
          justifyContent: 'center',
        }}
      >
        <LayoutDashboard size={20} />
        <span>Dashboard</span>
      </a>

      {/* Analytics Tab */}
      <a
        href="/analytics"
        onClick={(e) => {
          e.preventDefault();
          navigate('/analytics');
        }}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '3px',
          fontSize: '11px',
          fontWeight: location.pathname === '/analytics' ? 800 : 600,
          color: location.pathname === '/analytics' ? '#65597b' : '#6b7280',
          textDecoration: 'none',
          padding: '8px 16px',
          borderRadius: '12px',
          background: location.pathname === '/analytics' ? '#f3e8ff' : 'transparent',
          transition: 'all 150ms ease',
          flex: 1,
          justifyContent: 'center',
        }}
      >
        <BarChart2 size={20} />
        <span>Analytics</span>
      </a>

      {/* History Tab */}
      <a
        href="/history"
        onClick={(e) => {
          e.preventDefault();
          navigate('/history');
        }}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '3px',
          fontSize: '11px',
          fontWeight: location.pathname === '/history' ? 800 : 600,
          color: location.pathname === '/history' ? '#65597b' : '#6b7280',
          textDecoration: 'none',
          padding: '8px 16px',
          borderRadius: '12px',
          background: location.pathname === '/history' ? '#f3e8ff' : 'transparent',
          transition: 'all 150ms ease',
          flex: 1,
          justifyContent: 'center',
        }}
      >
        <History size={20} />
        <span>History</span>
      </a>
    </nav>

  </>
  );
};

export default Navbar;

