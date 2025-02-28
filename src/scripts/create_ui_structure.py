import os
from pathlib import Path
import logging
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UIStructureCreator:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.ui_dir = self.root_dir / "src/gui/components/ui"
        self.auth_dir = self.root_dir / "src/gui/auth"

    def create_component(self, name: str, content: str) -> None:
        """Create a UI component file"""
        file_path = self.ui_dir / f"{name}.tsx"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Created component: {file_path}")

    def create_page(self, path: str, content: str) -> None:
        """Create a page file"""
        file_path = self.auth_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Created page: {file_path}")

    def create_structure(self) -> None:
        """Create the UI structure"""
        # Button component
        button_content = """
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
""".strip()

        # Card component
        card_content = """
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
""".strip()

        # Auth pages
        login_content = """
export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6">Login</h1>
        {/* Add login form */}
      </div>
    </div>
  )
}
""".strip()

        forgot_password_content = """
export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6">Reset Password</h1>
        {/* Add password reset form */}
      </div>
    </div>
  )
}
""".strip()

        # Create components
        self.create_component("Button", button_content)
        self.create_component("Card", card_content)

        # Create pages
        self.create_page("login/page.tsx", login_content)
        self.create_page("forgot-password/page.tsx", forgot_password_content)

def main():
    try:
        creator = UIStructureCreator(".")
        creator.create_structure()
        logger.info("UI structure created successfully!")
    except Exception as e:
        logger.error(f"Failed to create UI structure: {e}")

if __name__ == "__main__":
    main()
