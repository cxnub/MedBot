CREATE_TABLES_QUERIES = ("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        fun_mode BOOLEAN DEFAULT FALSE
    ) ENGINE=InnoDB;
""",
"""
    CREATE TABLE IF NOT EXISTS hospitals (
        id VARCHAR(5) PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    ) ENGINE=InnoDB;
""",
"""
    CREATE TABLE IF NOT EXISTS doctors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        hospital_id VARCHAR(5) NOT NULL,
        INDEX (name)
    ) ENGINE=InnoDB;
""",
"""
    CREATE TABLE IF NOT EXISTS appointments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id BIGINT NOT NULL,
        doctor_id INT NOT NULL,
        hospital_id VARCHAR(5) NOT NULL,
        datetime TIMESTAMP NOT NULL
    ) ENGINE=InnoDB;
""",
"""
    ALTER TABLE appointments
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users (id),
    ADD CONSTRAINT fk_doctor FOREIGN KEY (doctor_id) REFERENCES doctors (id),
    ADD CONSTRAINT fk_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals (id);
""")

INSERT_DATA_QUERIES = ("""
    INSERT INTO hospitals (id, name) VALUES
    ('AH', 'Alexandra Hospital'),
    ('CGH', 'Changi General Hospital'),
    ('KTPH', 'Khoo Teck Puat Hospital'),
    ('KKH', "KK Women's and Children's Hospital"),
    ('NUH', 'National University Hospital'),
    ('NTFGH', 'Ng Teng Fong General Hospital'),
    ('SKGH', 'Sengkang General Hospital'),
    ('SGH', 'Singapore General Hospital'),
    ('TTSH', 'Tan Tock Seng Hospital'),
    ('WH', 'Woodlands Hospital');
""",
"""
    INSERT INTO doctors (name, hospital_id) VALUES
    ('Dr. John Doe', 'AH'),
    ('Dr. Jane Doe', 'AH'),
    ('Dr. John Doe', 'CGH'),
    ('Dr. Jane Doe', 'CGH'),
    ('Dr. John Doe', 'KTPH'),
    ('Dr. Jane Doe', 'KTPH'),
    ('Dr. John Doe', 'KKH'),
    ('Dr. Jane Doe', 'KKH'),
    ('Dr. John Doe', 'NUH'),
    ('Dr. Jane Doe', 'NUH'),
    ('Dr. John Doe', 'NTFGH'),
    ('Dr. Jane Doe', 'NTFGH'),
    ('Dr. John Doe', 'SKGH'),
    ('Dr. Jane Doe', 'SKGH'),
    ('Dr. John Doe', 'SGH'),
    ('Dr. Jane Doe', 'SGH'),
    ('Dr. John Doe', 'TTSH'),
    ('Dr. Jane Doe', 'TTSH'),
    ('Dr. John Doe', 'WH'),
    ('Dr. Jane Doe', 'WH');
""")

CHECK_AVAILABLE_SLOTS_QUERY = """
    WITH RECURSIVE time_slots AS (
        SELECT TIME('09:00:00') as slot_time
        UNION ALL
        SELECT ADDTIME(slot_time, '01:00:00')
        FROM time_slots
        WHERE slot_time < TIME('18:00:00')
    )
    SELECT 
        d.hospital_id,
        d.name as doctor,
        t.slot_time,
        CASE 
            WHEN a.id IS NULL THEN TRUE 
            ELSE FALSE 
        END AS available
    FROM 
        time_slots t
        CROSS JOIN (SELECT * FROM doctors WHERE id = %s) d
        LEFT JOIN appointments a ON 
            d.id = a.doctor_id AND
            d.hospital_id = a.hospital_id AND
            TIME(a.datetime) = t.slot_time AND
            DATE(a.datetime) = DATE(%s)
    ORDER BY t.slot_time;
"""

GET_APPOINTMENTS_QUERY = """
    SELECT 
        a.id,
        d.name as doctor,
        h.name as hospital,
        a.datetime
    FROM
        appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN hospitals h ON a.hospital_id = h.id
    WHERE
        a.user_id = %s AND
        a.id = %s
    ORDER BY a.datetime;
"""
