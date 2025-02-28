import React from 'react';

interface AlertProps {
  children?: React.ReactNode;
  variant?: "success" | "warning" | "error";
  className?: string;
}

const Alert: React.FC<AlertProps> = ({ children, variant = "success", className = "" }) => {
  const variantClasses = {
    success: "bg-green-100 text-green-700",
    warning: "bg-yellow-100 text-yellow-700",
    error: "bg-red-100 text-red-700",
  };

  return (
    <div className={`p-4 rounded ${variantClasses[variant]} ${className}`}>
      <h1>Alert Component</h1>
      <p>This is a placeholder for the Alert component.</p>
      {children}
    </div>
  );
};

export default Alert; 