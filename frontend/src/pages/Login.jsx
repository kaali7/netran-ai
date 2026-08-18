import React from 'react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

export const Login = () => {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <Card style={{ maxWidth: '420px', width: '100%', textAlign: 'center' }}>
        <h1 className="text-headline-xl">Netran AI</h1>
        <p className="text-body-md" style={{ margin: '8px 0 24px 0' }}>
          Sign in to access your interview preparation dashboard.
        </p>
        <Button variant="primary" style={{ width: '100%' }}>
          Continue with Candidate Account
        </Button>
      </Card>
    </div>
  );
};

export default Login;
