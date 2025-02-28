interface CardProps {
  children: React.ReactNode
  className?: string
}

export const Card = ({ children, className, ...props }: CardProps) => {
  return (
    <div 
      className={`card p-4 bg-white shadow rounded-lg ${className || ""}`} 
      {...props}
    >
      {children}
    </div>
  )
}