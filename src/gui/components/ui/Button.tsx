import { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline"
  size?: "sm" | "md" | "lg"
}

export const Button = ({ 
  children, 
  variant = "primary",
  size = "md",
  className,
  ...props 
}: ButtonProps) => {
  return (
    <button 
      className={`btn btn-${variant} btn-${size} ${className || ""}`}
      {...props}
    >
      {children}
    </button>
  )
}