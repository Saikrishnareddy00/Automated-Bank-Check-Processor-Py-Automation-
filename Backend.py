def save_to_mysql(details):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='bank_checks'
        )
        cursor = connection.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                account_number VARCHAR(50),
                amount VARCHAR(50),
                date VARCHAR(50),
                name VARCHAR(255),
                payee VARCHAR(255),
                check_number VARCHAR(50)
            )
        """)

        # Insert extracted data
        cursor.execute("""
            INSERT INTO check_data (account_number, amount, date, name, payee, check_number) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (details['account_number'], details['amount'], details['date'], 
              details['name'], details['payee'], details['check_number']))

        connection.commit()
        print("Data saved to MySQL successfully!")

    except mysql.connector.Error as err:
        print("MySQL Error:", err)

    finally:
        cursor.close()
        connection.close() 
