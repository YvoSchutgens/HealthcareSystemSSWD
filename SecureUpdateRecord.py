def update_patient_medical_record(username=None, role=None):
    from MainSystem import conn, c, list_patients
    from datetime import datetime
    import html

    # --- Safe Output Encoding ---
    def encode_output(text):
        """Encodes potentially dangerous characters for display"""
        return html.escape(str(text))

    print("\n=== Updating Medical Record ===")
    
    patient_id = list_patients()
    if not patient_id:
        return

    c.execute("PRAGMA table_info(patient_medical_record)")
    all_fields = [(i, row[1]) for i, row in enumerate(c.fetchall()) if row[1] != 'patient_id']

    # Define which fields can be edited by which roles
    staff_only_fields = {
        'username', 'name', 'address', 'phone', 'email', 
        'ssn', 'insurance', 'doctor_visit_summary', 'doctor_username'
    }

    # Define which fields can be edited by which roles
    nurse_only_fields = {
        'weight', 'height', 'blood_pressure', 'pulse_rate'
    }
    
    # Define which fields can be edited by which roles
    doctor_only_fields = {
        'treatment_content', 'prescription', 'lab_result', 
        'radiology_report', 'pathology_report', 'allergy_info', 
        'prescribed_medicines'
    }

    # Filter fields based on role
    if role == 'Staff':
        # Doctor can only edit medical fields
        fields = [(i, field) for i, field in all_fields if field in staff_only_fields]
    # Filter fields based on role
    if role == 'Nurse':
        # Doctor can only edit medical fields
        fields = [(i, field) for i, field in all_fields if field in nurse_only_fields]
    # Filter fields based on role
    if role == 'Doctor':
        # Doctor can only edit medical fields
        fields = [(i, field) for i, field in all_fields if field in doctor_only_fields]
    #else:
        # Other roles can edit all except medical fields
    #    fields = [(i, field) for i, field in all_fields if field not in doctor_only_fields]
    
    if not fields:
        print("No editable fields available for your role.\n")
        return

    print("Select field to update:")
    for idx, (_, field) in enumerate(fields, 1):
        print(f"{idx}. {field}")

    try:
        choice = int(input("Enter number of field to update: ")) - 1
        field = fields[choice][1]
    except (IndexError, ValueError):
        print("Invalid selection.\n")
        return

    new_value = input(f"Enter new value for {field}: ")
    c.execute(f"UPDATE patient_medical_record SET {field} = ? WHERE patient_id = ?", (new_value, patient_id))
    
    # Ask if doctor wants to continue editing (only add invoice when done)
    if role == 'Doctor' and field in doctor_only_fields:
        while True:
            more = input("Update another field? (y/n): ").lower()
            if more == 'y':
                # Show fields again
                print("\nSelect field to update:")
                for idx, (_, f) in enumerate(fields, 1):
                    print(f"{idx}. {f}")
                
                try:
                    choice = int(input("Enter number: ")) - 1
                    field = fields[choice][1]
                    new_value = input(f"Enter new value for {field}: ")
                    c.execute(f"UPDATE patient_medical_record SET {field} = ?, last_updated = CURRENT_TIMESTAMP WHERE patient_id = ?", 
                             (new_value, patient_id))
                except (IndexError, ValueError):
                    print("Invalid selection. Ending update session.")
                    break
            elif more == 'n':
                # Add copay payment
                copay_amount = 40.0
                c.execute("INSERT INTO payments (patient_id, type, amount, status) VALUES (?, 'copay', ?, 'Unpaid')",
                        (patient_id, copay_amount))
                print(f"\n$40 copay added for doctor visit.")
                conn.commit()
                # Only add ONE invoice when doctor finishes editing
                invoice_amount = 125.0
                c.execute("INSERT INTO payments (patient_id, type, amount, status) VALUES (?, 'invoice', ?, 'Unpaid')",
                         (patient_id, invoice_amount))
                print(f"\n$125 invoice added for medical services.")
                break
            else:
                print("Please enter 'y' or 'n'")
    
    conn.commit()
    print(f"Field updated: {encode_output(field)}")
    print(f"New value: {encode_output(new_value)}\n")
    print("Patient medical record updated.\n")