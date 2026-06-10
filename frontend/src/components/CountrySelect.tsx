import { useState, useRef, useEffect } from "react"

const COUNTRIES = [
  { code: "+54", flag: "🇦🇷", name: "Argentina" },
  { code: "+56", flag: "🇨🇱", name: "Chile" },
  { code: "+55", flag: "🇧🇷", name: "Brasil" },
  { code: "+598", flag: "🇺🇾", name: "Uruguay" },
  { code: "+593", flag: "🇪🇨", name: "Ecuador" },
  { code: "+57", flag: "🇨🇴", name: "Colombia" },
  { code: "+51", flag: "🇵🇪", name: "Perú" },
  { code: "+52", flag: "🇲🇽", name: "México" },
  { code: "+34", flag: "🇪🇸", name: "España" },
  { code: "+1", flag: "🇺🇸", name: "USA" },
]

export function CountrySelect({ value, onChange }: { value: string, onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState("")
  const ref = useRef<HTMLDivElement>(null)

  const selected = COUNTRIES.find(c => c.code === value) || COUNTRIES[0]

  const filtered = COUNTRIES.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) || 
    c.code.includes(search)
  )

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <div ref={ref} style={{ position: "relative", width: "120px" }}>
      <button
        type="button"
        onClick={() => {
          setOpen(!open)
          setSearch("")
        }}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          padding: "0.75rem",
          borderRadius: "4px",
          border: "1px solid #ccc",
          backgroundColor: "#fff",
          color: "#000",
          cursor: "pointer",
        }}
      >
        <span>{selected.flag} {selected.code}</span>
        <span style={{ fontSize: "0.8em" }}>▼</span>
      </button>

      {open && (
        <div style={{
          position: "absolute",
          top: "100%",
          left: 0,
          width: "200px",
          maxHeight: "250px",
          backgroundColor: "#fff",
          border: "1px solid #ccc",
          borderRadius: "4px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          zIndex: 10,
          display: "flex",
          flexDirection: "column",
          marginTop: "4px",
          overflow: "hidden"
        }}>
          <input
            type="text"
            placeholder="Buscar país o código..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              padding: "0.5rem",
              border: "none",
              borderBottom: "1px solid #eee",
              outline: "none",
              color: "#000"
            }}
            autoFocus
          />
          <div style={{ overflowY: "auto", flex: 1 }}>
            {filtered.map(c => (
              <button
                key={c.code}
                type="button"
                onClick={() => {
                  onChange(c.code)
                  setOpen(false)
                }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  width: "100%",
                  padding: "0.5rem",
                  border: "none",
                  backgroundColor: c.code === value ? "#f0f0f0" : "transparent",
                  textAlign: "left",
                  cursor: "pointer",
                  color: "#000"
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#f9f9f9"}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = c.code === value ? "#f0f0f0" : "transparent"}
              >
                <span>{c.flag}</span>
                <span>{c.name}</span>
                <span style={{ color: "#666", marginLeft: "auto" }}>{c.code}</span>
              </button>
            ))}
            {filtered.length === 0 && (
              <div style={{ padding: "0.5rem", color: "#666", textAlign: "center" }}>
                Sin resultados
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
