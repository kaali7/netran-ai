import React from 'react';
import {
  UserCheck,
  Mail,
  Phone,
  MapPin,
  CheckCircle,
  AlertTriangle,
  Code,
  Briefcase,
  GraduationCap,
  FolderGit2,
  Award,
  Sparkles,
  TrendingUp,
  Target,
  FileText,
} from 'lucide-react';

/**
 * ResumeAnalysisTab — Renders full structured candidate profile and AI evaluation.
 * Combines parsed resume data (CandidateProfile) with Stage 2 evaluation artifacts (resume_analysis).
 *
 * @param {object} resumeAnalysis - Stage 2 resume analysis artifact payload
 * @param {object} parsedResume - Initial CandidateProfile extracted from /ingest/resume
 */
export const ResumeAnalysisTab = ({ resumeAnalysis, parsedResume }) => {
  // Candidate Profile fields (from parsedResume or resumeAnalysis candidate_profile)
  const candidateName = parsedResume?.name || resumeAnalysis?.candidate_profile?.candidate_name || 'Candidate';
  const email = parsedResume?.email;
  const phone = parsedResume?.phone;
  const location = parsedResume?.location;
  const summary =
    parsedResume?.summary ||
    resumeAnalysis?.candidate_profile?.core_identity_summary ||
    resumeAnalysis?.summary ||
    'Resume successfully parsed and indexed.';

  const technicalSkills = parsedResume?.technical_skills?.length > 0 ? parsedResume.technical_skills : [];
  const softSkills = parsedResume?.soft_skills?.length > 0 ? parsedResume.soft_skills : (resumeAnalysis?.candidate_profile?.soft_skills || []);

  // Work History (from CandidateProfile or resume_analysis)
  const workHistory = parsedResume?.work_history?.length > 0 ? parsedResume.work_history : (resumeAnalysis?.experience_and_work_history || []);

  // Education (from CandidateProfile)
  const education = parsedResume?.education || [];

  // Projects (from CandidateProfile or detailed_project_analysis)
  const projects = parsedResume?.projects?.length > 0 ? parsedResume.projects : (resumeAnalysis?.detailed_project_analysis || []);

  // Certifications
  const certifications = parsedResume?.certifications || [];

  // Stage 2 Scoring Artifacts (if analysis completed)
  const fitScoring = resumeAnalysis?.role_fit_scoring || {};
  const overallMatchScore =
    fitScoring.overall_jd_match_score ||
    resumeAnalysis?.role_fit_score ||
    resumeAnalysis?.match_score ||
    null;

  const skillOverlap = resumeAnalysis?.extracted_skill_overlap || [];
  const strengths = resumeAnalysis?.strengths || resumeAnalysis?.key_strengths || [];
  const gaps = resumeAnalysis?.gaps || resumeAnalysis?.areas_for_growth || resumeAnalysis?.experience_gaps_and_red_flags?.technical_gaps || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxHeight: '520px', overflowY: 'auto', paddingRight: '4px' }}>
      
      {/* ── 1. Candidate Profile Header Card ─────────────────────────────── */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(245, 240, 255, 0.9))',
          border: '1.5px solid rgba(101, 89, 123, 0.15)',
          borderRadius: '18px',
          padding: '20px 22px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: 'var(--primary-container)',
                  color: 'var(--on-primary-container)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '700',
                  fontSize: '15px',
                }}
              >
                {candidateName.charAt(0).toUpperCase()}
              </div>
              <h2 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--on-surface)', margin: 0 }}>
                {candidateName}
              </h2>
            </div>

            {/* Contact Badges */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap', marginTop: '8px' }}>
              {email && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12.5px', color: 'var(--on-surface-variant)' }}>
                  <Mail size={14} color="var(--primary)" />
                  <span>{email}</span>
                </div>
              )}
              {phone && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12.5px', color: 'var(--on-surface-variant)' }}>
                  <Phone size={14} color="var(--primary)" />
                  <span>{phone}</span>
                </div>
              )}
              {location && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12.5px', color: 'var(--on-surface-variant)' }}>
                  <MapPin size={14} color="var(--primary)" />
                  <span>{location}</span>
                </div>
              )}
            </div>
          </div>

          {/* Overall Match Score Pill */}
          {overallMatchScore !== null && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '9999px',
                background: 'linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%)',
                color: '#ffffff',
                boxShadow: '0 4px 12px rgba(45, 106, 79, 0.25)',
              }}
            >
              <TrendingUp size={16} />
              <span style={{ fontSize: '13px', fontWeight: '800' }}>{overallMatchScore}% JD MATCH</span>
            </div>
          )}
        </div>

        {/* Summary */}
        <p style={{ fontSize: '13.5px', color: 'var(--on-surface-variant)', marginTop: '14px', marginBottom: 0, lineHeight: '1.5' }}>
          {summary}
        </p>
      </div>

      {/* ── 2. Stage 2 Role Fit Scores Breakdown Grid (If Available) ─────── */}
      {Object.keys(fitScoring).length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px' }}>
          {fitScoring.technical_depth_score && (
            <div style={{ background: '#fbf9fe', border: '1px solid rgba(101, 89, 123, 0.12)', padding: '10px 14px', borderRadius: '12px' }}>
              <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--outline)' }}>TECHNICAL DEPTH</div>
              <div style={{ fontSize: '18px', fontWeight: '800', color: 'var(--primary)', marginTop: '2px' }}>
                {fitScoring.technical_depth_score}%
              </div>
            </div>
          )}
          {fitScoring.experience_seniority_score && (
            <div style={{ background: '#fbf9fe', border: '1px solid rgba(101, 89, 123, 0.12)', padding: '10px 14px', borderRadius: '12px' }}>
              <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--outline)' }}>SENIORITY MATCH</div>
              <div style={{ fontSize: '18px', fontWeight: '800', color: 'var(--secondary)', marginTop: '2px' }}>
                {fitScoring.experience_seniority_score}%
              </div>
            </div>
          )}
          {fitScoring.project_relevance_score && (
            <div style={{ background: '#fbf9fe', border: '1px solid rgba(101, 89, 123, 0.12)', padding: '10px 14px', borderRadius: '12px' }}>
              <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--outline)' }}>PROJECT RELEVANCE</div>
              <div style={{ fontSize: '18px', fontWeight: '800', color: '#0369a1', marginTop: '2px' }}>
                {fitScoring.project_relevance_score}%
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── 3. Extracted Technical & Soft Skills ──────────────────────────── */}
      {technicalSkills.length > 0 && (
        <div style={{ background: 'rgba(255, 255, 255, 0.85)', border: '1.5px solid rgba(101, 89, 123, 0.12)', borderRadius: '16px', padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Code size={16} color="var(--primary)" />
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--on-surface-variant)' }}>
              TECHNICAL SKILLS ({technicalSkills.length})
            </span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {technicalSkills.map((skill, idx) => (
              <span
                key={idx}
                style={{
                  padding: '6px 12px',
                  borderRadius: '9999px',
                  background: 'rgba(101, 89, 123, 0.08)',
                  color: 'var(--primary)',
                  fontSize: '12.5px',
                  fontWeight: '700',
                }}
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ── 4. Work History Section ─────────────────────────────────────── */}
      {workHistory.length > 0 && (
        <div style={{ background: 'rgba(255, 255, 255, 0.85)', border: '1.5px solid rgba(101, 89, 123, 0.12)', borderRadius: '16px', padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Briefcase size={16} color="var(--primary)" />
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--on-surface-variant)' }}>
              WORK EXPERIENCE HISTORY
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {workHistory.map((item, idx) => {
              const comp = item.company || item.company_name || 'Organization';
              const role = item.role || 'Software Engineer';
              const duration = item.duration || item.tenure || '';
              const resp = item.responsibilities || item.key_responsibilities || [];

              return (
                <div key={idx} style={{ paddingBottom: idx !== workHistory.length - 1 ? '12px' : 0, borderBottom: idx !== workHistory.length - 1 ? '1px solid rgba(0,0,0,0.06)' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: '6px' }}>
                    <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--on-surface)' }}>{role}</span>
                    <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--primary)' }}>{comp}</span>
                  </div>
                  {duration && (
                    <div style={{ fontSize: '11.5px', color: 'var(--outline)', marginTop: '2px', fontWeight: '600' }}>
                      {duration}
                    </div>
                  )}
                  {Array.isArray(resp) && resp.length > 0 && (
                    <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px', fontSize: '12.5px', color: 'var(--on-surface-variant)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      {resp.map((r, rIdx) => (
                        <li key={rIdx}>{r}</li>
                      ))}
                    </ul>
                  )}
                  {typeof resp === 'string' && (
                    <p style={{ fontSize: '12.5px', color: 'var(--on-surface-variant)', marginTop: '6px', marginBottom: 0 }}>{resp}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 5. Projects Showcase ─────────────────────────────────────────── */}
      {projects.length > 0 && (
        <div style={{ background: 'rgba(255, 255, 255, 0.85)', border: '1.5px solid rgba(101, 89, 123, 0.12)', borderRadius: '16px', padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <FolderGit2 size={16} color="var(--primary)" />
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--on-surface-variant)' }}>
              PROJECT HIGHLIGHTS
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {projects.map((proj, idx) => {
              const projName = typeof proj === 'string' ? proj.split('|')[0] : (proj.project_name || 'Technical Project');
              const projDesc = typeof proj === 'string' ? proj : (proj.quantifiable_scale || proj.architecture_type || '');
              const techStack = proj.tech_stack_used || [];

              return (
                <div key={idx} style={{ background: '#fcfbfe', border: '1px solid rgba(101, 89, 123, 0.1)', borderRadius: '12px', padding: '12px 14px' }}>
                  <div style={{ fontSize: '13.5px', fontWeight: '700', color: 'var(--on-surface)', marginBottom: '4px' }}>
                    {projName}
                  </div>
                  <p style={{ fontSize: '12.5px', color: 'var(--on-surface-variant)', margin: 0, lineHeight: '1.4' }}>
                    {projDesc}
                  </p>
                  {techStack.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                      {techStack.map((t, tIdx) => (
                        <span key={tIdx} style={{ fontSize: '11px', fontWeight: '700', padding: '2px 8px', borderRadius: '4px', background: 'rgba(101, 89, 123, 0.08)', color: 'var(--primary)' }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 6. Education Section ────────────────────────────────────────── */}
      {education.length > 0 && (
        <div style={{ background: 'rgba(255, 255, 255, 0.85)', border: '1.5px solid rgba(101, 89, 123, 0.12)', borderRadius: '16px', padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <GraduationCap size={16} color="var(--primary)" />
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--on-surface-variant)' }}>
              EDUCATION
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {education.map((edu, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: '6px' }}>
                <div>
                  <div style={{ fontSize: '13.5px', fontWeight: '700', color: 'var(--on-surface)' }}>
                    {edu.degree || 'Degree Program'}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--on-surface-variant)', marginTop: '2px' }}>
                    {edu.institution}
                  </div>
                </div>
                {edu.year && (
                  <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--primary)' }}>{edu.year}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 7. Extracted Skill Overlap & Evidence (Stage 2 Analysis) ────── */}
      {skillOverlap.length > 0 && (
        <div style={{ background: 'rgba(255, 255, 255, 0.85)', border: '1.5px solid rgba(101, 89, 123, 0.12)', borderRadius: '16px', padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Target size={16} color="var(--primary)" />
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--on-surface-variant)' }}>
              AI SKILL OVERLAP & PROOF EVIDENCE
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {skillOverlap.map((so, idx) => (
              <div key={idx} style={{ background: '#fbf9fe', border: '1px solid rgba(101, 89, 123, 0.1)', borderRadius: '12px', padding: '10px 14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--on-surface)' }}>{so.skill}</span>
                  <span style={{ fontSize: '11px', fontWeight: '700', padding: '2px 8px', borderRadius: '9999px', background: 'var(--primary-container)', color: 'var(--on-primary-container)' }}>
                    {so.proficiency_tier || 'Verified'}
                  </span>
                </div>
                {so.resume_evidence && (
                  <p style={{ fontSize: '12px', color: 'var(--on-surface-variant)', margin: 0, fontStyle: 'italic' }}>
                    "{so.resume_evidence}"
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 8. Strengths & Gaps (Stage 2 Analysis) ────────────────────── */}
      {(strengths.length > 0 || gaps.length > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
          {strengths.length > 0 && (
            <div style={{ background: '#f0fdf4', border: '1.5px solid #bbf7d0', borderRadius: '14px', padding: '14px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', color: '#15803d', fontWeight: '700', fontSize: '13px' }}>
                <CheckCircle size={16} />
                <span>Key Strengths</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12.5px', color: '#166534', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {strengths.map((str, idx) => (
                  <li key={idx}>{typeof str === 'object' ? str.description || str.missing_skill : str}</li>
                ))}
              </ul>
            </div>
          )}

          {gaps.length > 0 && (
            <div style={{ background: '#fff7ed', border: '1.5px solid #fed7aa', borderRadius: '14px', padding: '14px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', color: '#c2410c', fontWeight: '700', fontSize: '13px' }}>
                <AlertTriangle size={16} />
                <span>Areas for Probing / Focus</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12.5px', color: '#9a3412', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {gaps.map((gap, idx) => (
                  <li key={idx}>{typeof gap === 'object' ? (gap.missing_skill || gap.description) : gap}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

    </div>
  );
};

export default ResumeAnalysisTab;
