def create_patient_medical_record():
    from MainSystem import conn, c, get_patient_id_by_username
    import psutil
    import subprocess
    import html
    from datetime import datetime, timedelta
    from sys import platform

    # --- Security Functions ---
    def encode_output(text):
        """Encodes potentially dangerous characters for display"""
        return html.escape(str(text))
    
    # --- Keylogger Detection Functions ---
    def check_for_keyloggers():
        """Check for known keylogger processes running on the system."""
        keylogger_indicators = [
            'keylog', 'notep', 'logger', 'logkbd', 'kbdlog', 'keystroke',
            'hook', 'spy', 'recorder', 'capture', 'rat', 'remote',
            'hax', 'inject', 'sniff'
        ]
        
        try:
            # Process check
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if any(indicator in proc_name for indicator in keylogger_indicators):
                        print(f"\n[!] SECURITY ALERT: Keylogger detected (Process: '{proc_name}')")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Windows registry check
            if platform == "win32":
                try:
                    reg = subprocess.run(
                        ['reg', 'query', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'],
                        capture_output=True, text=True)
                    if any(indicator in reg.stdout.lower() for indicator in keylogger_indicators):
                        print("\n[!] SECURITY ALERT: Keylogger detected in Windows Registry")
                        return True
                except subprocess.CalledProcessError:
                    pass

            return False  # No detection

        except Exception as e:
            print(f"[!] Error during security check: {e}")
            return False

    # --- Main Record Creation Logic ---
    print("\n--- Creating Patient Medical Record ---")
    
    # Single initial system check
    if check_for_keyloggers():
        print("Record creation CANCELLED due to security risk.\n")
        return
    else:
        print("[✓] Security check passed\n")

    # Input with validation
    def get_input(prompt, validate_fn=None):
        while True:
            value = input(prompt)
            if not validate_fn or validate_fn(value):
                return value
            print("Invalid input. Please try again.")

    # SSN validation (exactly 9 digits)
    def validate_ssn(ssn):
        return ssn.isdigit() and len(ssn) == 9

    # Collect data
    name = get_input("Name: ")
    address = get_input("Address: ")
    phone = get_input("Phone: ")
    email = get_input("Email: ")
    ssn = get_input("Social Security Number: ", validate_ssn)
    insurance = get_input("Insurance: ")
    
    doctor_visit_summary = get_input("Doctor visit summary: ")
    username = get_input("Patient username: ")
    doctor_username = get_input("Doctor's username: ")

    # Verify username exists
    c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if not c.fetchone():
        print("Error: Username doesn't exist.\n")
        return

    # Database operation
    try:
        # Start transaction
        conn.execute("BEGIN TRANSACTION")

        c.execute('''
            INSERT OR REPLACE INTO patient_medical_record 
            (username, name, address, phone, email, ssn, insurance, 
             doctor_visit_summary, doctor_username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, name, address, phone, email, ssn, insurance,
              doctor_visit_summary, doctor_username))

        # Verify only one record exists
        c.execute("SELECT COUNT(*) FROM patient_medical_record WHERE username = ?", (username,))
        new_count = c.fetchone()[0]
        
        if new_count != 1:
            conn.rollback()
            print("\n[!] CRITICAL ERROR: Multiple records creations detected.")
            return
        
        conn.commit()
        print("\n[✓] Patient Medical Record successfully created")
        print(encode_output(f"Patient: {name}"))
        print(encode_output(f"Address: {address}"))
        print(encode_output(f"Phone: {phone}"))
        print(encode_output(f"Email: {email}"))
        print(encode_output(f"SSN: {'*'*(len(ssn)-4)}{ssn[-4:]}"))  # Partial masking
        print(encode_output(f"Insurance: {insurance}"))
        print(encode_output(f"Doctor Visit Summary: {doctor_visit_summary}"))
        print(encode_output(f"Assigned Doctor: {doctor_username}"))
        print(f"{new_count} Record created\n")
    except Exception as e:
        conn.rollback()
        print(f"\n[!] Database error: {str(e)}")