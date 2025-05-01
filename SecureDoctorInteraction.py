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


def doctor_menu(username):
    from MainSystem import update_patient_medical_record, view_patient_medical_record
    
    # Generate initial token
    current_token = generate_xsrf_token(username)
    
    while True:
        print("\nDoctor Menu:")
        print("1. Update patient medical record")
        print("2. View patient medical record")
        print("3. Logout")
        
        opt = input("Choose an option: ")
        
        if opt == '1':
            print(f"[Security] Using XSRF token: {current_token}")
            update_patient_medical_record(username, 'Doctor')
            current_token = generate_xsrf_token(username)
            
        elif opt == '2':
            view_patient_medical_record(username, 'Doctor')  # Read-only
            
        elif opt == '3':
            if username in xsrf_tokens:
                del xsrf_tokens[username]
            break