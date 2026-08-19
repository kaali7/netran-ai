import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Download,
  Calendar,
  MoreVertical,
  Sparkles,
  Award,
  CheckCircle2,
  AlertCircle,
  BarChart2,
  Layers,
  History,
  Target,
  ChevronDown,
  Check,
} from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { getAggregatedAnalytics } from '../services/analyticsService';

export const Analytics = () => {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('30d');
  const [analyticsData, setAnalyticsData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Custom glassmorphic dropdown state
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Custom date range modal state
  const [showCustomModal, setShowCustomModal] = useState(false);
  const [customMode, setCustomMode] = useState('days'); // 'days' | 'dates'
  const [customDays, setCustomDays] = useState(45);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [appliedCustomOptions, setAppliedCustomOptions] = useState({});

  const rangeOptions = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '15d', label: 'Last 15 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '60d', label: 'Last 60 Days' },
    { value: '90d', label: 'Last 90 Days' },
    { value: 'all', label: 'All Time' },
    { value: 'custom', label: 'Custom Range...' },
  ];

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectTimeRange = (newRange) => {
    setTimeRange(newRange);
    if (newRange === 'custom') {
      setShowCustomModal(true);
    } else {
      setShowCustomModal(false);
      fetchData(newRange, {});
    }
  };

  const fetchData = async (range, customOpts) => {
    setIsLoading(true);
    const data = await getAggregatedAnalytics(range, customOpts);
    setAnalyticsData(data);
    setIsLoading(false);
  };

  useEffect(() => {
    if (timeRange !== 'custom') {
      fetchData(timeRange, {});
    }
  }, [timeRange]);

  const handleApplyCustom = () => {
    const opts = {};
    if (customMode === 'days') {
      opts.customDays = Number(customDays) || 30;
    } else {
      opts.startDate = startDate;
      opts.endDate = endDate;
    }
    setAppliedCustomOptions(opts);
    setShowCustomModal(false);
    fetchData('custom', opts);
  };

  // Default data structure while loading
  const data = analyticsData || {
    compositeScore: 0,
    totalSessions: 0,
    trendPercent: 0,
    strongestArea: 'Loading analytics...',
    insights: [],
    skillMatrix: [],
    sessionComparison: [],
  };

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: '60px', fontFamily: 'var(--font-family, system-ui)', position: 'relative' }}>
      {/* Shared Navbar Header */}
      <Navbar />

      {/* Main Container */}
      <PageWrapper>
        {/* Page Title & Controls Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '28px',
            flexWrap: 'wrap',
            gap: '16px',
            position: 'relative',
            zIndex: 50,
          }}
          className="animate-entrance"
        >
          <div>
            <h1
              style={{
                fontSize: '26px',
                fontWeight: '800',
                color: '#111827',
                letterSpacing: '-0.02em',
                margin: 0,
              }}
            >
              Master Performance Report
            </h1>
            <p style={{ fontSize: '14px', color: '#6b7280', margin: '4px 0 0 0' }}>
              Aggregated analysis from {data.totalSessions} selected interview sessions.
            </p>
          </div>

          {/* Right Action Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', position: 'relative', zIndex: 60 }}>
            {/* Custom Glassmorphic Time Filter Dropdown */}
            <div ref={dropdownRef} style={{ position: 'relative', zIndex: 70 }}>
              <button
                type="button"
                onClick={() => setIsDropdownOpen((prev) => !prev)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: '#ffffff',
                  border: isDropdownOpen ? '1px solid #65597b' : '1px solid #e5e7eb',
                  padding: '8px 16px',
                  borderRadius: '9999px',
                  fontSize: '13px',
                  fontWeight: '700',
                  color: '#374151',
                  cursor: 'pointer',
                  boxShadow: isDropdownOpen ? '0 0 0 3px rgba(101, 89, 123, 0.12)' : '0 2px 6px rgba(0, 0, 0, 0.03)',
                  transition: 'all 200ms ease',
                }}
              >
                <Calendar size={15} style={{ color: '#65597b' }} />
                <span>
                  {rangeOptions.find((o) => o.value === timeRange)?.label || 'Select Window'}
                </span>
                <ChevronDown
                  size={14}
                  style={{
                    color: '#6b7280',
                    transform: isDropdownOpen ? 'rotate(180deg)' : 'none',
                    transition: 'transform 200ms ease',
                  }}
                />
              </button>

              {/* Glassmorphic Dropdown Menu */}
              {isDropdownOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: '44px',
                    right: 0,
                    zIndex: 9999,
                    width: '190px',
                    background: 'rgba(255, 255, 255, 0.98)',
                    backdropFilter: 'blur(16px)',
                    border: '1px solid rgba(229, 231, 235, 0.8)',
                    borderRadius: '16px',
                    padding: '6px',
                    boxShadow: '0 16px 36px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.06)',
                  }}
                  className="animate-entrance"
                >
                  {rangeOptions.map((opt) => {
                    const isSelected = timeRange === opt.value;
                    const isCustom = opt.value === 'custom';
                    return (
                      <React.Fragment key={opt.value}>
                        {isCustom && <div style={{ height: '1px', background: '#f3f4f6', margin: '4px 0' }} />}
                        <button
                          type="button"
                          onClick={() => {
                            setIsDropdownOpen(false);
                            handleSelectTimeRange(opt.value);
                          }}
                          style={{
                            width: '100%',
                            padding: '9px 12px',
                            borderRadius: '10px',
                            border: 'none',
                            background: isSelected ? '#ede6f8' : 'transparent',
                            color: isSelected ? '#65597b' : '#374151',
                            fontSize: '13px',
                            fontWeight: isSelected ? '700' : '600',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            cursor: 'pointer',
                            transition: 'background 150ms ease, color 150ms ease',
                            textAlign: 'left',
                          }}
                          onMouseEnter={(e) => {
                            if (!isSelected) e.currentTarget.style.background = '#f5f3ff';
                          }}
                          onMouseLeave={(e) => {
                            if (!isSelected) e.currentTarget.style.background = 'transparent';
                          }}
                        >
                          <span>{opt.label}</span>
                          {isSelected && <Check size={14} style={{ color: '#65597b' }} />}
                        </button>
                      </React.Fragment>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Custom Range Popover Card */}
            {showCustomModal && (
              <div
                style={{
                  position: 'absolute',
                  top: '48px',
                  right: '120px',
                  zIndex: 9999,
                  width: '320px',
                  background: 'rgba(255, 255, 255, 0.98)',
                  backdropFilter: 'blur(16px)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '20px',
                  padding: '20px',
                  boxShadow: '0 16px 40px rgba(0, 0, 0, 0.12)',
                }}
                className="animate-entrance"
              >
                <h3 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 14px 0', color: '#111827' }}>
                  Select Custom Time Window
                </h3>

                {/* Sub-mode Switcher */}
                <div style={{ display: 'flex', background: '#f3f4f6', padding: '4px', borderRadius: '12px', marginBottom: '16px' }}>
                  <button
                    onClick={() => setCustomMode('days')}
                    style={{
                      flex: 1,
                      padding: '6px',
                      borderRadius: '8px',
                      border: 'none',
                      fontSize: '12px',
                      fontWeight: '700',
                      background: customMode === 'days' ? '#ffffff' : 'transparent',
                      color: customMode === 'days' ? '#111827' : '#6b7280',
                      cursor: 'pointer',
                      boxShadow: customMode === 'days' ? '0 2px 4px rgba(0,0,0,0.05)' : 'none',
                    }}
                  >
                    Days Count
                  </button>
                  <button
                    onClick={() => setCustomMode('dates')}
                    style={{
                      flex: 1,
                      padding: '6px',
                      borderRadius: '8px',
                      border: 'none',
                      fontSize: '12px',
                      fontWeight: '700',
                      background: customMode === 'dates' ? '#ffffff' : 'transparent',
                      color: customMode === 'dates' ? '#111827' : '#6b7280',
                      cursor: 'pointer',
                      boxShadow: customMode === 'dates' ? '0 2px 4px rgba(0,0,0,0.05)' : 'none',
                    }}
                  >
                    Date Picker
                  </button>
                </div>

                {customMode === 'days' ? (
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ fontSize: '12px', fontWeight: '600', color: '#4b5563', display: 'block', marginBottom: '6px' }}>
                      Lookback Window (Days)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={customDays}
                      onChange={(e) => setCustomDays(e.target.value)}
                      placeholder="e.g. 45"
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        borderRadius: '10px',
                        border: '1px solid #d1d5db',
                        fontSize: '13px',
                        outline: 'none',
                      }}
                    />
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ fontSize: '12px', fontWeight: '600', color: '#4b5563', display: 'block', marginBottom: '4px' }}>
                        Start Date
                      </label>
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          borderRadius: '10px',
                          border: '1px solid #d1d5db',
                          fontSize: '13px',
                          outline: 'none',
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '12px', fontWeight: '600', color: '#4b5563', display: 'block', marginBottom: '4px' }}>
                        End Date
                      </label>
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          borderRadius: '10px',
                          border: '1px solid #d1d5db',
                          fontSize: '13px',
                          outline: 'none',
                        }}
                      />
                    </div>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                  <button
                    onClick={() => {
                      setShowCustomModal(false);
                      setTimeRange('30d');
                    }}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '9999px',
                      border: '1px solid #e5e7eb',
                      background: '#ffffff',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#4b5563',
                      cursor: 'pointer',
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleApplyCustom}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '9999px',
                      border: 'none',
                      background: '#65597b',
                      color: '#ffffff',
                      fontSize: '12px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      boxShadow: '0 2px 8px rgba(101, 89, 123, 0.3)',
                    }}
                  >
                    Apply Filter
                  </button>
                </div>
              </div>
            )}

            {/* Export PDF Button */}
            <button
              onClick={() => window.print()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                borderRadius: '9999px',
                background: '#65597b',
                color: '#ffffff',
                border: 'none',
                fontWeight: '700',
                fontSize: '13px',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(101, 89, 123, 0.25)',
              }}
            >
              <Download size={15} />
              <span>Export PDF</span>
            </button>
          </div>
        </div>

        {/* TOP ROW GRID */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px',
            marginBottom: '24px',
          }}
        >
          {/* COMPOSITE READINESS SCORE CARD */}
          <Card
            style={{
              padding: '20px 16px',
              background: '#ffffff',
              borderRadius: '24px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '800', color: '#111827', margin: '0 0 6px 0', letterSpacing: '-0.01em' }}>
                Composite Readiness Score
              </h2>
              <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 14px 0', lineHeight: '1.4' }}>
                Overall interview readiness based on weighted aggregation of communication, technical knowledge, and empathy metrics.
              </p>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
                {/* Big Score Display */}
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                  <span style={{ fontSize: '42px', fontWeight: '800', color: '#111827', lineHeight: '1' }}>
                    {data.compositeScore}
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: '#6b7280' }}>
                    /100
                  </span>
                </div>

                {/* Info Box inside card - side by side on mobile */}
                <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: '8px', flex: 1, minWidth: '220px' }}>
                  {/* Trend Pill */}
                  <div
                    style={{
                      flex: 1,
                      minWidth: '110px',
                      background: '#fafafa',
                      border: '1px solid #f0f0f0',
                      borderRadius: '12px',
                      padding: '6px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '8px',
                    }}
                  >
                    <span style={{ fontSize: '11px', fontWeight: '600', color: '#6b7280' }}>Trend (30d)</span>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: '#15803d', background: '#dcfce7', padding: '2px 6px', borderRadius: '9999px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                      <TrendingUp size={11} />
                      +{data.trendPercent}%
                    </span>
                  </div>

                  {/* Strongest Area */}
                  <div
                    style={{
                      flex: 1.2,
                      minWidth: '130px',
                      background: '#fafafa',
                      border: '1px solid #f0f0f0',
                      borderRadius: '12px',
                      padding: '6px 10px',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <span style={{ fontSize: '10px', fontWeight: '600', color: '#6b7280' }}>Strongest Area</span>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: '#111827', marginTop: '1px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {data.strongestArea}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Horizontal Spectrum Slider Bar */}
            <div style={{ marginTop: '8px' }}>
              <div style={{ position: 'relative', width: '100%', height: '8px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden', marginBottom: '6px' }}>
                <div
                  style={{
                    width: `${data.compositeScore}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #8b5cf6 0%, #65597b 100%)',
                    borderRadius: '9999px',
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: '700', color: '#6b7280' }}>
                <span>Novice</span>
                <span>Proficient</span>
                <span>Expert</span>
              </div>
            </div>
          </Card>


          {/* EVA'S INSIGHTS CARD */}
          <Card
            style={{
              padding: '24px 20px',
              background: '#ffffff',
              borderRadius: '24px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#f5f0fb', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#65597b' }}>
                <Sparkles size={20} />
              </div>
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: '800', color: '#111827', margin: 0 }}>
                  Eva's Insights
                </h2>
                <span style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600' }}>
                  AI Synthesis
                </span>
              </div>
            </div>

            {/* Callout Feedback Items */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, justifyContent: 'center' }}>
              {(data.insights || []).map((item) => (
                <div
                  key={item.id}
                  style={{
                    padding: '14px 16px',
                    borderRadius: '12px',
                    background: '#f9fafb',
                    borderLeft: item.type === 'positive' ? '4px solid #16a34a' : '4px solid #dc2626',
                    fontSize: '13px',
                    color: '#374151',
                    lineHeight: '1.5',
                  }}
                >
                  {item.text}
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* BOTTOM ROW GRID */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px',
          }}
        >
          {/* AGGREGATED SKILL MATRIX CARD */}
          <Card
            style={{
              padding: '24px 20px',
              background: '#ffffff',
              borderRadius: '24px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: '800', color: '#111827', margin: '0 0 24px 0' }}>
              Aggregated Skill Matrix
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {(data.skillMatrix || []).map((skill, idx) => (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px', fontWeight: '700', color: '#374151' }}>
                    <span>{skill.name}</span>
                    <span>{skill.score}%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${skill.score}%`,
                        height: '100%',
                        background: skill.color || '#65597b',
                        borderRadius: '9999px',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* SESSION COMPARISON BAR CHART CARD */}
          <Card
            style={{
              padding: '24px 20px',
              background: '#ffffff',
              borderRadius: '24px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
              display: 'flex',
              flexDirection: 'column',

              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: '800', color: '#111827', margin: 0 }}>
                Session Comparison
              </h2>
              <button
                style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer' }}
                aria-label="Options"
              >
                <MoreVertical size={18} />
              </button>
            </div>

            {/* Custom SVG / CSS Bar Chart */}
            <div style={{ width: '100%', height: '180px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', gap: '16px', paddingBottom: '8px', borderBottom: '1px solid #f3f4f6' }}>
              {(data.sessionComparison || []).map((s, idx) => (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, height: '100%', justifyContent: 'flex-end', position: 'relative' }}>
                  {/* Score Tooltip Pill for Active Bar */}
                  {s.active && (
                    <div
                      style={{
                        position: 'absolute',
                        top: `${100 - s.score - 18}%`,
                        background: '#111827',
                        color: '#ffffff',
                        fontSize: '11px',
                        fontWeight: '800',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                      }}
                    >
                      {s.score}
                    </div>
                  )}

                  {/* Bar */}
                  <div
                    style={{
                      width: '100%',
                      maxWidth: '48px',
                      height: `${s.score}%`,
                      background: s.active ? '#65597b' : '#f3f4f6',
                      borderRadius: '8px 8px 0 0',
                      transition: 'all 300ms ease',
                    }}
                  />
                </div>
              ))}
            </div>

            {/* X-Axis Labels */}
            <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '12px' }}>
              {(data.sessionComparison || []).map((s, idx) => (
                <span key={idx} style={{ fontSize: '12px', fontWeight: '700', color: s.active ? '#65597b' : '#9ca3af' }}>
                  {s.label}
                </span>
              ))}
            </div>
          </Card>
        </div>
      </PageWrapper>
    </div>
  );
};

export default Analytics;

