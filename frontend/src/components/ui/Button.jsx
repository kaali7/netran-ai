import React from 'react';

export const Button = ({
  children,
  variant = 'primary', // 'primary' | 'ghost' | 'secondary-action' | 'compact'
  icon: Icon,
  className = '',
  disabled = false,
  onClick,
  type = 'button',
  ...props
}) => {
  let variantClass = 'btn-primary';
  if (variant === 'ghost') variantClass = 'btn-ghost';
  if (variant === 'secondary-action') variantClass = 'btn-secondary-action';
  if (variant === 'compact') variantClass = 'btn-ghost btn-compact';

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`btn ${variantClass} ${className}`}
      {...props}
    >
      {Icon && <Icon size={18} strokeWidth={2.2} />}
      <span>{children}</span>
    </button>
  );
};

export default Button;
