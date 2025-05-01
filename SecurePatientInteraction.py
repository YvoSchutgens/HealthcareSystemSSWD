import secrets
from functools import wraps

# Dictionary to store valid tokens
xsrf_tokens = {}

def generate_xsrf_token(username):
    """Generate and store a new XSRF token for the user"""
    token = secrets.token_urlsafe(32)
    xsrf_tokens[username] = token
    return token

def validate_xsrf_token(username, token):
    """Validate the provided token against stored token"""
    stored_token = xsrf_tokens.get(username)
    return stored_token is not None and secrets.compare_digest(stored_token, token)

def patient_menu(username):
    from MainSystem import make_appointment, change_appointment, cancel_appointment, view_patient_medical_record, make_payment
    
    # Generate initial token
    current_token = generate_xsrf_token(username)
    
    while True:
        print("\nPatient Menu:")
        print("1. Make appointment")
        print("2. Change appointment")
        print("3. Cancel appointment")
        print("4. View patient medical record")
        print("5. Make payment")
        print("6. Logout")
        
        opt = input("Choose an option: ")
        
        if opt == '1':
            print(f"[Security] Using XSRF token: {current_token}")
            make_appointment(username)
            current_token = generate_xsrf_token(username)
            
        elif opt == '2':
            print(f"[Security] Using XSRF token: {current_token}")
            change_appointment(username)
            current_token = generate_xsrf_token(username)
            
        elif opt == '3':
            print(f"[Security] Using XSRF token: {current_token}")
            cancel_appointment(username)
            current_token = generate_xsrf_token(username)
            
        elif opt == '4':
            view_patient_medical_record(username)  # Read-only
            
        elif opt == '5':
            print(f"[Security] Using XSRF token: {current_token}")
            make_payment(username)
            current_token = generate_xsrf_token(username)
            
        elif opt == '6':
            if username in xsrf_tokens:
                del xsrf_tokens[username]
            break
