import React, { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import useAuth from '../hooks/useAuth';
import useAuthStore from '../store/authStore';
import {
  User,
  Mail,
  Lock,
  Sliders,
  Mic,
  Volume2,
  CheckCircle2,
  Sparkles,
  Shield,
  Save,
  Key,
  Briefcase,
  Layers,
} from 'lucide-react';

export const Settings = () => {
  const { user } = useAuth();
  const updateUser = useAuthStore((state) => state.updateUser);

  const initialEmail = user?.email || 'candidate@netran.ai';
  const initialName = user?.name || (user?.email ? user.email.split('@')[0] : 'Candidate');

  // Form State
  const [displayName, setDisplayName] = useState(initialName);
  const [targetRole, setTargetRole] = useState('Senior Fullstack Engineer');
  const [seniorityLevel, setSeniorityLevel] = useState('Senior');
  const [interviewerPersona, setInterviewerPersona] = useState('Eva');
  const [aiStrictness, setAiStrictness] = useState('standard');
  const [targetPacing, setTargetPacing] = useState('180');
  const [autoPlayAudio, setAutoPlayAudio] = useState(true);
  const [noiseSuppression, setNoiseSuppression] = useState(true);

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  // Save Success State
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSaveProfile = (e) => {
    e.preventDefault();
    updateUser({ name: displayName, email: initialEmail });
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3500);
  };

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess(false);

    if (!currentPassword) {
      setPasswordError('Please enter your current password.');
      return;
    }
    if (newPassword.length < 6) {
      setPasswordError('New password must be at least 6 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New password and confirm password do not match.');
      return;
    }

    // Success simulation
    setPasswordSuccess(true);
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setTimeout(() => setPasswordSuccess(false), 4000);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
      {/* Top Navbar */}
      <Navbar userName={displayName} />

      {/* Main Container */}
      <PageWrapper>
        {/* Header Title Section */}
        <div style={{ marginBottom: '28px' }} className="animate-entrance">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '12px',
                fontWeight: '700',
                padding: '4px 12px',
                background: '#ede6f8',
                color: 'var(--primary)',
                borderRadius: '9999px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <Sparkles size={13} />
              <span>Candidate Account & Preferences</span>
            </span>
          </div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', color: 'var(--on-surface)', margin: 0, letterSpacing: '-0.02em' }}>
            Settings & Profile Configuration
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)', margin: '6px 0 0 0' }}>
            Manage your candidate profile details, default AI interviewer persona parameters, and security settings.
          </p>
        </div>

        {/* Global Success Notification */}
        {saveSuccess && (
          <div
            style={{
              padding: '14px 20px',
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              color: '#166534',
              fontWeight: '700',
              fontSize: '14px',
              marginBottom: '24px',
              boxShadow: '0 4px 14px rgba(22, 101, 52, 0.08)',
            }}
            className="animate-entrance"
          >
            <CheckCircle2 size={20} style={{ color: '#16a34a', flexShrink: 0 }} />
            <span>Profile and practice preferences saved successfully!</span>
          </div>
        )}

        {/* 2-Column Glassmorphic Layout Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
            gap: '24px',
            marginBottom: '40px',
          }}
        >
          {/* LEFT COLUMN: Candidate Profile & Security */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Card 1: Candidate Information */}
            <form onSubmit={handleSaveProfile} className="glass-card animate-entrance">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '12px',
                    background: '#ede6f8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--primary)',
                  }}
                >
                  <User size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', margin: 0, color: 'var(--on-surface)' }}>
                    Candidate Profile
                  </h3>
                  <p style={{ fontSize: '12px', margin: 0, color: 'var(--on-surface-variant)' }}>
                    Personal display identity and career target
                  </p>
                </div>
              </div>

              {/* Display Name Field */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '6px' }}>
                  Full Display Name
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Candidate Name"
                    style={{
                      width: '100%',
                      padding: '11px 14px 11px 38px',
                      borderRadius: '12px',
                      border: '1px solid #d9dadb',
                      fontSize: '14px',
                      outline: 'none',
                      background: '#ffffff',
                      color: 'var(--on-surface)',
                    }}
                  />
                  <User size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
                </div>
              </div>

              {/* Target Career Track Field */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '6px' }}>
                  Primary Target Career Track
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    placeholder="e.g. Senior Fullstack Engineer"
                    style={{
                      width: '100%',
                      padding: '11px 14px 11px 38px',
                      borderRadius: '12px',
                      border: '1px solid #d9dadb',
                      fontSize: '14px',
                      outline: 'none',
                      background: '#ffffff',
                      color: 'var(--on-surface)',
                    }}
                  />
                  <Briefcase size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
                </div>
              </div>

              {/* Email Field (Readonly) */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '6px' }}>
                  Account Email Address
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="email"
                    value={initialEmail}
                    disabled
                    style={{
                      width: '100%',
                      padding: '11px 14px 11px 38px',
                      borderRadius: '12px',
                      border: '1px solid #e5e7eb',
                      fontSize: '14px',
                      background: '#f9fafb',
                      color: '#6b7280',
                      cursor: 'not-allowed',
                    }}
                  />
                  <Mail size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', padding: '12px', fontSize: '14px' }}
              >
                <Save size={16} />
                <span>Save Candidate Profile</span>
              </button>
            </form>

            {/* Card 2: Password & Credentials */}
            <form onSubmit={handlePasswordSubmit} className="glass-card animate-entrance animate-delay-1">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '12px',
                    background: '#faede2',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#c2410c',
                  }}
                >
                  <Lock size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', margin: 0, color: 'var(--on-surface)' }}>
                    Security & Password
                  </h3>
                  <p style={{ fontSize: '12px', margin: 0, color: 'var(--on-surface-variant)' }}>
                    Update your login credentials securely
                  </p>
                </div>
              </div>

              {passwordSuccess && (
                <div
                  style={{
                    padding: '10px 14px',
                    background: '#f0fdf4',
                    border: '1px solid #bbf7d0',
                    borderRadius: '10px',
                    color: '#166534',
                    fontSize: '13px',
                    fontWeight: '600',
                    marginBottom: '16px',
                  }}
                >
                  Password updated successfully!
                </div>
              )}

              {passwordError && (
                <div
                  style={{
                    padding: '10px 14px',
                    background: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '10px',
                    color: '#991b1b',
                    fontSize: '13px',
                    fontWeight: '600',
                    marginBottom: '16px',
                  }}
                >
                  {passwordError}
                </div>
              )}

              {/* Current Password */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '6px' }}>
                  Current Password
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    border: '1px solid #d9dadb',
                    fontSize: '14px',
                    outline: 'none',
                    background: '#ffffff',
                  }}
                />
              </div>

              {/* New Password */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '6px' }}>
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    border: '1px solid #d9dadb',
                    fontSize: '14px',
                    outline: 'none',
                    background: '#ffffff',
                  }}
                />
              </div>

              {/* Confirm New Password */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '6px' }}>
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    border: '1px solid #d9dadb',
                    fontSize: '14px',
                    outline: 'none',
                    background: '#ffffff',
                  }}
                />
              </div>

              <button
                type="submit"
                className="btn btn-ghost"
                style={{ width: '100%', padding: '10px', fontSize: '13px' }}
              >
                <Key size={15} />
                <span>Update Password</span>
              </button>
            </form>
          </div>

          {/* RIGHT COLUMN: AI Interviewer Preferences & Hardware */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Card 3: AI Interviewer Persona Preferences */}
            <div className="glass-card animate-entrance animate-delay-1">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '12px',
                    background: '#e0f2fe',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#0284c7',
                  }}
                >
                  <Sliders size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', margin: 0, color: 'var(--on-surface)' }}>
                    Practice & Persona Defaults
                  </h3>
                  <p style={{ fontSize: '12px', margin: 0, color: 'var(--on-surface-variant)' }}>
                    Customize Eva's strictness and default track seniority
                  </p>
                </div>
              </div>

              {/* Target Seniority Selector */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '6px' }}>
                  Default Seniority Level
                </label>
                <select
                  value={seniorityLevel}
                  onChange={(e) => setSeniorityLevel(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '12px',
                    border: '1px solid #d9dadb',
                    fontSize: '14px',
                    background: '#ffffff',
                    color: 'var(--on-surface)',
                    outline: 'none',
                    fontWeight: '600',
                  }}
                >
                  <option value="Junior">Junior (0-2 Years)</option>
                  <option value="Mid-Level">Mid-Level (2-5 Years)</option>
                  <option value="Senior">Senior (5+ Years)</option>
                  <option value="Staff/Lead">Staff / Principal Lead (8+ Years)</option>
                </select>
              </div>

              {/* AI Strictness Radio Cards */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '8px' }}>
                  Interviewer Strictness Level
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <label
                    style={{
                      padding: '12px 14px',
                      borderRadius: '12px',
                      border: aiStrictness === 'encouraging' ? '2px solid #65597b' : '1px solid #e5e7eb',
                      background: aiStrictness === 'encouraging' ? '#f7f5fb' : '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="radio"
                      name="strictness"
                      value="encouraging"
                      checked={aiStrictness === 'encouraging'}
                      onChange={() => setAiStrictness('encouraging')}
                    />
                    <div>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', display: 'block' }}>
                        Encouraging & Conversational
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--on-surface-variant)' }}>
                        Provides subtle hints and supportive follow-ups
                      </span>
                    </div>
                  </label>

                  <label
                    style={{
                      padding: '12px 14px',
                      borderRadius: '12px',
                      border: aiStrictness === 'standard' ? '2px solid #65597b' : '1px solid #e5e7eb',
                      background: aiStrictness === 'standard' ? '#f7f5fb' : '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="radio"
                      name="strictness"
                      value="standard"
                      checked={aiStrictness === 'standard'}
                      onChange={() => setAiStrictness('standard')}
                    />
                    <div>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', display: 'block' }}>
                        Standard Technical Rigor (Recommended)
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--on-surface-variant)' }}>
                        Balanced tech probing with trade-off deep dives
                      </span>
                    </div>
                  </label>

                  <label
                    style={{
                      padding: '12px 14px',
                      borderRadius: '12px',
                      border: aiStrictness === 'rigorous' ? '2px solid #65597b' : '1px solid #e5e7eb',
                      background: aiStrictness === 'rigorous' ? '#f7f5fb' : '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="radio"
                      name="strictness"
                      value="rigorous"
                      checked={aiStrictness === 'rigorous'}
                      onChange={() => setAiStrictness('rigorous')}
                    />
                    <div>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', display: 'block' }}>
                        Faang-Level Challenge Mode
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--on-surface-variant)' }}>
                        Strict rubric scoring, edge-case probing & zero hand-holding
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              {/* Per-Question Target Pacing Selector */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '6px' }}>
                  Target Pacing Per Question
                </label>
                <select
                  value={targetPacing}
                  onChange={(e) => setTargetPacing(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '12px',
                    border: '1px solid #d9dadb',
                    fontSize: '14px',
                    background: '#ffffff',
                    color: 'var(--on-surface)',
                    outline: 'none',
                    fontWeight: '600',
                  }}
                >
                  <option value="120">2 Minutes (Concise Pacing)</option>
                  <option value="180">3 Minutes (Standard Pacing)</option>
                  <option value="240">4 Minutes (Deep Architecture Pacing)</option>
                </select>
              </div>
            </div>

            {/* Card 4: Audio Hardware & Media Preferences */}
            <div className="glass-card animate-entrance animate-delay-2">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '12px',
                    background: '#dcfce7',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#15803d',
                  }}
                >
                  <Mic size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', margin: 0, color: 'var(--on-surface)' }}>
                    Voice & Audio Settings
                  </h3>
                  <p style={{ fontSize: '12px', margin: 0, color: 'var(--on-surface-variant)' }}>
                    Web Audio PCM streaming and microphone preferences
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Auto Play Toggle */}
                <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                  <div>
                    <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--on-surface)', display: 'block' }}>
                      Gapless Neural TTS Auto-Play
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--on-surface-variant)' }}>
                      Automatically stream Kokoro 82M voice chunks on response
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={autoPlayAudio}
                    onChange={(e) => setAutoPlayAudio(e.target.checked)}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                  />
                </label>

                <div style={{ height: '1px', background: '#f0f1f3' }} />

                {/* Noise Suppression Toggle */}
                <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                  <div>
                    <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--on-surface)', display: 'block' }}>
                      Silero VAD Noise Cancellation
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--on-surface-variant)' }}>
                      Inline 16kHz high-pass filtering & dynamic room noise floor gate
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={noiseSuppression}
                    onChange={(e) => setNoiseSuppression(e.target.checked)}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                  />
                </label>
              </div>
            </div>
          </div>
        </div>
      </PageWrapper>
    </div>
  );
};

export default Settings;
