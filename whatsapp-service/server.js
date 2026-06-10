const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const QRCode = require('qrcode');
const qrcodeTerminal = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');
const { respaldarSesion, restaurarSesionSiHaceFalta, limpiarLocks } = require('./session-backup');

const app = express();
app.use(express.json());

let qrCode = null;
let client = null;
let isReady = false;

const SESSION_DIR = path.join(__dirname, '.wwhatsapp_auth');

// Crear directorio de sesión si no existe
if (!fs.existsSync(SESSION_DIR)) {
  fs.mkdirSync(SESSION_DIR, { recursive: true });
}

console.log('🚀 Iniciando WhatsApp Web Service...');

// Inicializar cliente
client = new Client({
  authStrategy: new LocalAuth({
    clientId: 'appointa',
    dataPath: SESSION_DIR,
  }),
  puppeteer: {
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--single-process',
    ],
    executablePath: '/usr/bin/chromium',
  },
});

client.on('qr', async (qr) => {
  console.clear();
  console.log('\n' + '='.repeat(50));
  console.log('🔗 ESCANEA ESTE QR CON TU TELÉFONO 🔗');
  console.log('='.repeat(50));
  console.log('');
  console.log('📱 Abre WhatsApp → Configuración → Dispositivos vinculados');
  console.log('');

  // Mostrar QR en terminal
  qrcodeTerminal.generate(qr, { small: true });

  try {
    const qrImage = await QRCode.toDataURL(qr, { width: 200 });
    qrCode = qrImage;
  } catch (err) {
    console.error('Error generando QR base64:', err);
    qrCode = qr;
  }

  console.log('');
  console.log('⏱️ Código válido por 2 minutos');
  console.log('='.repeat(50) + '\n');

  // Notificar a clientes SSE
  broadcastQR();
});

client.on('ready', async () => {
  console.log('\n✅ WhatsApp autenticado correctamente');
  console.log('✅ Listo para enviar mensajes\n');
  isReady = true;
  qrCode = null;
  programarBackupSesion();
});

// Agenda un backup diferido (30s) y otro periódico (6h). Idempotente.
let backupProgramado = false;
function programarBackupSesion() {
  if (backupProgramado) return;
  backupProgramado = true;
  setTimeout(respaldarSesion, 30000).unref();
  setInterval(respaldarSesion, 6 * 60 * 60 * 1000).unref();
}

client.on('authenticated', async () => {
  console.log('✅ Sesión autenticada');
  // Marcar listo inmediatamente cuando se autentica
  await new Promise(r => setTimeout(r, 2000));
  if (!isReady) {
    isReady = true;
    qrCode = null;
    console.log('✅ Cliente listo para enviar mensajes');
  }
});

client.on('auth_failure', (msg) => {
  console.error('❌ Error de autenticación:', msg);
  isReady = false;
});

client.on('disconnected', (reason) => {
  console.log('⚠️ Desconectado:', reason);
  isReady = false;
});

// Inicializa el cliente limpiando locks y restaurando la sesión, con reintentos.
async function startWhatsApp(intentos = 3, demora = 8000) {
  for (let i = 1; i <= intentos; i++) {
    limpiarLocks();
    restaurarSesionSiHaceFalta();

    try {
      await client.initialize();
      return; // Éxito
    } catch (err) {
      const msg = err.message || '';
      const recuperable =
        msg.includes('Execution context was destroyed') ||
        msg.includes('browser is already running') ||
        msg.includes('WS endpoint URL');

      if (recuperable && i < intentos) {
        console.warn(`⚠️ Error recuperable en intento ${i}/${intentos} (${msg.slice(0, 60)}). Reintentando en ${demora / 1000}s...`);
        await new Promise(r => setTimeout(r, demora));
      } else {
        console.error(`❌ Error fatal en initialize() (intento ${i}/${intentos}):`, msg);
        process.exit(1); // que el orquestador (Docker) reinicie
      }
    }
  }
}

startWhatsApp();

// Destruye el cliente (cierra Chromium y libera el lock) antes de salir.
let cerrando = false;
async function cerrarLimpio(code, motivo) {
  if (cerrando) return;
  cerrando = true;
  console.error(`🛑 Cerrando servicio (${motivo}). Liberando Chromium...`);

  const forzar = setTimeout(() => process.exit(code), 8000);
  try {
    await client.destroy();
  } catch (e) {
    console.error('⚠️ Error al destruir el cliente:', e.message);
  } finally {
    clearTimeout(forzar);
    limpiarLocks();
    process.exit(code);
  }
}
process.on('SIGINT', () => cerrarLimpio(0, 'SIGINT'));
process.on('SIGTERM', () => cerrarLimpio(0, 'SIGTERM'));

// Evita que un error transitorio (p.ej. 'auth timeout' al caerse la red) mate el proceso.
process.on('unhandledRejection', (reason) => {
  console.error('🚨 unhandledRejection (ignorado, el servicio sigue vivo):', reason?.message || reason);
});
process.on('uncaughtException', (err) => {
  console.error('🚨 uncaughtException (ignorado, el servicio sigue vivo):', err?.message || err);
});

// Reenviar QR cada 20s si no está autenticado y hay clientes escuchando (silencioso)
setInterval(() => {
  if (!isReady && qrCode && qrClients.length > 0) {
    broadcastQR();
  }
}, 20000);

let qrClients = [];

function broadcastQR() {
  qrClients.forEach(res => {
    if (!res.headersSent) {
      res.write(`data: ${JSON.stringify({qr_code: qrCode, timestamp: new Date().toISOString()})}\n\n`);
    }
  });
}

// Endpoints
// Server-Sent Events: streaming de QR cada 20s
app.get('/qr/watch', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');

  if (isReady) {
    res.write('data: {"authenticated": true}\n\n');
    res.end();
    return;
  }

  // Enviar QR inmediatamente si existe
  if (qrCode) {
    res.write(`data: ${JSON.stringify({qr_code: qrCode, timestamp: new Date().toISOString()})}\n\n`);
  }

  // Agregar a lista de clientes para broadcast
  qrClients.push(res);

  req.on('close', () => {
    qrClients = qrClients.filter(client => client !== res);
  });
});

app.get('/qr', (req, res) => {
  if (isReady) {
    return res.json({ qr_code: null, message: 'Ya autenticado' });
  }

  if (qrCode) {
    return res.json({ qr_code: qrCode, message: 'Escanea este QR' });
  }

  return res.json({ qr_code: null, message: 'Generando QR...' });
});

app.get('/status', (req, res) => {
  return res.json({
    authenticated: isReady,
    status: isReady ? 'authenticated' : 'pending_auth',
    message: isReady ? 'WhatsApp listo' : 'Escanea el QR en GET /qr',
  });
});

// Resuelve true si el mensaje alcanza el ack >= minAck (1=servidor) antes del timeout.
function esperarAck(msg, minAck, timeoutMs) {
  return new Promise((resolve) => {
    if ((msg?.ack ?? 0) >= minAck) return resolve(true);
    const target = msg?.id?._serialized;
    const handler = (m, ack) => {
      if (m?.id?._serialized === target && ack >= minAck) {
        cleanup();
        resolve(true);
      }
    };
    const cleanup = () => {
      clearTimeout(timer);
      client.removeListener('message_ack', handler);
    };
    const timer = setTimeout(() => { cleanup(); resolve(false); }, timeoutMs);
    client.on('message_ack', handler);
  });
}

app.post('/send', async (req, res) => {
  try {
    const { phone, message } = req.body;

    console.log(`📨 Intento de envío a ${phone}, isReady=${isReady}`);

    if (!phone || !message) {
      return res.status(400).json({
        success: false,
        error: 'phone y message requeridos',
      });
    }

    if (!isReady) {
      console.error('❌ WhatsApp no autenticado');
      return res.status(503).json({
        success: false,
        error: 'WhatsApp no autenticado',
      });
    }

    // Rechaza el envío si la página no está realmente conectada (isReady puede mentir).
    let estado = null;
    try {
      estado = await client.getState();
    } catch (e) {
      console.error('❌ No pude leer el estado de WhatsApp:', e.message);
    }
    if (estado !== 'CONNECTED') {
      console.error(`❌ WhatsApp sin conexión (estado: ${estado || 'desconocido'})`);
      return res.status(503).json({
        success: false,
        error: `WhatsApp sin conexión (estado: ${estado || 'desconocido'})`,
      });
    }

    // Limpiar número
    let phoneNumber = phone.replace(/\D/g, '');

    // Formato Argentina: asegurar que tiene código de país
    if (!phoneNumber.startsWith('54')) {
      phoneNumber = '54' + phoneNumber;
    }

    const chatId = phoneNumber + '@c.us';

    console.log(`📱 Número limpio: ${phoneNumber}`);
    console.log(`📱 ChatId: ${chatId}`);

    // Intentar obtener el chat existente
    let chatExists = false;
    try {
      const chat = await client.getChatById(chatId);
      chatExists = true;
      console.log(`💬 Chat existente encontrado`);
    } catch (e) {
      console.log(`📱 Chat no existe, creándolo con wa.me...`);
      // Abrir chat con wa.me para inicializarlo en WhatsApp Web
      try {
        const waUrl = `https://wa.me/${phoneNumber}`;
        console.log(`🔗 Navegando a ${waUrl}`);
        const page = await client.pupPage;
        await page.goto(waUrl, { waitUntil: 'networkidle2', timeout: 30000 });
        await new Promise(r => setTimeout(r, 30000)); // Esperar a que cargue
        chatExists = true;
        console.log(`✅ Chat inicializado con wa.me`);
      } catch (e) {
        console.log(`⚠️ Error inicializando con wa.me: ${e.message}`);
      }
    }

    // Enviar con reintentos
    const delays = [1000, 3000, 5000];
    let lastError;

    for (let attempt = 0; attempt <= delays.length; attempt++) {
      try {
        console.log(`🔄 Intento de envío ${attempt + 1}...`);
        const sent = await client.sendMessage(chatId, message);

        // Confirma entrega real esperando el ack del servidor (no solo el encolado).
        const confirmado = await esperarAck(sent, 1, 15000);
        if (confirmado) {
          console.log(`✅ Mensaje entregado a ${phone}`);
          return res.json({ success: true, message: 'Mensaje enviado' });
        }

        lastError = new Error('Encolado pero sin confirmación del servidor (posible falta de conexión)');
        console.warn(`⚠️ Intento ${attempt + 1}: ${lastError.message}`);
      } catch (error) {
        lastError = error;
        console.error(`❌ Intento ${attempt + 1}: ${error.message}`);
      }

      if (attempt < delays.length) {
        const delay = delays[attempt];
        console.log(`⏳ Esperando ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
      }
    }

    throw lastError || new Error('Error después de múltiples intentos');

  } catch (error) {
    console.error('❌ Error final:', error.message);
    return res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.get('/health', (req, res) => {
  return res.json({ status: 'ok', authenticated: isReady });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`📡 Servidor WhatsApp escuchando en puerto ${PORT}`);
});
