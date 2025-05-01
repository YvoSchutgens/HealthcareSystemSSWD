def view_patient_medical_record(username=None, role=None):
    from MainSystem import c, get_patient_id_by_username, list_patients
    import time
    import threading

    # Session expiration
    SESSION_TIMEOUT = 120  
    last_activity = time.time()
    session_active = True
    last_warning_time = time.time()

    def countdown_timer():
        """Background thread to show remaining time"""
        nonlocal last_activity, session_active, last_warning_time
        while session_active:
            elapsed = time.time() - last_activity
            remaining = max(0, SESSION_TIMEOUT - elapsed)
            
            # Show warning every 10 seconds
            if time.time() - last_warning_time >= 10 and remaining > 0:
                print(f"\nWarning: Session will expire in {int(remaining)} seconds.")
                last_warning_time = time.time()
            
            if remaining <= 0:
                session_active = False
                print("\nSession expired due to inactivity.")
                return
            
            time.sleep(1)  # Check every second

    def check_session():
        """Check if session has expired"""
        nonlocal last_activity
        if time.time() - last_activity > SESSION_TIMEOUT:
            print("\nSession expired due to inactivity.")
            return False
        return True
    
    # Start the countdown timer thread
    timer_thread = threading.Thread(target=countdown_timer, daemon=True)
    timer_thread.start()
    
    def display_record(record, fields):
        """Display record with session tracking"""
        nonlocal last_activity
        if not check_session():
            return False
        
        print("\nMedical Record:")
        for field, value in zip(fields, record):
            print(f"{field.replace('_', ' ').capitalize()}: {value}")
        
        

    try:
        if role == 'Patient':

            patient_id = get_patient_id_by_username(username)
            if not patient_id:
                print("Medical record does not exist.")
                return

            c.execute("""SELECT username, name, doctor_visit_summary, prescription, 
                         lab_result, radiology_report, pathology_report, allergy_info 
                         FROM patient_medical_record WHERE patient_id = ?""", (patient_id,))
            record = c.fetchone()
            
            if record:
                fields = ['username', 'name', 'doctor_visit_summary', 'prescription', 
                         'lab_result', 'radiology_report', 'pathology_report', 'allergy_info']
                
                while session_active:
                    if not check_session():
                        return
                    
                    print("\nMedical Record:")
                    for field, value in zip(fields, record):
                        print(f"{field.replace('_', ' ').capitalize()}: {value}")
                    
                    print("\nOptions:")
                    print("1. View record again")
                    print("2. Return to menu")
                    choice = input("Select option: ")
                    last_activity = time.time()
                    
                    if choice == '2':
                        return

        elif role == 'Doctor':
            c.execute("SELECT patient_id, username FROM patient_medical_record WHERE doctor_username = ?", (username,))
            patients = c.fetchall()
            if not patients:
                print("You have no assigned patients.")
                return
            
            for pid, p_username in patients:
                print(f"{pid}: {p_username}")
            
            patient_id = input("Enter patient ID to select: ")
            last_activity = time.time()
        else:
            patient_id = list_patients()
            last_activity = time.time()

        c.execute("SELECT * FROM patient_medical_record WHERE patient_id = ?", (patient_id,))
        record = c.fetchone()
        
        if record:
            fields = [description[0] for description in c.description]
            
            while session_active:
                if not check_session():
                    return
                
                print("\nMedical Record:")
                for field, value in zip(fields, record):
                    print(f"{field.replace('_', ' ').capitalize()}: {value}")
                
                print("\nOptions:")
                print("1. View record again")
                print("2. Return to menu")
                choice = input("Select option: ")
                last_activity = time.time()
                
                if choice == '2':
                    return
        else:
            print("Record not found.\n")

    finally:
        session_active = False
        timer_thread.join()  # Ensure thread stops