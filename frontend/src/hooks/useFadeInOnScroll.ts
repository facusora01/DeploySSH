import { useCallback, useRef, useState } from "react"

/**
 * Devuelve [refCallback, visible]. Aplicá el callback al ref del
 * elemento a animar y usá `visible` para alternar `.is-visible`.
 *
 * Usa callback ref (no useRef + useEffect) para que el setup del
 * observer corra cuando el nodo entra al DOM, no cuando el componente
 * monta. Esto importa cuando el componente padre tiene un early return
 * en su primer render (ej. Landing esperando a que cargue el auth).
 */
function useFadeInOnScroll<T extends HTMLElement>(): [
  (node: T | null) => void,
  boolean,
] {
  const [visible, setVisible] = useState(false)
  const observerRef = useRef<IntersectionObserver | null>(null)

  const refCallback = useCallback((node: T | null) => {
    // Si había un observer previo (por re-mount), lo limpiamos.
    if (observerRef.current) {
      observerRef.current.disconnect()
      observerRef.current = null
    }

    // node = null cuando el elemento se desmonta.
    if (!node) return

    // Fallback si IntersectionObserver no está disponible.
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true)
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      {
        threshold: 0.1,
        rootMargin: "0px 0px -80px 0px",
      },
    )

    observer.observe(node)
    observerRef.current = observer
  }, [])

  return [refCallback, visible]
}

export default useFadeInOnScroll