import React from 'react';

export const PageWrapper = ({ children, className = '', style = {} }) => {
  return (
    <div
      className={`page-wrapper-container ${className}`}
      style={{
        width: '100%',
        maxWidth: '100%',
        margin: '0 auto',
        padding: '0 36px 60px 36px',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export default PageWrapper;

