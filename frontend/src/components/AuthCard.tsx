import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import AuthBackground from "./AuthBackground"

interface AuthCardProps {
  title: string
  subtitle: string
  children: ReactNode
  footerText: string
  footerLinkLabel: string
  footerLinkTo: string
}

function AuthCard({
  title,
  subtitle,
  children,
  footerText,
  footerLinkLabel,
  footerLinkTo,
}: AuthCardProps) {
  return (
    <div className="auth-page">
      <AuthBackground />
      <div className="auth-container">
        <section className="auth-card">
          <header className="auth-header">
            <Link to="/" className="auth-logo">APPOINTA</Link>
            <h1 className="auth-title">{title}</h1>
            <p className="auth-subtitle">{subtitle}</p>
          </header>

          {children}

          <footer className="auth-footer">
            <p className="auth-footer-text">
              {footerText}{" "}
              <Link to={footerLinkTo} className="auth-footer-link">
                {footerLinkLabel}
              </Link>
            </p>
          </footer>
        </section>
      </div>
    </div>
  )
}

export default AuthCard