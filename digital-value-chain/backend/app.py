
import json, os, decimal, boto3
from urllib.parse import urljoin

dynamodb = boto3.resource("dynamodb")
OFFERS = dynamodb.Table(os.getenv("OFFERS_TABLE"))
ORDERS = dynamodb.Table(os.getenv("ORDERS_TABLE"))

def _resp(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body, default=str)}

def list_offers():
    items = OFFERS.scan().get("Items", [])
    return _resp(200, items)

def create_offer(body):
    OFFERS.put_item(Item=body)
    return _resp(200, {"ok": True})

def start_checkout(body):
    # Stripe minimal call (test mode)
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
    price = int(float(body["price"]) * 100)
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price_data":{"currency":"usd","product_data":{"name": body["sku"]},"unit_amount": price}, "quantity":1}],
        customer_email=body["email"],
        success_url=body["success_url"], cancel_url=body["cancel_url"]
    )
    ORDERS.put_item(Item={"orderId": session.id, "sku": body["sku"], "email": body["email"], "status":"created"})
    return _resp(200, {"checkout_url": session.url})

def stripe_webhook(event):
    data = json.loads(event["body"] or "{}")
    if data.get("type") == "checkout.session.completed":
        sid = data["data"]["object"]["id"]
        ORDERS.update_item(
            Key={"orderId": sid},
            UpdateExpression="set #s=:p",
            ExpressionAttributeNames={"#s":"status"},
            ExpressionAttributeValues={":p":"paid"}
        )
    return _resp(200, {"received": True})

LABELS = {
    "billing": ["invoice","payment","charge","refund","stripe"],
    "technical": ["error","api","integration","timeout","bug"],
    "sales": ["quote","pricing","offer","plan","contract"]
}
TEMPLATES = {
    "billing":"Thanks for reaching out about billing. I checked your order and...",
    "technical":"Sorry about the technical trouble. Here are steps to unblock...",
    "sales":"Happy to help with pricing and offers. Here’s a summary..."
}

def ai_triage(body):
    text = (body.get("text") or "").lower()
    scores = {k: sum(w in text for w in ws) for k, ws in LABELS.items()}
    label = max(scores, key=scores.get) if any(scores.values()) else "sales"
    return _resp(200, {"label": label, "draft": TEMPLATES[label]})

# Router
def handler(event, context):
    route = (event.get("requestContext", {}).get("http", {}).get("path") or "/")
    method = (event.get("requestContext", {}).get("http", {}).get("method") or "GET")
    body = json.loads(event.get("body") or "{}")

    if route == "/offers" and method == "GET": return list_offers()
    if route == "/offers" and method == "POST": return create_offer(body)
    if route == "/checkout" and method == "POST": return start_checkout(body)
    if route == "/stripe/webhook" and method == "POST": return stripe_webhook(event)
    if route == "/ai/triage" and method == "POST": return ai_triage(body)
    return _resp(404, {"error": "not found"})
