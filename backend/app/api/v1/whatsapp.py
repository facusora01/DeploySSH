from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["whatsapp"])


@router.get("/auth")
async def whatsapp_auth():
    """Get QR code for WhatsApp authentication."""
    from app.services.whatsapp import get_qr_code

    qr_code = await get_qr_code()

    if not qr_code:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhatsApp - Estado</title>
            <style>
                body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #ecf0f1; }
                .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
                h1 { color: #25d366; margin: 0; }
                p { color: #666; font-size: 18px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ WhatsApp Autenticado</h1>
                <p>Tu cuenta está lista para recibir mensajes</p>
            </div>
        </body>
        </html>
        """)

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp - Autenticación</title>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 500px;
            }}
            h1 {{
                color: #25d366;
                margin-top: 0;
                font-size: 28px;
            }}
            .qr-container {{
                margin: 30px 0;
                padding: 20px;
                background: #f5f5f5;
                border-radius: 10px;
            }}
            .qr-container img {{
                max-width: 100%;
                height: auto;
                border: 2px solid #25d366;
                border-radius: 8px;
            }}
            .instructions {{
                color: #666;
                font-size: 16px;
                margin: 20px 0;
                line-height: 1.6;
            }}
            .step {{
                background: #ecf0f1;
                padding: 15px;
                border-left: 4px solid #25d366;
                text-align: left;
                margin: 10px 0;
                border-radius: 5px;
            }}
            .timer {{
                color: #e74c3c;
                font-weight: bold;
                font-size: 18px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Escanea el QR</h1>
            <p style="color: #666; font-size: 14px;">Abre WhatsApp en tu teléfono</p>

            <div class="qr-container">
                <img src="{qr_code}" alt="WhatsApp QR Code">
            </div>

            <div class="instructions">
                <div class="step">
                    <strong>1.</strong> Abre WhatsApp en tu teléfono
                </div>
                <div class="step">
                    <strong>2.</strong> Ve a Configuración → Dispositivos vinculados
                </div>
                <div class="step">
                    <strong>3.</strong> Toca "Vincular un dispositivo"
                </div>
                <div class="step">
                    <strong>4.</strong> Escanea este código con tu cámara
                </div>
            </div>

            <div class="timer">⏱️ Código válido por 3 minutos</div>
        </div>

        <script>
            setInterval(() => {{
                fetch(window.location.href).then(r => r.text()).then(html => {{
                    if (html.includes("✅ WhatsApp Autenticado")) {{
                        location.reload();
                    }}
                }});
            }}, 5000);
        </script>
    </body>
    </html>
    """)


@router.get("/status")
def whatsapp_status():
    """Check WhatsApp authentication status."""
    from app.services.whatsapp import client_ready

    return {
        "status": "authenticated" if client_ready.is_set() else "pending_auth",
        "message": "WhatsApp listo" if client_ready.is_set() else "Escanea el QR en GET /api/v1/whatsapp/auth",
    }
