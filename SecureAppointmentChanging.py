def change_appointment(username):
    from MainSystem import conn, c, get_patient_id_by_username
    from datetime import datetime, timedelta
    import re

    # Input validatior
    def is_valid_date(date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def is_valid_time(time_str):
        return re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str)

    def is_valid_reason(reason):
        return len(reason) <= 100 and not any(char in reason for char in [";", "--", "/*", "*/", "'", "\""])

    def sanitize_input(input_str, max_length=100, allowed_chars=None):
        if allowed_chars is None:
            allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.:,@")
        return all(c in allowed_chars for c in input_str) and len(input_str) <= max_length

    patient_id = get_patient_id_by_username(username)
    if not patient_id:
        print("No medical record found.")
        return

    # Get all appointments for the patient
    c.execute("SELECT appointment_id, datetime, reason, status FROM appointments WHERE patient_id = ?", (patient_id,))
    appointments = c.fetchall()

    if not appointments:
        print("No appointments to change.")
        return

    print("\nYour Appointments:")
    for i, (aid, dt, reason, status) in enumerate(appointments, 1):
        print(f"{i}. ID: {aid}, Time: {dt}, Reason: {reason}, Status: {status}")

    # Appointment selection validation
    try:
        choice = int(input("Select appointment number to change: "))
        if choice < 1 or choice > len(appointments):
            raise ValueError
        appt_id, old_datetime, old_reason, _ = appointments[choice - 1]
    except ValueError:
        print("Error: Please enter a valid appointment number.")
        return

    # Date validation
    date_str = input("Enter new date for appointment (YYYY-MM-DD): ")
    if not is_valid_date(date_str):
        print("Error: Invalid date format. Please use YYYY-MM-DD format.")
        return

    # Get doctor's username for this patient
    c.execute("SELECT doctor_username FROM patient_medical_record WHERE patient_id = ?", (patient_id,))
    result = c.fetchone()
    if not result or not result[0]:
        print("Doctor not assigned to this patient.")
        return
    doctor_username = result[0]

    # Get all 30-min slots
    all_slots = [(datetime.strptime("08:00", "%H:%M") + timedelta(minutes=30 * i)).strftime("%H:%M") for i in range(18)]

    # Check booked slots for that doctor on new date
    c.execute("""
        SELECT strftime('%H:%M', a.datetime)
        FROM appointments a
        JOIN patient_medical_record p ON a.patient_id = p.patient_id
        WHERE date(a.datetime) = ?
        AND p.doctor_username = ?
        AND a.status != 'Cancelled'
        AND a.appointment_id != ?
    """, (date_str, doctor_username, appt_id))
    booked_slots = {row[0] for row in c.fetchall()}
    available_slots = [slot for slot in all_slots if slot not in booked_slots]

    if not available_slots:
        print("No available slots for that day.")
        return

    print("\nAvailable slots:")
    for i, slot in enumerate(available_slots):
        print(f"{i + 1}. {slot}")

    try:
        slot_choice = int(input("Select a time slot number: ")) 
        if slot_choice < 1 or slot_choice > len(available_slots):
            raise ValueError
        selected_time = available_slots[slot_choice - 1]
    except ValueError:
        print("Invalid selection.")
        return

    # Reason validation
    new_reason = input(f"Enter reason for appointment [Current: {old_reason[:50]}]: ") or old_reason
    if not is_valid_reason(new_reason):
        print("Error: Reason contains invalid characters or is too long.")
        return

    # Final confirmation
    confirm = input(f"Confirm change to {date_str} {selected_time}? (y/n): ").lower()
    if confirm != 'y':
        print("Appointment change cancelled.")
        return

    # Update with parameterized query
    try:
        c.execute("UPDATE appointments SET datetime = ?, reason = ? WHERE appointment_id = ?",
                 (f"{date_str} {selected_time}", new_reason, appt_id))
        conn.commit()
        print(f"Appointment successfully updated to {date_str} {selected_time}.\n")
    except Exception as e:
        conn.rollback()
        print(f"Database error: {str(e)}")