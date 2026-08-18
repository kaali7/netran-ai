import React, { useState, useEffect } from 'react';
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
} from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { getAggregatedAnalytics } from '../services/analyticsService';

export const Analytics = () => {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('30d');
  const [analyticsData, setAnalyticsData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      const data = await getAggregatedAnalytics(timeRange);
      setAnalyticsData(data);
      setIsLoading(false);
    }
    loadData();
  }, [timeRange]);

  // Fallback while loading
  const data = analyticsData || {
    compositeScore: 82,
    totalSessions: 12,
    trendPercent: 5.2,
    strongestArea: 'System Architecture',
    insights: [],
    skillMatrix: [],
    sessionComparison: [],
  };

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: '60px', fontFamily: 'var(--font-family, system-ui)' }}>
      {/* Shared Navbar Header */}
      <Navbar />

      {/* Main Container */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
        {/* Page Title & Controls Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '28px',
            flexWrap: 'wrap',
            gap: '16px',
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Time Filter Select */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: '#ffffff',
                border: '1px solid #e5e7eb',
                padding: '8px 14px',
                borderRadius: '9999px',
                fontSize: '13px',
                fontWeight: '600',
                color: '#374151',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.02)',
              }}
            >
              <Calendar size={14} style={{ color: '#6b7280' }} />
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                style={{
                  border: 'none',
                  background: 'transparent',
                  fontWeight: '600',
                  fontSize: '13px',
                  color: '#374151',
                  outline: 'none',
                  cursor: 'pointer',
                }}
              >
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
                <option value="all">All Time</option>
              </select>
            </div>

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
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: '24px',
            marginBottom: '24px',
          }}
        >
          {/* COMPOSITE READINESS SCORE CARD */}
          <Card
            style={{
              padding: '32px',
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
              <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#111827', margin: '0 0 8px 0', letterSpacing: '-0.01em' }}>
                Composite Readiness Score
              </h2>
              <p style={{ fontSize: '13px', color: '#6b7280', margin: '0 0 28px 0', lineHeight: '1.5' }}>
                Overall interview readiness based on weighted aggregation of communication, technical knowledge, and empathy metrics.
              </p>

              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '32px' }}>
                {/* Big Score Display */}
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <span style={{ fontSize: '48px', fontWeight: '800', color: '#111827', lineHeight: '1' }}>
                    {data.compositeScore}
                  </span>
                  <span style={{ fontSize: '18px', fontWeight: '700', color: '#6b7280' }}>
                    /100
                  </span>
                </div>

                {/* Right Info Box inside card */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {/* Trend Pill */}
                  <div
                    style={{
                      background: '#fafafa',
                      border: '1px solid #f0f0f0',
                      borderRadius: '12px',
                      padding: '8px 14px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '16px',
                    }}
                  >
                    <span style={{ fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Trend (30d)</span>
                    <span style={{ fontSize: '12px', fontWeight: '700', color: '#15803d', background: '#dcfce7', padding: '3px 8px', borderRadius: '9999px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <TrendingUp size={12} />
                      +{data.trendPercent}%
                    </span>
                  </div>

                  {/* Strongest Area */}
                  <div
                    style={{
                      background: '#fafafa',
                      border: '1px solid #f0f0f0',
                      borderRadius: '12px',
                      padding: '8px 14px',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <span style={{ fontSize: '11px', fontWeight: '600', color: '#6b7280' }}>Strongest Area</span>
                    <span style={{ fontSize: '13px', fontWeight: '700', color: '#111827', marginTop: '2px' }}>
                      {data.strongestArea}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Horizontal Spectrum Slider Bar */}
            <div>
              <div style={{ position: 'relative', width: '100%', height: '10px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden', marginBottom: '8px' }}>
                <div
                  style={{
                    width: `${data.compositeScore}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #8b5cf6 0%, #65597b 100%)',
                    borderRadius: '9999px',
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: '700', color: '#6b7280' }}>
                <span>Novice</span>
                <span>Proficient</span>
                <span>Expert</span>
              </div>
            </div>
          </Card>

          {/* EVA'S INSIGHTS CARD */}
          <Card
            style={{
              padding: '32px',
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
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: '24px',
          }}
        >
          {/* AGGREGATED SKILL MATRIX CARD */}
          <Card
            style={{
              padding: '32px',
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
              padding: '32px',
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
      </main>
    </div>
  );
};

export default Analytics;
