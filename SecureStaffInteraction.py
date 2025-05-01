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

def staff_menu(username):
    from MainSystem import create_patient_medical_record, update_patient_medical_record, view_patient_medical_record
    
    # Generate initial token
    current_token = generate_xsrf_token(username)
    
    while True:
        print("\nStaff Menu:")
        print("1. Create patient medical record")
        print("2. Update patient medical record")
        print("3. View patient medical record")
        print("4. Logout")
        
        opt = input("Choose an option: ")
        
        # Automatically include token for sensitive actions
        if opt == '1':
            # For demonstration, show the token being used
            print(f"[Security] Using XSRF token: {current_token}")
            create_patient_medical_record()
            current_token = generate_xsrf_token(username)  # Rotate token
            
        elif opt == '2':
            print(f"[Security] Using XSRF token: {current_token}")
            update_patient_medical_record(username, 'Staff')
            current_token = generate_xsrf_token(username)  # Rotate token
            
        elif opt == '3':
            view_patient_medical_record()  # No token needed for read-only
            
        elif opt == '4':
            # Clear token on logout
            if username in xsrf_tokens:
                del xsrf_tokens[username]
            break