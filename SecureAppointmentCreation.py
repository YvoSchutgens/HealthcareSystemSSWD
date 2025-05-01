def make_appointment(username):
    from MainSystem import conn, c, get_patient_id_by_username
    from datetime import datetime, timedelta
    import html

    # --- Safe Output Encoding ---
    def encode_output(text):
        """Encodes potentially dangerous characters for HTML display"""
        return html.escape(text)
    
    print("\n=== Appointment Creation ===")
    
    patient_id = get_patient_id_by_username(username)
    if not patient_id:
        print("No medical record found for appointment.")
        return

    # Get doctor_username for this patient
    c.execute("SELECT doctor_username FROM patient_medical_record WHERE patient_id = ?", (patient_id,))
    result = c.fetchone()
    if not result or not result[0]:
        print("No doctor assigned to this patient.")
        return

    doctor_username = result[0]

    # Get appointment date
    date_str = input("Enter appointment date (YYYY-MM-DD): ")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date information provided.")
        return

    # Generate all possible time slots from 08:00 to 16:30 (30 min intervals)
    all_slots = [(datetime.strptime("08:00", "%H:%M") + timedelta(minutes=30 * i)).strftime("%H:%M") for i in range(18)]

    # Fetch all appointments for that doctor on that date (excluding cancelled ones)
    c.execute("""
        SELECT strftime('%H:%M', a.datetime)
        FROM appointments a
        JOIN patient_medical_record p ON a.patient_id = p.patient_id
        WHERE date(a.datetime) = ?
        AND p.doctor_username = ?
        AND a.status != 'Cancelled'
    """, (date_str, doctor_username))

    booked_slots = {row[0] for row in c.fetchall()}
    available_slots = [slot for slot in all_slots if slot not in booked_slots]

    if not available_slots:
        print("No available time slots with your doctor on that day.\n")
        return

    print("\nAvailable time slots with your doctor:")
    for i, slot in enumerate(available_slots):
        print(f"{i + 1}. {slot}")

    try:
        slot_choice = int(input("Select a time slot number: ")) - 1
        selected_time = available_slots[slot_choice]
    except (IndexError, ValueError):
        print("Invalid selection.")
        return

    reason = input("Enter reason for appointment: ")
    full_datetime = f"{date_str} {selected_time}"

    c.execute("INSERT INTO appointments (patient_id, datetime, reason, status) VALUES (?, ?, ?, ?)",
              (patient_id, full_datetime, reason, "Scheduled"))
    conn.commit()
    
    # Confirmation message with encoded output
    safe_datetime = encode_output(full_datetime)
    safe_reason = encode_output(reason)
    
    print(f"Appointment created at {full_datetime} with your doctor.\n")
    print(f"Reason: {encode_output(reason)}")


