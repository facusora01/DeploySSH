import { useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import AuthBackground from "../components/AuthBackground"
import useFadeInOnScroll from "../hooks/useFadeInOnScroll"
import "./landing.css"

const BANNERS = [
  {
    eyebrow: "Para clientes",
    title: "Reservá en segundos, sin llamadas",
    description:
      "Elegí horario desde cualquier dispositivo. Confirmación inmediata y recordatorios automáticos por mail.",
  },
  {
    eyebrow: "Para profesionales",
    title: "Una agenda que se ordena sola",
    description:
      "Definí tus horarios, duraciones y bloqueos. Appointa se encarga del resto: avisos, reprogramaciones y cancelaciones.",
  },
  {
    eyebrow: "Sin fricciones",
    title: "Recordatorios automáticos",
    description:
      "Te avisamos antes de cada turno por mail. Menos ausencias, menos llamadas, más turnos cumplidos.",
  },
  {
    eyebrow: "Datos en un lugar",
    title: "Tu historial siempre a mano",
    description:
      "Próximos turnos, pasados y notas — todo en tu perfil. Vos y tu profesional ven lo mismo, en tiempo real.",
  },
]

type BannerData = (typeof BANNERS)[number]

function Banner({ index, eyebrow, title, description }: BannerData & { index: number }) {
  const [ref, visible] = useFadeInOnScroll<HTMLElement>()
  const isReversed = index % 2 === 1

  return (
    <article
      ref={ref}
      className={`landing-banner ${isReversed ? "is-reversed" : ""} ${visible ? "is-visible" : ""}`}
    >
      <div className="landing-banner-text">
        <span className="landing-banner-eyebrow">{eyebrow}</span>
        <h2 className="landing-banner-title">{title}</h2>
        <p className="landing-banner-description">{description}</p>
      </div>
      <div className="landing-banner-visual" aria-hidden="true" />
    </article>
  )
}

function Landing() {
  const navigate = useNavigate()
  const { user, loading } = useAuth()
  const [ctaRef, ctaVisible] = useFadeInOnScroll<HTMLElement>()

  useEffect(() => {
    if (!loading && user) navigate("/turnos", { replace: true })
  }, [loading, user, navigate])

  if (loading || user) return null

  return (
    <div className="landing-page">
      {/* Wrapper propio: aisla el canvas del CSS de auth-background */}
      <div className="landing-background" aria-hidden="true">
        <AuthBackground />
      </div>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-hero-content">
          <h1 className="landing-logo">APPOINTA</h1>
          <p className="landing-tagline">Gestioná turnos en minutos</p>
          <div className="landing-actions">
            <Link to="/login" className="landing-button landing-button--primary">
              Iniciar sesión
            </Link>
            <Link to="/register" className="landing-button landing-button--secondary">
              Crear cuenta
            </Link>
          </div>
        </div>
      </section>

      {/* Banners alternados con fade-in al scrollear */}
      <section className="landing-banners">
        {BANNERS.map((banner, i) => (
          <Banner key={banner.title} index={i} {...banner} />
        ))}
      </section>

      {/* CTA final con login/registro */}
      <section
        ref={ctaRef}
        className={`landing-cta ${ctaVisible ? "is-visible" : ""}`}
      >
        <h2 className="landing-cta-title">Empezá a usar Appointa hoy</h2>
        <p className="landing-cta-subtitle">
          Gratis para arrancar. Sin tarjeta, sin instalaciones.
        </p>
        <div className="landing-actions">
          <Link to="/register" className="landing-button landing-button--primary">
            Crear cuenta
          </Link>
          <Link to="/login" className="landing-button landing-button--secondary">
            Iniciar sesión
          </Link>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <p className="landing-footer-text">© {new Date().getFullYear()} Appointa</p>
        </div>
      </footer>
    </div>
  )
}

export default Landing