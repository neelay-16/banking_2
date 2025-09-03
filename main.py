from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json
import os
import requests

app = FastAPI(title="Banking AI Agent API", version="1.0.0")
security = HTTPBearer()

# Add CORS middleware for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables for ElevenLabs
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "your_api_key_here")
ELEVENLABS_AGENT_ID = os.environ.get("ELEVENLABS_AGENT_ID", "your_agent_id_here")

# Pydantic Models for Request/Response
class CustomerAuth(BaseModel):
    phone_number: str
    pin: Optional[str] = None

class CallRequest(BaseModel):
    phone_number: str
    customer_id: Optional[str] = None

class AccountInfo(BaseModel):
    account_number: str
    account_type: str
    balance: float
    currency: str
    status: str
    opened_date: date

class Transaction(BaseModel):
    transaction_id: str
    date: datetime
    amount: float
    description: str
    type: str
    balance_after: float
    merchant: Optional[str] = None

# Sample Banking Data
SAMPLE_CUSTOMERS = {
    "CUST001": {
        "customer_id": "CUST001",
        "name": "John Smith",
        "phone": "+1234567890",
        "email": "john.smith@email.com",
        "accounts": [
            {
                "account_number": "ACC123456789",
                "account_type": "Savings",
                "balance": 15750.50,
                "currency": "USD",
                "status": "Active",
                "opened_date": "2020-03-15"
            },
            {
                "account_number": "ACC987654321",
                "account_type": "Checking",
                "balance": 3250.75,
                "currency": "USD",
                "status": "Active",
                "opened_date": "2020-03-15"
            }
        ],
        "transactions": [
            {
                "transaction_id": "TXN001",
                "account_number": "ACC123456789",
                "date": "2025-09-01T10:30:00",
                "amount": -50.00,
                "description": "ATM Withdrawal",
                "type": "debit",
                "balance_after": 15750.50,
                "merchant": "Chase ATM #1234"
            },
            {
                "transaction_id": "TXN002",
                "account_number": "ACC123456789",
                "date": "2025-08-30T14:22:00",
                "amount": 2500.00,
                "description": "Salary Deposit",
                "type": "credit",
                "balance_after": 15800.50,
                "merchant": "ABC Corp Payroll"
            }
        ],
        "loans": [
            {
                "loan_id": "LOAN001",
                "loan_type": "Home Mortgage",
                "principal_amount": 250000.00,
                "outstanding_balance": 187500.00,
                "monthly_payment": 1850.00,
                "next_due_date": "2025-09-15",
                "interest_rate": 3.5
            }
        ],
        "credit_cards": []
    },
    "CUST002": {
        "customer_id": "CUST002",
        "name": "Sarah Johnson",
        "phone": "+1987654321",
        "email": "sarah.johnson@email.com",
        "accounts": [
            {
                "account_number": "ACC555666777",
                "account_type": "Checking",
                "balance": 8900.25,
                "currency": "USD",
                "status": "Active",
                "opened_date": "2019-07-10"
            }
        ],
        "transactions": [
            {
                "transaction_id": "TXN004",
                "account_number": "ACC555666777",
                "date": "2025-09-02T08:45:00",
                "amount": -75.50,
                "description": "Utility Bill Payment",
                "type": "debit",
                "balance_after": 8900.25,
                "merchant": "City Electric Company"
            }
        ],
        "loans": [],
        "credit_cards": []
    },
    # Add an Indian customer for testing
    "CUST003": {
        "customer_id": "CUST003",
        "name": "Rahul Sharma",
        "phone": "+919876543210",
        "email": "rahul.sharma@email.com",
        "accounts": [
            {
                "account_number": "ACC111222333",
                "account_type": "Savings",
                "balance": 85000.00,
                "currency": "INR",
                "status": "Active",
                "opened_date": "2021-01-10"
            }
        ],
        "transactions": [
            {
                "transaction_id": "TXN005",
                "account_number": "ACC111222333",
                "date": "2025-09-02T15:30:00",
                "amount": -5000.00,
                "description": "UPI Payment",
                "type": "debit",
                "balance_after": 85000.00,
                "merchant": "PhonePe"
            }
        ],
        "loans": [],
        "credit_cards": []
    }
}

# Banking Knowledge Base
BANKING_KNOWLEDGE = {
    "account_types": {
        "savings": "Savings accounts earn interest and are ideal for long-term savings goals.",
        "checking": "Checking accounts are designed for daily transactions and bill payments."
    },
    "fees": {
        "atm_withdrawal": "$2.50 for out-of-network ATMs",
        "overdraft": "$35.00 per overdraft transaction",
        "wire_transfer": "$25.00 domestic, $45.00 international"
    },
    "hours": {
        "branches": "Monday-Friday: 9:00 AM - 5:00 PM, Saturday: 9:00 AM - 2:00 PM",
        "customer_service": "24/7 phone support available"
    }
}

# Authentication function (for agent endpoints only)
async def verify_agent_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    expected_token = "banking_agent_secure_token_2025"
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Banking API is running!", "status": "healthy"}

# Serve the HTML file at the root
@app.get("/index.html")
async def get_index():
    return FileResponse("static/index.html")

# PUBLIC ENDPOINT - No authentication required for frontend
@app.post("/authenticate_customer")
async def authenticate_customer(auth_data: CustomerAuth):
    """Authenticate customer using phone number (public endpoint for frontend)"""
    for customer_id, customer in SAMPLE_CUSTOMERS.items():
        if customer["phone"] == auth_data.phone_number:
            return {
                "success": True,
                "customer_id": customer_id,
                "name": customer["name"],
                "message": f"Welcome back, {customer['name']}!"
            }
    raise HTTPException(status_code=404, detail="Customer not found")

# PUBLIC ENDPOINT - Make call through ElevenLabs
@app.post("/make_call")
async def make_call(call_data: CallRequest):
    """Initiate a call through ElevenLabs agent"""
    try:
        print(f"Making call to {call_data.phone_number} with customer_id: {call_data.customer_id}")
        
        # Check if we have valid ElevenLabs credentials
        if ELEVENLABS_API_KEY == "your_api_key_here" or ELEVENLABS_AGENT_ID == "your_agent_id_here":
            # Return mock response for testing
            return {
                "success": True,
                "message": f"Mock call initiated to {call_data.phone_number}",
                "call_id": f"MOCK_CALL_{int(datetime.now().timestamp())}",
                "status": "initiated",
                "note": "This is a mock response. Set ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID environment variables for real calls."
            }
        
        # Try different possible API endpoints based on ElevenLabs documentation
        possible_urls = [
            f"https://api.elevenlabs.io/v1/convai/agents/{ELEVENLABS_AGENT_ID}/phone",
            f"https://api.elevenlabs.io/v1/convai/agents/{ELEVENLABS_AGENT_ID}/call",
            f"https://api.elevenlabs.io/v1/agents/{ELEVENLABS_AGENT_ID}/phone",
            f"https://api.elevenlabs.io/v1/agents/{ELEVENLABS_AGENT_ID}/call"
        ]
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Prepare customer data if available
        customer_context = {}
        if call_data.customer_id:
            customer = SAMPLE_CUSTOMERS.get(call_data.customer_id)
            if customer:
                customer_context = {
                    "customer_name": customer["name"],
                    "customer_id": call_data.customer_id,
                    "phone_number": call_data.phone_number,
                    "accounts": customer["accounts"]
                }
        
        # Try different payload formats
        payloads_to_try = [
            {
                "phone_number": call_data.phone_number,
                "context": customer_context
            },
            {
                "to": call_data.phone_number,
                "agent_id": ELEVENLABS_AGENT_ID,
                "context": customer_context
            },
            {
                "phone_number": call_data.phone_number,
                "agent_id": ELEVENLABS_AGENT_ID,
                "metadata": customer_context
            }
        ]
        
        # Try each combination of URL and payload
        for url in possible_urls:
            for payload in payloads_to_try:
                try:
                    print(f"Trying URL: {url}")
                    print(f"With payload: {payload}")
                    
                    # Make the API call to ElevenLabs
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    
                    print(f"ElevenLabs response status: {response.status_code}")
                    print(f"ElevenLabs response: {response.text}")
                    
                    if response.status_code == 200:
                        elevenlabs_response = response.json()
                        return {
                            "success": True,
                            "message": f"Call initiated to {call_data.phone_number}",
                            "call_id": elevenlabs_response.get("call_id", f"EL_CALL_{int(datetime.now().timestamp())}"),
                            "status": "initiated",
                            "elevenlabs_response": elevenlabs_response,
                            "endpoint_used": url
                        }
                    elif response.status_code == 404:
                        # Continue trying other combinations
                        continue
                    else:
                        # For non-404 errors, we might have the right endpoint but wrong payload
                        error_detail = response.text
                        print(f"ElevenLabs API error (non-404): {error_detail}")
                        # Continue trying but log this
                        
                except requests.exceptions.RequestException as req_e:
                    print(f"Request error for {url}: {str(req_e)}")
                    continue
        
        # If we get here, all attempts failed
        raise HTTPException(
            status_code=404, 
            detail="Could not find correct ElevenLabs API endpoint. Please check your Agent ID and API documentation."
        )
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        print(f"Call error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

     
# Optional: Add endpoint to check call status
@app.get("/call_status/{call_id}")
async def get_call_status(call_id: str):
    """Get the status of a call"""
    try:
        if call_id.startswith("MOCK_"):
            return {
                "success": True,
                "call_data": {
                    "call_id": call_id,
                    "status": "completed",
                    "duration": 120,
                    "note": "This is mock call status data"
                }
            }
            
        url = f"https://api.elevenlabs.io/v1/convai/calls/{call_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "call_data": response.json()
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get call status: {str(e)}")

# PROTECTED ENDPOINTS - Require authentication for agent access
@app.get("/customer/{customer_id}/accounts")
async def get_customer_accounts(customer_id: str, token: str = Depends(verify_agent_token)):
    """Get all accounts for a customer"""
    if customer_id not in SAMPLE_CUSTOMERS:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = SAMPLE_CUSTOMERS[customer_id]
    accounts = customer["accounts"]
    return {
        "success": True,
        "customer_name": customer["name"],
        "accounts": accounts
    }

@app.get("/customer/{customer_id}/transactions")
async def get_recent_transactions(customer_id: str, limit: int = 5, token: str = Depends(verify_agent_token)):
    """Get recent transactions for customer"""
    if customer_id not in SAMPLE_CUSTOMERS:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = SAMPLE_CUSTOMERS[customer_id]
    transactions = customer["transactions"]
    sorted_transactions = sorted(transactions, key=lambda x: x["date"], reverse=True)[:limit]
    return {
        "success": True,
        "customer_name": customer["name"],
        "transactions": sorted_transactions
    }

@app.get("/customer/{customer_id}/loans")
async def get_customer_loans(customer_id: str, token: str = Depends(verify_agent_token)):
    """Get all loans for a customer"""
    if customer_id not in SAMPLE_CUSTOMERS:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = SAMPLE_CUSTOMERS[customer_id]
    return {
        "success": True,
        "customer_name": customer["name"],
        "loans": customer["loans"]
    }

@app.get("/knowledge/hours")
async def get_banking_hours(token: str = Depends(verify_agent_token)):
    """Get branch and service hours"""
    return BANKING_KNOWLEDGE["hours"]

@app.get("/knowledge/fees")
async def get_fee_information(token: str = Depends(verify_agent_token)):
    """Get current fee structure"""
    return BANKING_KNOWLEDGE["fees"]

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# For Railway deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on port {port}")
    print(f"ElevenLabs API Key: {'Set' if ELEVENLABS_API_KEY != 'your_api_key_here' else 'Not Set'}")
    print(f"ElevenLabs Agent ID: {'Set' if ELEVENLABS_AGENT_ID != 'your_agent_id_here' else 'Not Set'}")
    uvicorn.run(app, host="0.0.0.0", port=port)
