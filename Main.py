import os
import cv2
import pytesseract
import mysql.connector
import re
import numpy as np
import streamlit as st
import pandas as pd
from PIL import Image

# Image Preprocessing #
def preprocess_image(image_path):
    """Preprocesses the image to improve OCR accuracy."""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, sharpen_kernel)

    thresh = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return processed


# Extract Text Using OCR #
def extract_text(image_path):
    """Extracts text from the preprocessed image using Tesseract OCR."""
    processed_image = preprocess_image(image_path)

    # Tesseract OCR with optimized settings
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(processed_image, config=custom_config)

    print(f"Extracted OCR Text from {image_path}:\n{text}\n{'-'*50}")
    return text


# Extract Relevant Check Details #
def parse_check_details(text):
    """Extracts date, name, account number, amount, payee, and check number using regex."""
    details = {}

    account_match = re.search(r'\b\d{10,16}\b', text)
    details['account_number'] = account_match.group(0) if account_match else "Not Found"

    amount_match = re.search(r'\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?', text)
    details['amount'] = amount_match.group(0) if amount_match else "Not Found"

    date_match = re.search(r'\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b', text)
    details['date'] = date_match.group(0) if date_match else "Not Found"

    name_match = re.search(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b', text)
    details['name'] = name_match.group(0) if name_match else "Not Found"

    payee_match = re.search(r'Pay to the Order of\s+([A-Za-z\s]+)', text, re.IGNORECASE)
    details['payee'] = payee_match.group(1).strip() if payee_match else "Not Found"

    check_number_match = re.search(r'\b\d{3,6}\b', text)
    details['check_number'] = check_number_match.group(0) if check_number_match else "Not Found"

    print("Extracted Check Details:", details)
    return details


# Save Extracted Data to MySQL #
def save_to_mysql(details):
    """Saves extracted check details to MySQL."""
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


# Streamlit Web Interface #
def main():
    """Runs the Streamlit app for uploading and processing checks."""
    st.title("Automated Bank Check Extraction")

    uploaded_files = st.file_uploader(
        "Upload a Check Image", accept_multiple_files=True,
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_files:
        os.makedirs("uploaded_checks", exist_ok=True)
        extracted_data = []

        st.success("Files uploaded successfully!")

        for uploaded_file in uploaded_files:
            # Save uploaded file locally
            image_path = os.path.join("uploaded_checks", uploaded_file.name)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Process OCR and extract details
            text = extract_text(image_path)
            details = parse_check_details(text)

            save_to_mysql(details)
            extracted_data.append(details)

        df = pd.DataFrame(extracted_data)
        st.success("OCR results saved to MySQL database.")
        st.write("### Extracted Data:")
        st.dataframe(df)


if __name__ == "__main__":
    main()
