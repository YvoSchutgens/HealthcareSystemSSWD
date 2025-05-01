from collections import defaultdict
import time

# Global rate limit tracker
cancellation_tracker = defaultdict(list)  # {username: [timestamps]}


def cancel_appointment(username):
    from MainSystem import conn, c, get_patient_id_by_username
    from datetime import datetime, timedelta

    # --- Rate Limiter Configuration ---
   # --- Rate Limiter Constants ---
    RATE_LIMIT_WINDOW = 30  # seconds
    MAX_CANCELLATIONS = 1    # per time window

    # --- Check Rate Limit ---
    now = time.time()
    recent_cancellations = [
        ts for ts in cancellation_tracker[username] 
        if now - ts < RATE_LIMIT_WINDOW
    ]

    if len(recent_cancellations) >= MAX_CANCELLATIONS:
        oldest = recent_cancellations[0]
        remaining = int(RATE_LIMIT_WINDOW - (now - oldest))
        print(f"\nMaximum amount of cancellations reached in a short time. Please wait {remaining} seconds.")
        return

    # --- Main Logic ---
    patient_id = get_patient_id_by_username(username)
    if not patient_id:
        print("No medical record found.")
        return

    c.execute("""
        SELECT appointment_id, datetime, reason, status 
        FROM appointments 
        WHERE patient_id = ? AND status = 'Scheduled'
    """, (patient_id,))
    appointments = c.fetchall()

    if not appointments:
        print("You have no active appointments to cancel.\n")
        return

    print("\nYour Appointments:")
    for i, (aid, dt, reason, status) in enumerate(appointments, 1):
        print(f"{i}. ID: {aid}, Date/Time: {dt}, Reason: {reason}")

    try:
        choice = int(input("\nSelect appointment to cancel (number): ")) - 1
        appt_id = appointments[choice][0]
    except (IndexError, ValueError):
        print("Invalid selection.\n")
        return

    c.execute("UPDATE appointments SET status = 'Cancelled' WHERE appointment_id = ?", (appt_id,))
    conn.commit()
    
    # Record successful cancellation
    cancellation_tracker[username].append(now)
    print("\n[✓] Appointment cancelled successfully")
    print(f"Recent cancellations: {len(recent_cancellations)+1}/{MAX_CANCELLATIONS} in last {RATE_LIMIT_WINDOW} seconds\n")