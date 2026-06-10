const fs = require("fs");
const path = require("path");

const BASE = path.join(__dirname, ".wwhatsapp_auth");
const SESSION_DIR = path.join(BASE, "session-appointa");
const BACKUP_DIR = path.join(BASE, "session-backup");

const LOCKS = ["SingletonLock", "SingletonSocket", "SingletonCookie"];
const CACHE_DIRS = new Set([
  "Cache", "Code Cache", "GPUCache", "ShaderCache", "GrShaderCache",
  "DawnCache", "DawnGraphiteCache", "DawnWebGPUCache", "component_crx_cache",
]);

// True si el perfil tiene una sesión de WhatsApp (IndexedDB presente).
function rutaTieneSesion(dir) {
  return fs.existsSync(path.join(dir, "Default", "IndexedDB"));
}

// Borra los locks de singleton de Chromium del perfil vivo.
function limpiarLocks() {
  for (const f of LOCKS) {
    try {
      fs.rmSync(path.join(SESSION_DIR, f), { force: true });
    } catch (e) {
      console.warn(`⚠️ No pude limpiar lock ${f}:`, e.message);
    }
  }
}

// Copia un perfil de Chromium salteando locks, cachés y archivos que desaparecen.
function copiarPerfil(src, dest) {
  let entries;
  try {
    entries = fs.readdirSync(src, { withFileTypes: true });
  } catch (e) {
    if (e.code === "ENOENT") return;
    throw e;
  }

  fs.mkdirSync(dest, { recursive: true });

  for (const ent of entries) {
    const base = ent.name;
    if (LOCKS.includes(base) || CACHE_DIRS.has(base)) continue;

    const s = path.join(src, base);
    const d = path.join(dest, base);
    try {
      if (ent.isDirectory()) {
        copiarPerfil(s, d);
      } else if (ent.isFile()) {
        fs.copyFileSync(s, d);
      }
    } catch (e) {
      if (e.code === "ENOENT" || e.code === "EBUSY") continue;
      throw e;
    }
  }
}

// Respalda la sesión viva al backup con swap atómico vía carpeta .tmp.
function respaldarSesion() {
  try {
    if (!rutaTieneSesion(SESSION_DIR)) return;
    const tmp = BACKUP_DIR + ".tmp";
    fs.rmSync(tmp, { recursive: true, force: true });
    copiarPerfil(SESSION_DIR, tmp);
    fs.rmSync(BACKUP_DIR, { recursive: true, force: true });
    fs.renameSync(tmp, BACKUP_DIR);
    console.log("💾 Backup de sesión actualizado.");
  } catch (e) {
    console.warn("⚠️ No pude respaldar la sesión:", e.message);
  }
}

// Restaura el backup sobre el perfil vivo si éste perdió la sesión y el backup la tiene.
function restaurarSesionSiHaceFalta() {
  try {
    if (rutaTieneSesion(SESSION_DIR)) return false;
    if (!rutaTieneSesion(BACKUP_DIR)) return false;
    console.log("♻️ Sesión viva ausente/incompleta. Restaurando desde backup...");
    copiarPerfil(BACKUP_DIR, SESSION_DIR);
    return true;
  } catch (e) {
    console.warn("⚠️ No pude restaurar la sesión desde backup:", e.message);
    return false;
  }
}

module.exports = { respaldarSesion, restaurarSesionSiHaceFalta, limpiarLocks };
