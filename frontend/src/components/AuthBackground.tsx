import { useEffect, useRef } from "react"
import vertexShaderSource from "./shaders/quad.vert.glsl?raw"
import fragmentShaderSource from "./shaders/auth-bg.frag.glsl?raw"

function AuthBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext("webgl")
    if (!gl) {
      console.warn("WebGL no soportado")
      return
    }

    function compile(source: string, type: number) {
      const shader = gl!.createShader(type)!
      gl!.shaderSource(shader, source)
      gl!.compileShader(shader)
      if (!gl!.getShaderParameter(shader, gl!.COMPILE_STATUS)) {
        console.error(gl!.getShaderInfoLog(shader))
      }
      return shader
    }

    const vs = compile(vertexShaderSource, gl.VERTEX_SHADER)
    const fs = compile(fragmentShaderSource, gl.FRAGMENT_SHADER)
    const program = gl.createProgram()!
    gl.attachShader(program, vs)
    gl.attachShader(program, fs)
    gl.linkProgram(program)
    gl.useProgram(program)

    // Geometría: 2 triángulos que cubren toda la pantalla
    const buffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
      gl.STATIC_DRAW,
    )
    const positionLoc = gl.getAttribLocation(program, "a_position")
    gl.enableVertexAttribArray(positionLoc)
    gl.vertexAttribPointer(positionLoc, 2, gl.FLOAT, false, 0, 0)

    const resolutionLoc = gl.getUniformLocation(program, "u_resolution")
    const timeLoc = gl.getUniformLocation(program, "u_time")
    const mouseLoc = gl.getUniformLocation(program, "u_mousepos")

    // Posición del mouse en coords del canvas.
    // Lo inicializamos fuera del viewport para que el halo no aparezca al cargar.
    let mouseX = -9999
    let mouseY = -9999

    function handleMouseMove(e: MouseEvent) {
      if (!canvas) return
      const rect = canvas.getBoundingClientRect()
      const dpr = Math.min(window.devicePixelRatio, 2)
      mouseX = (e.clientX - rect.left) * dpr
      // WebGL tiene origen abajo-izq, el DOM arriba-izq → invertimos Y
      mouseY = (rect.bottom - e.clientY) * dpr
    }
    window.addEventListener("mousemove", handleMouseMove)

    function resize() {
      const dpr = Math.min(window.devicePixelRatio, 2)
      canvas!.width = canvas!.clientWidth * dpr
      canvas!.height = canvas!.clientHeight * dpr
      gl!.viewport(0, 0, canvas!.width, canvas!.height)
    }
    resize()
    window.addEventListener("resize", resize)

    let rafId = 0
    const start = performance.now()
    function render() {
      const elapsed = (performance.now() - start) / 1000
      gl!.uniform2f(resolutionLoc, canvas!.width, canvas!.height)
      gl!.uniform1f(timeLoc, elapsed)
      gl!.uniform4f(mouseLoc, mouseX, mouseY, 0, 0)
      gl!.drawArrays(gl!.TRIANGLES, 0, 6)
      rafId = requestAnimationFrame(render)
    }
    render()

    return () => {
      cancelAnimationFrame(rafId)
      window.removeEventListener("resize", resize)
      window.removeEventListener("mousemove", handleMouseMove)
      gl.deleteProgram(program)
      gl.deleteShader(vs)
      gl.deleteShader(fs)
      gl.deleteBuffer(buffer)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="auth-background"
      aria-hidden="true"
    />
  )
}

export default AuthBackground