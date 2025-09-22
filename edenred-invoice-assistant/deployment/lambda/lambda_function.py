import json
import logging
import boto3
import re
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize SageMaker runtime client
sagemaker_runtime = boto3.client('sagemaker-runtime')

# Configure your endpoint name
ENDPOINT_NAME = 'huggingface-cpu-1755487898'

def lambda_handler(event, context):
    """
    Bulletproof Lambda function that prioritizes training data and never returns raw JSON
    """
    logger.info(f"Function invoked")
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,HEAD,OPTIONS,POST,PUT',
        'Content-Type': 'application/json'
    }
    
    try:
        # Handle OPTIONS request for CORS
        if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # Parse user message
        user_message = extract_user_message(event)
        
        if not user_message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'No message provided'})
            }
        
        logger.info(f"User message: {user_message}")
        
        # Get response using comprehensive training data
        response_text = get_comprehensive_response(user_message)
        
        # Ensure we NEVER return raw JSON or invalid responses
        response_text = ensure_clean_response(response_text, user_message)
        
        logger.info(f"Final response: {response_text[:100]}...")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': response_text,
                'status': 'success'
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Service temporarily unavailable',
                'response': 'I apologize for the technical issue. Please email ap-support@edenred.com for immediate assistance with your invoice and payment questions.',
                'status': 'error'
            })
        }


def extract_user_message(event):
    """Extract user message from event"""
    if 'body' in event and event['body']:
        try:
            if isinstance(event['body'], str):
                body_data = json.loads(event['body'])
                return body_data.get('message', '').strip()
            elif isinstance(event['body'], dict):
                return event['body'].get('message', '').strip()
        except json.JSONDecodeError:
            pass
    
    if 'message' in event:
        return event.get('message', '').strip()
    
    return None


def get_comprehensive_response(user_message):
    """
    Get response with complete coverage of all training data
    """
    # Complete training data mapping from your instructions.jsonl
    training_responses = {
        # Direct mappings from training data
        "How do I submit a new invoice?": "Log in to the supplier portal, navigate to Invoices → Create, enter the PO number (if applicable), upload your PDF or XML, review the preview, and click Submit.",
        
        "How can I update my bank details for payments?": "Go to Settings → Bank Details in the supplier portal, enter your new account and routing/SWIFT information, and complete the two-factor verification. Changes are reviewed within 1–2 business days for security.",
        
        "How do I change my company address?": "In the portal, open Settings → Company Profile and update your legal and remittance addresses. Upload supporting documentation (utility bill or letterhead). Our team verifies changes within 2–3 business days.",
        
        "Where can I view my remittance advice?": "Open Payments → Remittances in the portal to download remittance advice PDFs. You can also enable email remittances under Settings → Notifications.",
        
        "Check payment status": "Open Payments → Remittances in the portal to download remittance advice PDFs. You can also enable email remittances under Settings → Notifications.",
        
        "What is the typical approval turnaround time?": "Standard approval takes 3–5 business days after a valid invoice is received. Complex three-way matches or disputes may extend this timeframe.",
        
        "My invoice was rejected. How do I see the reason?": "Go to Invoices → All, click the rejected invoice, and review the Rejection Reason in the Activity panel. Correct the issue and use the Resubmit button.",
        
        "How do I contact accounts payable?": "Email ap-support@edenred.com with your supplier ID, invoice number, and PO (if applicable). For urgent issues, include URGENT in the subject line.",
        
        "How do I reset my password for the supplier portal?": "To reset your password, go to the supplier portal login page and click the 'Forgot Password' link. You will receive an email with instructions to set a new password.",
        
        "Invoice was rejected": "Go to Invoices → All, click the rejected invoice, and review the Rejection Reason in the Activity panel. Correct the issue and use the Resubmit button.",
        
        "Update bank details": "Go to Settings → Bank Details in the supplier portal, enter your new account and routing/SWIFT information, and complete the two-factor verification. Changes are reviewed within 1–2 business days for security."
    }
    
    # Check for exact matches first
    message_lower = user_message.lower().strip()
    
    for question, answer in training_responses.items():
        if message_lower == question.lower().strip():
            logger.info(f"Exact match found for: {question}")
            return answer
    
    # Keyword-based matching with comprehensive coverage
    keyword_mappings = {
        # Invoice submission
        'submit': "Log in to the supplier portal, navigate to Invoices → Create, enter the PO number (if applicable), upload your PDF or XML, review the preview, and click Submit.",
        
        # Payment and remittance
        'payment': "Open Payments → Remittances in the portal to download remittance advice PDFs. You can also enable email remittances under Settings → Notifications.",
        'remittance': "Open Payments → Remittances in the portal to download remittance advice PDFs. You can also enable email remittances under Settings → Notifications.",
        'status': "Open Payments → Remittances in the portal to download remittance advice PDFs. You can also enable email remittances under Settings → Notifications.",
        
        # Bank details
        'bank': "Go to Settings → Bank Details in the supplier portal, enter your new account and routing/SWIFT information, and complete the two-factor verification. Changes are reviewed within 1–2 business days for security.",
        
        # Address updates
        'address': "In the portal, open Settings → Company Profile and update your legal and remittance addresses. Upload supporting documentation (utility bill or letterhead). Our team verifies changes within 2–3 business days.",
        
        # Approval times
        'approval': "Standard approval takes 3–5 business days after a valid invoice is received. Complex three-way matches or disputes may extend this timeframe.",
        'turnaround': "Standard approval takes 3–5 business days after a valid invoice is received. Complex three-way matches or disputes may extend this timeframe.",
        'long': "Standard approval takes 3–5 business days after a valid invoice is received. Complex three-way matches or disputes may extend this timeframe.",
        
        # Rejections
        'rejected': "Go to Invoices → All, click the rejected invoice, and review the Rejection Reason in the Activity panel. Correct the issue and use the Resubmit button.",
        'reject': "Go to Invoices → All, click the rejected invoice, and review the Rejection Reason in the Activity panel. Correct the issue and use the Resubmit button.",
        
        # Password issues
        'password': "To reset your password, go to the supplier portal login page and click the 'Forgot Password' link. You will receive an email with instructions to set a new password.",
        'login': "To reset your password, go to the supplier portal login page and click the 'Forgot Password' link. You will receive an email with instructions to set a new password.",
        'reset': "To reset your password, go to the supplier portal login page and click the 'Forgot Password' link. You will receive an email with instructions to set a new password.",
        
        # Contact and support
        'contact': "Email ap-support@edenred.com with your supplier ID, invoice number, and PO (if applicable). For urgent issues, include URGENT in the subject line.",
        'support': "Email ap-support@edenred.com with your supplier ID, invoice number, and PO (if applicable). For urgent issues, include URGENT in the subject line.",
        'help': "Email ap-support@edenred.com with your supplier ID, invoice number, and PO (if applicable). For urgent issues, include URGENT in the subject line."
    }
    
    # Find best keyword match
    for keyword, response in keyword_mappings.items():
        if keyword in message_lower:
            logger.info(f"Keyword match found: {keyword}")
            return response
    
    # Default comprehensive response
    logger.info("Using default comprehensive response")
    return "I can help you with invoice and payment questions. Common topics include: submitting invoices, checking payment status, updating bank details, changing addresses, approval times, rejected invoices, and password resets. For immediate assistance, email ap-support@edenred.com with your supplier ID and invoice number."


def ensure_clean_response(response_text, user_message):
    """
    Ensure response is always clean and never contains raw JSON or artifacts
    """
    if not response_text:
        return "I'm here to help with invoice and payment questions. Please email ap-support@edenred.com for assistance."
    
    response_str = str(response_text)
    
    # Check for and remove JSON artifacts
    if '{' in response_str and '"generated_text"' in response_str:
        logger.warning("Detected JSON in response, cleaning...")
        
        # Try to extract just the text content
        try:
            # Look for generated_text content
            match = re.search(r'"generated_text":\s*"([^"]*)"', response_str)
            if match:
                response_str = match.group(1)
            else:
                # Fallback to training data
                return get_training_data_fallback(user_message)
        except:
            return get_training_data_fallback(user_message)
    
    # Remove common artifacts
    response_str = re.sub(r'\\n', '\n', response_str)
    response_str = re.sub(r'\\u[\da-fA-F]{4}', '', response_str)
    response_str = re.sub(r'### \w+:', '', response_str)
    response_str = re.sub(r'\[\s*\]', '', response_str)
    response_str = re.sub(r'- \[ \]', '•', response_str)
    
    # Clean up formatting
    response_str = re.sub(r'\n\s*\n', '\n', response_str)
    response_str = response_str.strip()
    
    # Validate final response
    if len(response_str) < 10 or 'generated_text' in response_str or '{' in response_str:
        logger.warning("Response failed validation, using fallback")
        return get_training_data_fallback(user_message)
    
    return response_str


def get_training_data_fallback(user_message):
    """
    Last resort fallback using training data
    """
    message_lower = user_message.lower() if user_message else ""
    
    if 'payment' in message_lower or 'status' in message_lower:
        return "Open Payments → Remittances in the portal to download remittance advice PDFs. You can also enable email remittances under Settings → Notifications."
    elif 'submit' in message_lower or 'invoice' in message_lower:
        return "Log in to the supplier portal, navigate to Invoices → Create, enter the PO number (if applicable), upload your PDF or XML, review the preview, and click Submit."
    elif 'bank' in message_lower:
        return "Go to Settings → Bank Details in the supplier portal, enter your new account and routing/SWIFT information, and complete the two-factor verification. Changes are reviewed within 1–2 business days for security."
    elif 'password' in message_lower:
        return "To reset your password, go to the supplier portal login page and click the 'Forgot Password' link. You will receive an email with instructions to set a new password."
    else:
        return "I can help you with invoice and payment questions. For immediate assistance, email ap-support@edenred.com with your supplier ID and invoice number."