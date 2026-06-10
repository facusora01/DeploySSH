import type { InputHTMLAttributes } from "react"

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  id: string 
}

function TextField({ label, id, ...inputProps }: TextFieldProps) {
  return (
    <div className="auth-form-group">
      <label htmlFor={id} className="auth-label">
        {label}
      </label>
      <input id={id} className="auth-input" {...inputProps} />
    </div>
  )
}

export default TextField