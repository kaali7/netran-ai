import React from 'react';

export const Badge = ({
  children,
  variant = 'completed', // 'completed' | 'pending' | 'focus'
  className = '',
}) => {
  let badgeStyle = 'badge-completed';
  if (variant === 'pending') badgeStyle = 'badge-pending';
  if (variant === 'focus') badgeStyle = 'badge-focus';

  return (
    <span className={`badge-chip ${badgeStyle} ${className}`}>
      {children}
    </span>
  );
};

export default Badge;
