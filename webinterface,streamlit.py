# Streamlit Web Interface  #
def main():
    """Runs the Streamlit app for uploading and processing checks."""
    st.title("Automated Bank Check Extraction")
    
    uploaded_files = st.file_uploader("Upload a Check Image", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
    
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
