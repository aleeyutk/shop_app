import logging
import httpx
from typing import Dict, Any, List
from app.config import get_settings

logger = logging.getLogger("shop.mailgun")
settings = get_settings()


def generate_order_html(order_data: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    """Generate a clean, responsive HTML email template for the order confirmation."""
    item_rows = ""
    for item in items:
        img_tag = (
            f'<img src="{item.get("product_image")}" alt="{item["product_name"]}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; margin-right: 12px; vertical-align: middle;" />'
            if item.get("product_image")
            else ""
        )
        item_rows += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px 8px; font-size: 14px; color: #111827;">
                {img_tag}
                <span style="font-weight: 500;">{item['product_name']}</span>
            </td>
            <td style="padding: 12px 8px; text-align: center; font-size: 14px; color: #4b5563;">
                x{item['quantity']}
            </td>
            <td style="padding: 12px 8px; text-align: right; font-size: 14px; font-weight: 600; color: #111827;">
                ${item['subtotal']:.2f}
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Order Confirmation - {order_data['id']}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 24px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 32px 24px; text-align: center; color: #ffffff;">
                <div style="display: inline-block; background-color: #4338ca; border-radius: 50%; width: 48px; height: 48px; line-height: 48px; margin-bottom: 12px; font-size: 24px;">
                    ✨
                </div>
                <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.025em;">Order Confirmed!</h1>
                <p style="margin: 8px 0 0 0; font-size: 15px; color: #c7d2fe;">Thank you for shopping with NovaShop</p>
            </div>

            <!-- Main Content -->
            <div style="padding: 32px 24px;">
                <p style="font-size: 16px; color: #374151; margin-top: 0;">
                    Hi <strong>{order_data['customer_name']}</strong>,
                </p>
                <p style="font-size: 14px; color: #4b5563; line-height: 1.6;">
                    We've received your order and our team is already preparing it for shipment. Here is a summary of your purchase:
                </p>

                <!-- Order Meta Card -->
                <div style="background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 20px 0; font-size: 14px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #6b7280;">Order Number:</span>
                        <strong style="color: #111827; font-family: monospace;">{order_data['id']}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #6b7280;">Status:</span>
                        <span style="background-color: #d1fae5; color: #065f46; font-weight: 600; padding: 2px 8px; border-radius: 9999px; font-size: 12px;">{order_data['status']}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6b7280;">Payment Method:</span>
                        <strong style="color: #111827;">{order_data.get('payment_method', 'Credit Card')}</strong>
                    </div>
                </div>

                <!-- Items Table -->
                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 24px 0 12px 0;">Items Ordered</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="border-bottom: 2px solid #e5e7eb; text-align: left; font-size: 12px; color: #6b7280; text-transform: uppercase;">
                            <th style="padding: 8px;">Product</th>
                            <th style="padding: 8px; text-align: center;">Qty</th>
                            <th style="padding: 8px; text-align: right;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {item_rows}
                    </tbody>
                </table>

                <!-- Pricing Summary -->
                <div style="border-top: 2px solid #f3f4f6; padding-top: 16px; margin-bottom: 24px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 14px; color: #4b5563;">
                        <span>Subtotal:</span>
                        <span>${order_data['subtotal']:.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 14px; color: #4b5563;">
                        <span>Standard Shipping:</span>
                        <span>{f"${order_data['shipping_fee']:.2f}" if order_data['shipping_fee'] > 0 else "FREE"}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 18px; font-weight: 700; color: #111827; border-top: 1px solid #e5e7eb; padding-top: 10px; margin-top: 10px;">
                        <span>Total Paid:</span>
                        <span style="color: #4338ca;">${order_data['total_amount']:.2f} {order_data['currency']}</span>
                    </div>
                </div>

                <!-- Shipping Address Card -->
                <div style="background-color: #f8fafc; border-left: 4px solid #4338ca; padding: 14px 16px; border-radius: 4px; margin-bottom: 24px;">
                    <h4 style="margin: 0 0 6px 0; font-size: 14px; color: #1e293b; text-transform: uppercase; letter-spacing: 0.05em;">Shipping Destination</h4>
                    <p style="margin: 0; font-size: 14px; color: #475569; line-height: 1.5;">
                        {order_data['customer_name']}<br/>
                        {order_data['shipping_address']}<br/>
                        {order_data['city']}, {order_data['state']} {order_data['postal_code']}<br/>
                        {order_data['country']}
                    </p>
                </div>

                <p style="font-size: 13px; color: #9ca3af; text-align: center; margin-top: 32px; border-top: 1px solid #f3f4f6; padding-top: 16px;">
                    Questions regarding your order? Reply directly to this email or visit our help center.<br/>
                    &copy; 2026 NovaShop. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


async def send_order_confirmation_email(
    order_data: Dict[str, Any], items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Send an order confirmation email via Mailgun API.
    If Mailgun API key is not configured, gracefully logs the email and simulates success.
    """
    recipient_email = order_data["customer_email"]
    order_id = order_data["id"]
    subject = f"Order Confirmed: #{order_id} - NovaShop"

    html_content = generate_order_html(order_data, items)
    plain_text = f"""
    Hello {order_data['customer_name']},

    Thank you for your order with NovaShop!
    Order Number: {order_id}
    Status: {order_data['status']}
    Total Paid: ${order_data['total_amount']:.2f} {order_data['currency']}

    Shipping Address:
    {order_data['shipping_address']}
    {order_data['city']}, {order_data['state']} {order_data['postal_code']}
    {order_data['country']}

    We will notify you once your package ships!
    """.strip()

    if not settings.is_mailgun_configured:
        logger.info(
            "============================================================\n"
            "[MAILGUN SIMULATION / LOCAL MODE]\n"
            "To: %s\nSubject: %s\nOrder ID: %s\nTotal: $%.2f\n"
            "Note: Set MAILGUN_API_KEY and MAILGUN_DOMAIN in .env to deliver real emails.\n"
            "============================================================",
            recipient_email,
            subject,
            order_id,
            order_data["total_amount"],
        )
        return {
            "sent": True,
            "simulated": True,
            "message_id": f"simulated-mailgun-{order_id}",
            "message": "Mailgun simulation: Email logged successfully in development mode.",
        }

    mailgun_url = f"{settings.MAILGUN_BASE_URL.rstrip('/')}/{settings.MAILGUN_DOMAIN}/messages"
    auth = ("api", settings.MAILGUN_API_KEY)
    payload = {
        "from": settings.MAILGUN_FROM_EMAIL,
        "to": [recipient_email],
        "subject": subject,
        "text": plain_text,
        "html": html_content,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(mailgun_url, auth=auth, data=payload)
            if response.status_code in (200, 201, 202):
                res_data = response.json()
                logger.info("Mailgun email sent successfully to %s: %s", recipient_email, res_data)
                return {
                    "sent": True,
                    "simulated": False,
                    "message_id": res_data.get("id"),
                    "message": res_data.get("message", "Email queued"),
                }
            else:
                logger.error(
                    "Mailgun API error (%d): %s", response.status_code, response.text
                )
                return {
                    "sent": False,
                    "simulated": False,
                    "error": response.text,
                    "status_code": response.status_code,
                }
    except Exception as exc:
        logger.exception("Failed to send Mailgun email to %s: %s", recipient_email, exc)
        return {
            "sent": False,
            "simulated": False,
            "error": str(exc),
        }
