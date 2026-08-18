import { useState, useEffect } from 'react';
import api from '../services/api';
import { DEFAULT_DASHBOARD_DATA } from '../utils/constants';

export const useDashboard = () => {
  const [data, setData] = useState(DEFAULT_DASHBOARD_DATA);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchDashboardTelemetry = async () => {
      setLoading(true);
      try {
        // Attempt to fetch current authenticated user profile
        const userRes = await api.get('/auth/me');
        if (isMounted && userRes?.data) {
          const user = userRes.data;
          const name = user.email ? user.email.split('@')[0] : 'Candidate';
          const capitalizedName = name.charAt(0).toUpperCase() + name.slice(1);

          setData((prev) => ({
            ...prev,
            candidateName: capitalizedName,
            candidateFirstName: capitalizedName,
          }));
        }
      } catch (err) {
        // Graceful fallback to default mock dashboard state
        // console.info('Using local client dataset for dashboard view.');
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDashboardTelemetry();

    return () => {
      isMounted = false;
    };
  }, []);

  return { data, loading, error };
};

export default useDashboard;
