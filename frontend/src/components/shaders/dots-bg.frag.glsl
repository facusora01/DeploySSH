//Estas son mis notas sobre el shader, para ir aprendiendo

// Precisión de punto flotante. "mediump" = media precisión, suficiente para efectos visuales.
precision mediump float;

// "uniform" = variable que viene desde JavaScript y es igual para TODOS los pixels.
// u_resolution: ancho y alto del canvas en pixels.
// u_time: segundos transcurridos desde que arrancó el shader.
uniform vec2 u_resolution;
uniform float u_time;

// Color de los puntos en RGB normalizado (0.0–1.0). Es el azul-índigo del diseño.
const vec3 DOT_COLOR = vec3(0.227, 0.380, 0.773);

void main() {
  // gl_FragCoord es una variable built-in: la posición en pixels del pixel actual.
  // .xy extrae solo x e y (ignoramos z y w que no necesitamos).
  // fc va de (0,0) abajo-izquierda a (width, height) arriba-derecha.
  vec2 fc = gl_FragCoord.xy;

  // --- ZONA LATERAL: solo mostramos puntos en los costados, no sobre el contenido ---

  // Ancho del área de contenido: máximo 880px, o el ancho del canvas si es más angosto.
  float contentW = min(1280.0, u_resolution.x);

  // Borde izquierdo y derecho del bloque de contenido en pixels.
  // El contenido está centrado, así que el margen es (total - contenido) / 2.
  float cl = (u_resolution.x - contentW) * 0.5; //lado izquierdo
  float cr = cl + contentW; //lado derecho

  // Distancia horizontal del pixel actual al borde más cercano del contenido.
  // Si está dentro del contenido, ambos max() dan 0.0 → xDist = 0.
  // Si está a la izquierda: (cl - fc.x) > 0, el otro término es 0.
  // Si está a la derecha: (fc.x - cr) > 0, el otro término es 0.
  float xDist = max(0.0, cl - fc.x) + max(0.0, fc.x - cr);

  // smoothstep(edge0, edge1, x): interpolación suave entre 0 y 1.
  // Cuando xDist=0 (dentro del contenido) → devuelve 0.
  // Cuando xDist=150 (150px afuera del contenido) → devuelve 1.
  // Entre 0 y 150px hace una curva en S, no una transición abrupta.
  float sideFade = smoothstep(0.0, 150.0, xDist);

  // Optimización: si este pixel está muy cerca del contenido (casi invisible),
  // lo descartamos directamente para no hacer cálculos innecesarios.
  if (sideFade < 0.01) {
    gl_FragColor = vec4(0.0); // transparente total
    return;
  }

  // --- GRILLA DE PUNTOS ---

  // Tamaño de cada celda de la grilla en pixels.
  float cellSize = 15.0;

  // fract(x) devuelve la parte fraccionaria: fract(1.7) = 0.7, fract(3.0) = 0.0.
  // Al dividir la posición por cellSize y sacar fract, "reiniciamos" las coordenadas
  // cada 28 pixels → obtenemos coordenadas locales dentro de cada celda, en [0, 1).
  // Restamos 0.5 para centrar el origen en el medio de la celda → rango [-0.5, 0.5).

  // esto es un poco magia negra la verdad, al resetearlas le das a cada pixel una posición virtual de
  // mentira para que se hagan muchos círculos en vez de uno
  vec2 cellUV = fract(fc / cellSize) - 0.5;

  // length() calcula la distancia euclidiana desde el centro de la celda (0,0).
  // d = 0 en el centro exacto del punto, d = 0.5 en la esquina de la celda.
  float d = length(cellUV);

  // smoothstep con edge0 > edge1 → la función queda invertida.
  // Cuando d < 0.13 (cerca del centro): dotMask → 1.0 (pixel dentro del punto).
  // Cuando d > 0.19 (lejos del centro): dotMask → 0.0 (pixel fuera del punto).
  // El rango 0.13–0.19 es el borde suavizado del círculo (antialiasing manual).
  float dotMask = smoothstep(0.19, 0.13, d);

  // Si este pixel no pertenece a ningún punto, descartamos sin más cálculos.
  if (dotMask < 0.01) {
    gl_FragColor = vec4(0.0);
    return;
  }

  // --- ANIMACIÓN DE OLAS ---
  // Sumamos tres ondas sinusoidales con distintas frecuencias y velocidades.
  // Cada sin() oscila entre -1 y 1. Al combinarlos con pesos (0.5, 0.3, 0.2)
  // que suman 1.0, el resultado total también queda en el rango [-1, 1].
  float wave =
    sin(fc.x * 0.044 + u_time * 0.42) * sin(fc.y * 0.037 + u_time * 0.31) * 0.5 +
    sin(fc.x * 0.068 - fc.y * 0.052 + u_time * 0.58) * 0.3 +
    sin(fc.x * 0.027 + fc.y * 0.041 - u_time * 0.21) * 0.2;

  // wave está en [-1, 1]. Lo remapeamos a [0, 1] con (* 0.5 + 0.5).
  // Luego lo escalamos al rango [0.25, 1.0] para que ningún punto desaparezca del todo:
  //   mínimo 25% de brillo en los valles, máximo 100% en las crestas.
  float brightness = 0.25 + 0.75 * (wave * 0.5 + 0.5);

  // Alpha final = producto de los tres factores, multiplicado por 0.28 para suavidad global.
  // sideFade:  0 sobre el contenido → 1 en los costados       (dónde aparece)
  // dotMask:   0 fuera del punto   → 1 en el centro del punto (forma del punto)
  // brightness: 0.25–1.0 según las olas                       (brillo animado)
  // 0.55: opacidad máxima global — lo suficientemente alto para que el azul se vea
  float alpha = sideFade * dotMask * brightness*0.30 ;

  // Salida: color fijo + alpha calculado.
  // vec4(vec3, float) → (r, g, b, a)
  gl_FragColor = vec4(DOT_COLOR, alpha);
}
