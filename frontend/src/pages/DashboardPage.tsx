import { useEffect } from 'react';
import { useAuth } from '../lib/auth';
import { useNavigate } from 'react-router-dom';

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      const role = user.role;
      if (role === 'owner') navigate('/dashboard/owner', { replace: true });
      else if (role === 'manager') navigate('/dashboard/manager', { replace: true });
      else navigate('/dashboard/employee', { replace: true });
    }
  }, [user, navigate]);

  return null;
}
