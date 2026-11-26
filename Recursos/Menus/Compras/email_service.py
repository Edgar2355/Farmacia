import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "farmaciascruzazul.05@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASSWORD", "")


def _enviar_mensaje_smtp(destinatario, msg):
    servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
    servidor.ehlo()
    servidor.starttls()
    servidor.ehlo()
    servidor.login(SMTP_USER, SMTP_PASS)
    servidor.sendmail(SMTP_USER, destinatario, msg.as_string())
    servidor.quit()


def enviar_factura(destinatario, asunto, mensaje, archivo_pdf, async_send=True):
    """Envía la factura PDF por correo al cliente (por defecto en un hilo en segundo plano)."""
    if not destinatario or "@" not in str(destinatario):
        return

    def _tarea():
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = destinatario
            msg["Subject"] = asunto
            msg.attach(MIMEText(mensaje, "plain", "utf-8"))

            if archivo_pdf and os.path.exists(archivo_pdf):
                nombre_archivo = os.path.basename(archivo_pdf)
                with open(archivo_pdf, "rb") as archivo:
                    parte = MIMEBase("application", "octet-stream")
                    parte.set_payload(archivo.read())
                encoders.encode_base64(parte)
                parte.add_header(
                    "Content-Disposition",
                    f"attachment; filename={nombre_archivo}",
                )
                msg.attach(parte)

            _enviar_mensaje_smtp(destinatario, msg)
            print(f"Correo con factura enviado correctamente a {destinatario}")
        except Exception as e:
            print("Error enviando correo de factura:", e)

    if async_send:
        threading.Thread(target=_tarea, daemon=True).start()
    else:
        _tarea()


def enviar_correo_proveedor(destinatario, productos, direccion, async_send=True):
    """Envía orden de compra por correo al proveedor (por defecto en un hilo en segundo plano)."""
    if not destinatario or "@" not in str(destinatario):
        return

    def _tarea():
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = destinatario
            msg["Subject"] = "Solicitud de pedido - Farmacia CUCEI"

            cuerpo = "Estimado proveedor,\n\nLe solicitamos de la manera más atenta los siguientes productos:\n\n"
            for item in productos:
                cuerpo += (
                    f"- {item['nombre']} | Cantidad: {item['cantidad']} | "
                    f"Subtotal: ${item['precio']}\n"
                )
            cuerpo += f"\nFavor de enviar a la sucursal: {direccion}\n\n"
            cuerpo += "Agradecemos su pronta atención y colaboración."

            msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
            _enviar_mensaje_smtp(destinatario, msg)
            print(f"Correo enviado al proveedor ({destinatario}) correctamente")
        except Exception as e:
            print("Error enviando correo al proveedor:", e)

    if async_send:
        threading.Thread(target=_tarea, daemon=True).start()
    else:
        _tarea()
