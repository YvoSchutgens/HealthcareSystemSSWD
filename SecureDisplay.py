def list_patients():
    from MainSystem import c, conn, get_patient_id_by_username
    c.execute("SELECT patient_id, username FROM patient_medical_record")
    patients = c.fetchall()
    for pid, username in patients:
        print(f"{pid}: {username}")
    return input("Enter patient ID to select: ")

