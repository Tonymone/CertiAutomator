
# Certificate Generator

This project is a web application that generates PDF certificates for students based on data provided in two Excel files. The application allows users to upload these Excel files, validate them, and then generate a PDF containing certificates for all eligible students.

## Features

- **File Upload and Validation**: Upload two Excel files, one containing college data and another with course data. The files are validated to ensure they meet the required criteria.
- **Batch Processing**: Processes large Excel files in batches to avoid system crashes.
- **PDF Generation**: Generates a PDF containing certificates for students who have passed, using a pre-designed certificate template.
- **Real-time Status Updates**: Displays the current status of certificate generation in real-time.
- **File Deletion**: Automatically deletes uploaded and generated files after downloading to keep the server clean.
- **Resume on Failure**: If the application is interrupted, it can resume processing from the last saved checkpoint.

## Tech Stack

- **Frontend**: React, React-Bootstrap, Bootstrap, Axios
- **Backend**: Flask, Pandas, FPDF, OpenCV
- **Others**: Threading for concurrent processing, File management with Python's `os` module

## Installation

### Prerequisites

- Node.js and npm
- Python 3.7+
- Flask
- pip

### Clone the repository

```bash
git clone https://github.com/Tonymone/CertiAutomator.git
cd CertiAutomator
```

### Backend Setup

1. Navigate to the `backend` directory:

   ```bash
   cd backend
   ```

2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask server:

   ```bash
   python app.py
   ```

### Frontend Setup

1. Navigate to the `frontend` directory:

   ```bash
   cd frontend
   ```

2. Install the required npm packages:

   ```bash
   npm install
   ```

3. Start the React development server:

   ```bash
   npm start
   ```

## Usage

1. **Upload Files**: Open the web application and upload the required MS6 and BMS Excel files.
2. **Validate Files**: Click the "Validate Files" button to ensure that the files are in the correct format.
3. **Generate Certificates**: Once the files are validated, enter the month, year, course name, and semester, then click "Generate Certificates".
4. **Download PDF**: After the processing is complete, the PDF of the certificates will be automatically downloaded.

## File Requirements

- **MS6 File**: Must contain the column `COLL_NO` and should be in `.xlsx` or `.xls` format.
- **BMS File**: Must contain the columns `SEAT_NO`, `NAME`, `SEX`, `RSLT`, `FREM`, `RES` and should be in `.xlsx` or `.xls` format.

## Folder Structure

- **frontend/**: Contains the React frontend code.
- **backend/**: Contains the Flask backend code.
- **uploads/**: Folder where uploaded files are temporarily stored.
- **gens/**: Folder where generated certificate PDFs are stored.
- **certificate-template.png**: Template image used for generating certificates.

## API Endpoints

- **POST `/validate-files`**: Validates the uploaded Excel files.
- **POST `/generate-certificates`**: Generates certificates from the validated files.
- **GET `/status`**: Fetches the current status of the certificate generation process.
- **POST `/delete-files`**: Deletes uploaded and generated files.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Create a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

- **React-Bootstrap** for providing UI components.
- **FPDF** for generating PDF files.
- **Pandas** for data processing.

## Contact

For any inquiries or issues, please contact `[tonymone1234@gmail.com](mailto:tonymone1234@gmail.com)` or `shivaji.ware23@spit.ac.in(mailto:shivaji.ware23@spit.ac.in)`.

---

**Disclaimer**: This project was developed for educational purposes.
