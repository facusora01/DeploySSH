precision mediump float;

uniform vec2 u_resolution;
uniform float u_time;
uniform vec4 u_mousepos;

const vec3 BG     = vec3(0.961, 0.937, 0.902);
const vec3 ACCENT = vec3(0.427, 0.580, 0.773);
const vec3 SOFT   = vec3(0.796, 0.863, 0.922);

vec4 permute(vec4 x) {
  return mod(((x * 34.0) + 1.0) * x, 289.0);
}

vec2 fade(vec2 t) {
  return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
}

//ruido perlin copaido de interner
float perlin(vec2 P) {
  vec4 Pi = floor(P.xyxy) + vec4(0.0, 0.0, 1.0, 1.0);
  vec4 Pf = fract(P.xyxy) - vec4(0.0, 0.0, 1.0, 1.0);
  Pi = mod(Pi, 289.0);
  vec4 ix = Pi.xzxz;
  vec4 iy = Pi.yyww;
  vec4 fx = Pf.xzxz;
  vec4 fy = Pf.yyww;
  vec4 i = permute(permute(ix) + iy);
  vec4 gx = 2.0 * fract(i * 0.0243902439) - 1.0;
  vec4 gy = abs(gx) - 0.5;
  vec4 tx = floor(gx + 0.5);
  gx = gx - tx;
  vec2 g00 = vec2(gx.x, gy.x);
  vec2 g10 = vec2(gx.y, gy.y);
  vec2 g01 = vec2(gx.z, gy.z);
  vec2 g11 = vec2(gx.w, gy.w);
  vec4 norm = 1.79284291400159 - 0.85373472095314 *
    vec4(dot(g00, g00), dot(g01, g01), dot(g10, g10), dot(g11, g11));
  g00 *= norm.x; g01 *= norm.y; g10 *= norm.z; g11 *= norm.w;
  float n00 = dot(g00, vec2(fx.x, fy.x));
  float n10 = dot(g10, vec2(fx.y, fy.y));
  float n01 = dot(g01, vec2(fx.z, fy.z));
  float n11 = dot(g11, vec2(fx.w, fy.w));
  vec2 fade_xy = fade(Pf.xy);
  vec2 n_x = mix(vec2(n00, n01), vec2(n10, n11), fade_xy.x);
  return 2.3 * mix(n_x.x, n_x.y, fade_xy.y);
}

float pnoise(vec2 p) {
  return perlin(p) * 0.5 + 0.5;
}

void main() {
  // Coordenadas normalizadas 0-1, sin corrección de aspect ratio
  vec2 fragUv = gl_FragCoord.xy / u_resolution.xy;

  // Coordenadas con corrección de aspect ratio (para el ruido)
  vec2 uv = fragUv;
  uv.x *= u_resolution.x / u_resolution.y;

  // --- Ruido ---
  float t = u_time * 0.1;
  vec2 p = uv * 0.7 + vec2(t, sin(t * 0.7));

  float n = pnoise(p) * 0.5
          + pnoise(p * 2.0) * 0.25
          + pnoise(p * 4.0) * 0.125
          + pnoise(p * 8.0) * 0.0625;

  vec3 color = mix(BG, SOFT, smoothstep(0.3, 0.6, n));
  color = mix(color, ACCENT, smoothstep(0.65, 0.85, n) * 0.4);

  // --- Halo del mouse ---
  vec2 mouseUv = u_mousepos.xy / u_resolution.xy;

  // Compensación de aspect ratio: sin esto, el halo se vería ovalado.
  // Estiramos el delta-X para que la distancia sea isotrópica.
  vec2 delta = (fragUv - mouseUv) * vec2(u_resolution.x / u_resolution.y, 1.0);
  float dist = length(delta);

  // halo = 1.0 en el centro, 0.0 al borde del radio, el segundo arguemtno del ss es el diametro
  float halo = 1.0 - smoothstep(0.0, 0.55, dist);

  // Mezclamos el color hacia BG en la zona del halo
  color = mix(color, BG, halo * 0.85);

  gl_FragColor = vec4(color, 1.0);
}