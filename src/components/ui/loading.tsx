interface LoadingProps {
  size?: "sm" | "md" | "lg";  // Define allowed sizes
}

export default function Loading({ size = "md" }: LoadingProps) {
  const sizeClass = size === "sm" ? "h-4 w-4" : size === "lg" ? "h-10 w-10" : "h-6 w-6";

  return (
    <div className={`animate-spin border-t-2 border-white rounded-full ${sizeClass}`} />
  );
}
