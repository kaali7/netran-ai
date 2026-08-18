import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchReport } from '../services/reportService';

/**
 * Custom React hook for fetching and polling Stage 4 session evaluation reports.
 * 
 * @param {string} sessionId - The active interview session UUID.
 * @param {number} pollIntervalMs - Polling interval in ms (default: 3000ms).
 */
export const useReports = (sessionId, pollIntervalMs = 3000) => {
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState('evaluating');
  const [progressMessage, setProgressMessage] = useState('Initializing session evaluation...');
  const [isLoading, setIsLoading] = useState(true);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(null);

  const timerRef = useRef(null);

  const getReportData = useCallback(async () => {
    if (!sessionId) return;

    try {
      const data = await fetchReport(sessionId);
      
      if (data) {
        setStatus(data.status);
        if (data.progress_message) {
          setProgressMessage(data.progress_message);
        }
        
        if (data.evaluation_report) {
          setReport(data.evaluation_report);
        }

        if (data.status === 'completed' && data.evaluation_report) {
          setIsReady(true);
          setIsLoading(false);
          setError(null);
          // Stop polling once report is ready
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
          return;
        }

        // If error message in progress_message
        if (data.progress_message && data.progress_message.toLowerCase().includes('failed')) {
          setError(data.progress_message);
          setIsLoading(false);
        }
      }
    } catch (err) {
      console.error('Error fetching report:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch report');
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    setIsLoading(true);
    setIsReady(false);
    setError(null);

    // Initial fetch
    getReportData();

    // Setup polling interval
    timerRef.current = setInterval(() => {
      getReportData();
    }, pollIntervalMs);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [getReportData, pollIntervalMs]);

  return {
    report,
    status,
    progressMessage,
    isLoading,
    isReady,
    error,
    refetch: getReportData,
  };
};

export default useReports;
