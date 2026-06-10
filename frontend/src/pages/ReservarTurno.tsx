import { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import Icon from "../components/Icon";
import { buildGoogleCalendarUrl } from "../utils/googleCalendar";
import "./booking.css";

interface Slot {
  start_time: string;
  end_time: string;
  max_slots: number;
  current_occupancy: number;
  is_available: boolean;
}

interface ServiceAvailability {
  service_id: string;
  service_name: string;
  profesional_public_link: string;
  availability: Slot[];
  deposit_active?: boolean;
  deposit_amount?: string | null;
  deposit_required?: boolean;
}

interface FormField {
  id: string;
  field_name: string;
  is_required: boolean;
  order: number;
  field_type: "text" | "yes_no" | "select";
  options: string[];
}

interface ClientProfileResponse {
  full_name?: string;
  phone?: string | null;
}

function ReservarTurno() {
  const { servicio } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successData, setSuccessData] = useState<any | null>(null);
  const [depositPending, setDepositPending] = useState<any | null>(null);
  const [depositAction, setDepositAction] = useState<"pay" | "skip" | null>(
    null,
  );

  // Availability state
  const [availability, setAvailability] = useState<ServiceAvailability | null>(
    null,
  );

  // Date and slot selection states
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);

  // Custom form fields state
  const [formFields, setFormFields] = useState<FormField[]>([]);
  const [formAnswers, setFormAnswers] = useState<Record<string, string>>({});

  // Form states (prefilled with user profile)
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");

  // Pre-fill from user context when available
  useEffect(() => {
    if (user) {
      if (user.full_name && !fullName) setFullName(user.full_name);
      if (user.phone && !phone) setPhone(user.phone);
    }
  }, [user]);

  // Fetch availability and client profile
  useEffect(() => {
    async function loadData() {
      try {
        if (!servicio) return;

        // 1. Fetch service availability (includes profesional_public_link)
        const availData = await api.get<ServiceAvailability>(
          `/api/v1/availability/${servicio}`,
        );
        setAvailability(availData);

        // 2. Fetch professional's custom form fields (public endpoint, no auth needed)
        try {
          const fields = await api.get<FormField[]>(
            `/api/v1/form-fields/public/${availData.profesional_public_link}`,
          );
          setFormFields(fields);
        } catch {
          // If fetch fails, continue without custom fields
        }

        // 3. Fetch client profile info to pre-fill the form
        try {
          const clientData = await api.get<ClientProfileResponse>(
            "/api/v1/clientes/me",
            true,
          );
          if (clientData) {
            if (clientData.full_name) setFullName(clientData.full_name);
            if (clientData.phone) setPhone(clientData.phone || "");
          }
        } catch {
          // Ignore error: client profile might not be created yet, which is fine
        }
      } catch (err: any) {
        setError(
          err.response?.data?.detail ||
            "No se pudo cargar la disponibilidad del servicio.",
        );
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [servicio]);

  // Group slots by date
  const slotsByDate = useMemo(() => {
    const grouped: Record<string, Slot[]> = {};
    if (!availability?.availability) return grouped;

    for (const slot of availability.availability) {
      const dateStr = slot.start_time.split("T")[0];
      if (!grouped[dateStr]) {
        grouped[dateStr] = [];
      }
      grouped[dateStr].push(slot);
    }

    // Sort dates chronologically
    const sortedGrouped: Record<string, Slot[]> = {};
    Object.keys(grouped)
      .sort()
      .forEach((key) => {
        sortedGrouped[key] = grouped[key].sort((a, b) =>
          a.start_time.localeCompare(b.start_time),
        );
      });

    return sortedGrouped;
  }, [availability]);

  // Extract all unique dates
  const dates = useMemo(() => Object.keys(slotsByDate), [slotsByDate]);

  // Set default selected date once dates load
  useEffect(() => {
    if (dates.length > 0 && !selectedDate) {
      setSelectedDate(dates[0]);
    }
  }, [dates, selectedDate]);

  // Helper to format date button label
  function formatDateBtn(dateStr: string) {
    const [year, month, day] = dateStr.split("-").map(Number);
    const d = new Date(year, month - 1, day);
    const weekday = d.toLocaleDateString("es-AR", { weekday: "short" });
    const monthName = d.toLocaleDateString("es-AR", { month: "short" });
    return {
      weekday: weekday.replace(".", ""),
      day: day,
      month: monthName.replace(".", ""),
    };
  }

  // format time helper
  function formatTime(isoStr: string) {
    const timePart = isoStr.split("T")[1];
    return timePart.slice(0, 5);
  }

  async function handleBook(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedSlot) {
      setError("Por favor, selecciona un horario para tu turno.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const payload = {
        service_id: servicio,
        start_time: selectedSlot.start_time,
        full_name: fullName || null,
        phone: phone || null,
        form_responses: Object.entries(formAnswers)
          .filter(([, answer]) => answer.trim() !== "")
          .map(([field_id, answer]) => ({ field_id, answer: answer.trim() })),
      };

      const response = await api.post<any>(
        "/api/v1/appointments",
        payload,
        true,
      );

      // Check if service has deposit and appointment is pending deposit payment
      if (
        availability?.deposit_active &&
        response.deposit_status === "PENDING"
      ) {
        setDepositPending({
          ...response,
          service_name: availability?.service_name,
          date: selectedSlot.start_time.split("T")[0],
          time: formatTime(selectedSlot.start_time),
        });
      } else {
        setSuccessData({
          ...response,
          service_name: availability?.service_name,
          date: selectedSlot.start_time.split("T")[0],
          time: formatTime(selectedSlot.start_time),
        });
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          "No se pudo realizar la reserva del turno.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePayDeposit() {
    if (!depositPending) return;
    setDepositAction("pay");
    setError("");

    try {
      const response = await api.patch<any>(
        `/api/v1/appointments/${depositPending.id}/pay-deposit`,
        {},
        true,
      );
      setDepositPending(null);
      setSuccessData({
        ...response,
        service_name: depositPending.service_name,
        date: depositPending.date,
        time: depositPending.time,
      });
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "No se pudo procesar el pago de la seña.",
      );
    } finally {
      setDepositAction(null);
    }
  }

  async function handleSkipDeposit() {
    if (!depositPending) return;
    setDepositAction("skip");
    setError("");

    try {
      const response = await api.patch<any>(
        `/api/v1/appointments/${depositPending.id}/confirm-without-deposit`,
        {},
        true,
      );
      setDepositPending(null);
      setSuccessData({
        ...response,
        service_name: depositPending.service_name,
        date: depositPending.date,
        time: depositPending.time,
      });
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "No se pudo confirmar la reserva.",
      );
    } finally {
      setDepositAction(null);
    }
  }

  if (loading) {
    return (
      <div className="booking-page">
        <div
          className="booking-container"
          style={{ textAlign: "center", padding: "2rem" }}
        >
          Cargando disponibilidad del servicio...
        </div>
      </div>
    );
  }

  if (depositPending) {
    const depositAmount = availability?.deposit_amount;
    const depositRequired = availability?.deposit_required;

    return (
      <div className="booking-page">
        <div className="booking-success-card">
          <div
            className="booking-success-icon"
            style={{ color: "var(--warning, #f59e0b)" }}
          >
            <Icon name="lock" size={28} />
          </div>
          <h1 className="perfil-title" style={{ margin: 0 }}>
            {depositRequired
              ? "Pago de Seña Requerido"
              : "Confirmar Pago de Seña"}
          </h1>
          <p className="perfil-subtitle">
            {depositRequired
              ? "Esta reserva requiere el pago de una seña para confirmarse."
              : "Puedes pagar una seña (opcional) o continuar sin hacerlo."}
          </p>

          <div className="booking-success-details">
            <div className="booking-success-detail-row">
              <span className="booking-success-label">Servicio:</span>
              <span className="booking-success-value">
                {depositPending.service_name}
              </span>
            </div>
            <div className="booking-success-detail-row">
              <span className="booking-success-label">Fecha:</span>
              <span className="booking-success-value">
                {new Date(depositPending.date + "T00:00:00").toLocaleDateString(
                  "es-AR",
                  {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  },
                )}
              </span>
            </div>
            <div className="booking-success-detail-row">
              <span className="booking-success-label">Horario:</span>
              <span className="booking-success-value">
                {depositPending.time} hs
              </span>
            </div>
            <div
              className="booking-success-detail-row"
              style={{
                borderTop: "1px solid var(--border)",
                paddingTop: "12px",
                marginTop: "12px",
              }}
            >
              <span
                className="booking-success-label"
                style={{ fontWeight: "bold" }}
              >
                Monto de Seña:
              </span>
              <span
                className="booking-success-value"
                style={{ fontWeight: "bold", color: "var(--primary, #3b82f6)" }}
              >
                $
                {Number(depositAmount || 0).toLocaleString("es-AR", {
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          </div>

          {error && (
            <div
              style={{
                background: "var(--error-bg)",
                color: "var(--error)",
                padding: "12px",
                borderRadius: "var(--radius)",
                fontSize: "14px",
                marginTop: "12px",
              }}
            >
              {error}
            </div>
          )}

          <div
            style={{
              display: "flex",
              gap: "12px",
              marginTop: "24px",
              flexWrap: "wrap",
              justifyContent: "center",
            }}
          >
            <button
              className="perfil-edit-button"
              onClick={handlePayDeposit}
              disabled={depositAction !== null}
              style={{
                padding: "12px 32px",
                fontSize: "15px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                opacity: depositAction === "pay" ? 0.7 : 1,
              }}
            >
              {depositAction === "pay" && (
                <span className="spinner" style={{ marginRight: "4px" }}>
                  ⟳
                </span>
              )}
              {depositAction === "pay" ? "Procesando..." : "Pagar Seña"}
            </button>
            {!depositRequired && (
              <button
                className="perfil-edit-button"
                onClick={handleSkipDeposit}
                disabled={depositAction !== null}
                style={{
                  padding: "12px 32px",
                  fontSize: "15px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  background: "var(--border)",
                  color: "var(--text-h)",
                  opacity: depositAction === "skip" ? 0.7 : 1,
                }}
              >
                {depositAction === "skip" && (
                  <span className="spinner" style={{ marginRight: "4px" }}>
                    ⟳
                  </span>
                )}
                {depositAction === "skip"
                  ? "Procesando..."
                  : "Continuar sin Pagar"}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (successData) {
    return (
      <div className="booking-page">
        <div className="booking-success-card">
          <div className="booking-success-icon">
            <Icon name="check" size={28} />
          </div>
          <h1 className="perfil-title" style={{ margin: 0 }}>
            ¡Reserva Confirmada!
          </h1>
          <p className="perfil-subtitle">
            Tu turno ha sido reservado correctamente.
          </p>

          <div className="booking-success-details">
            <div className="booking-success-detail-row">
              <span className="booking-success-label">Servicio:</span>
              <span className="booking-success-value">
                {successData.service_name}
              </span>
            </div>
            <div className="booking-success-detail-row">
              <span className="booking-success-label">Fecha:</span>
              <span className="booking-success-value">
                {new Date(successData.date + "T00:00:00").toLocaleDateString(
                  "es-AR",
                  {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  },
                )}
              </span>
            </div>
            <div className="booking-success-detail-row">
              <span className="booking-success-label">Horario:</span>
              <span className="booking-success-value">
                {successData.time} hs
              </span>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              gap: "12px",
              marginTop: "12px",
              flexWrap: "wrap",
            }}
          >
            <a
              href={buildGoogleCalendarUrl({
                title: `Turno: ${successData.service_name} con ${successData.profesional_name}`,
                startTime: successData.start_time,
                endTime: successData.end_time,
                details: successData.notes || undefined,
              })}
              target="_blank"
              rel="noopener noreferrer"
              className="perfil-edit-button"
              style={{
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <Icon name="calendar" size={16} />
              Agregar a Google Calendar
            </a>
            <button
              className="perfil-edit-button"
              onClick={() => navigate("/turnos")}
            >
              Ver mis Turnos
            </button>
            <button
              className="perfil-edit-button"
              style={{ background: "var(--border)", color: "var(--text-h)" }}
              onClick={() => navigate(-1)}
            >
              Volver
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="booking-page">
      <div className="booking-container">
        <header className="perfil-header">
          <div>
            <h1 className="perfil-title">Reservar Turno</h1>
            <p className="perfil-subtitle">
              Servicio: {availability?.service_name}
            </p>
          </div>
          <button
            type="button"
            className="perfil-edit-button"
            style={{ background: "var(--border)", color: "var(--text-h)" }}
            onClick={() => navigate(-1)}
          >
            Volver
          </button>
        </header>

        {error && (
          <div
            style={{
              background: "var(--error-bg)",
              color: "var(--error)",
              padding: "12px",
              borderRadius: "var(--radius)",
              fontSize: "14px",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleBook} className="booking-card">
          {/* STEP 1: SELECT DATE */}
          <div>
            <h2
              className="perfil-section-title"
              style={{ fontSize: "15px", marginBottom: "10px" }}
            >
              1. Selecciona una Fecha
            </h2>
            {dates.length === 0 ? (
              <p
                style={{
                  color: "var(--muted)",
                  fontSize: "14px",
                  fontStyle: "italic",
                }}
              >
                El profesional no tiene horarios disponibles configurados en su
                agenda.
              </p>
            ) : (
              <div className="booking-dates-scroll">
                {dates.map((dateStr) => {
                  const parts = formatDateBtn(dateStr);
                  const isSelected = selectedDate === dateStr;
                  return (
                    <div
                      key={dateStr}
                      className={`booking-date-btn ${isSelected ? "is-selected" : ""}`}
                      onClick={() => {
                        setSelectedDate(dateStr);
                        setSelectedSlot(null);
                      }}
                    >
                      <span className="booking-date-day-name">
                        {parts.weekday}
                      </span>
                      <span className="booking-date-day-num">{parts.day}</span>
                      <span className="booking-date-month">{parts.month}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* STEP 2: SELECT TIME SLOT */}
          {selectedDate && slotsByDate[selectedDate] && (
            <div>
              <h2
                className="perfil-section-title"
                style={{ fontSize: "15px", marginBottom: "10px" }}
              >
                2. Selecciona un Horario
              </h2>
              <div className="booking-slots-grid">
                {slotsByDate[selectedDate].map((slot, index) => {
                  const isSelected =
                    selectedSlot?.start_time === slot.start_time;
                  const isFull = !slot.is_available;

                  return (
                    <button
                      key={index}
                      type="button"
                      disabled={isFull}
                      className={`booking-slot-btn ${isSelected ? "is-selected" : ""} ${isFull ? "is-disabled" : ""}`}
                      onClick={() => setSelectedSlot(slot)}
                    >
                      <span className="booking-slot-time">
                        {formatTime(slot.start_time)}
                      </span>
                      {slot.max_slots > 1 && (
                        <span
                          className="booking-slot-occupancy"
                          style={{ fontSize: "10px", marginTop: "2px" }}
                        >
                          {isFull
                            ? "Lleno"
                            : `Cupos: ${slot.current_occupancy}/${slot.max_slots}`}
                        </span>
                      )}
                      {slot.max_slots === 1 && isFull && (
                        <span
                          className="booking-slot-occupancy"
                          style={{
                            color: "var(--error)",
                            fontSize: "10px",
                            marginTop: "2px",
                          }}
                        >
                          Ocupado
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 3 (OPTIONAL): CUSTOM FORM FIELDS */}
          {formFields.length > 0 && (
            <div
              style={{
                borderTop: "1px solid var(--border)",
                paddingTop: "20px",
                marginTop: "10px",
              }}
            >
              <h2
                className="perfil-section-title"
                style={{ fontSize: "15px", marginBottom: "12px" }}
              >
                3. Completá el formulario
              </h2>
              <div className="booking-form-grid">
                {formFields.map((field) => (
                  <div key={field.id} className="booking-form-group">
                    <label>
                      {field.field_name}
                      {field.is_required ? " *" : " (Opcional)"}
                    </label>

                    {field.field_type === "text" && (
                      <input
                        type="text"
                        required={field.is_required}
                        placeholder={field.field_name}
                        value={formAnswers[field.id] ?? ""}
                        onChange={(e) =>
                          setFormAnswers((prev) => ({
                            ...prev,
                            [field.id]: e.target.value,
                          }))
                        }
                      />
                    )}

                    {field.field_type === "yes_no" && (
                      <div className="booking-radio-group">
                        {["Sí", "No"].map((opt) => (
                          <label key={opt} className="booking-radio-label">
                            <input
                              type="radio"
                              name={field.id}
                              value={opt}
                              required={field.is_required}
                              checked={formAnswers[field.id] === opt}
                              onChange={() =>
                                setFormAnswers((prev) => ({
                                  ...prev,
                                  [field.id]: opt,
                                }))
                              }
                            />
                            {opt}
                          </label>
                        ))}
                      </div>
                    )}

                    {field.field_type === "select" && (
                      <select
                        required={field.is_required}
                        value={formAnswers[field.id] ?? ""}
                        onChange={(e) =>
                          setFormAnswers((prev) => ({
                            ...prev,
                            [field.id]: e.target.value,
                          }))
                        }
                      >
                        <option value="">Seleccioná una opción</option>
                        {field.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 3 or 4: ACCOUNT & PERSONAL INFO FORM */}
          <div
            style={{
              borderTop: "1px solid var(--border)",
              paddingTop: "20px",
              marginTop: "10px",
            }}
          >
            <h2
              className="perfil-section-title"
              style={{ fontSize: "15px", marginBottom: "12px" }}
            >
              {formFields.length > 0 ? "4." : "3."} Completa los Datos de tu
              Cuenta
            </h2>
            <div className="booking-form-grid">
              <div className="booking-form-group">
                <label>Nombre y Apellido *</label>
                <input
                  type="text"
                  required
                  placeholder="Tu nombre completo"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>

              <div className="booking-form-group">
                <label>Contacto</label>
                <input
                  type="text"
                  placeholder="Teléfono o email"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginTop: "10px",
            }}
          >
            <button
              type="submit"
              disabled={submitting || !selectedSlot}
              className="perfil-edit-button"
              style={{
                padding: "12px 32px",
                fontSize: "15px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                opacity: !selectedSlot ? 0.6 : 1,
                cursor: !selectedSlot ? "not-allowed" : "pointer",
              }}
            >
              {submitting ? "Reservando..." : "Reservar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ReservarTurno;
