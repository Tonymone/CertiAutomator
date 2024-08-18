import 'bootstrap/dist/css/bootstrap.min.css';
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { IoInformationCircleSharp } from 'react-icons/io5';
import { Button, Container, Form, Col, Row, Modal } from 'react-bootstrap';
import 'react-tooltip/dist/react-tooltip.css';
import { Tooltip } from 'react-tooltip';

function App() {
  const [ms6File, setMs6File] = useState(null);
  const [bmsFile, setBmsFile] = useState(null);
  const [year, setYear] = useState('');
  const [courseName, setCourseName] = useState('');
  const [semester, setSemester] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState('');
  const [isValid, setIsValid] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.name === 'ms6File') {
      setMs6File(e.target.files[0]);
    } else if (e.target.name === 'bmsFile') {
      setBmsFile(e.target.files[0]);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name === 'year') setYear(value);
    if (name === 'courseName') setCourseName(value);
    if (name === 'semester') setSemester(value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isValid) {
      // Proceed with form submission for certificate generation
      setLoading(true);
      const formData = new FormData();
      formData.append('ms6File', ms6File);
      formData.append('bmsFile', bmsFile);
      formData.append('year', year);
      formData.append('courseName', courseName);
      formData.append('semester', semester);

      try {
        const response = await axios.post('http://127.0.0.1:5000/generate-certificates', formData, {
          responseType: 'blob',
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'certificates.pdf');
        document.body.appendChild(link);
        link.click();
        link.remove();

        // Delete files after downloading
        await axios.post('http://127.0.0.1:5000/delete-files');
        console.log("Files deleted successfully");

        setTimeout(() => {
          setShowModal(true); // Show modal after download and a delay
        }, 3000);
      } catch (error) {
        console.error('Error generating certificates', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const pollStatus = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/status');
      setStatus(response.data.message);
    } catch (error) {
      console.error("Error fetching status", error);
    }
  };

  const validateFiles = async () => {
    setError('');
    setIsValid(false);

    const formData = new FormData();
    formData.append('ms6File', ms6File);
    formData.append('bmsFile', bmsFile);

    try {
      const response = await axios.post('http://127.0.0.1:5000/validate-files', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.status === 200) {
        setIsValid(true);
      }
    } catch (error) {
      if (error.response && error.response.data.error) {
        setError(error.response.data.error);
      } else {
        setError('An unexpected error occurred.');
      }
    }
  };


  const handleCloseModal = () => {
    setShowModal(false);
  };

  useEffect(() => {
    if (!loading && showModal) {
      console.log('Modal should be shown'); // Debugging statement
    }
  }, [loading, showModal]);

  useEffect(() => {
    const intervalId = setInterval(pollStatus, 5000); 
    return () => clearInterval(intervalId);
  }, []);


  return (
    <Container className="app-container">
      <Row className="justify-content-md-center">
        <Col md="auto">
          {!loading && <h1 className="app-title">Certificate Generator</h1>}
          {loading ? (
            <div className="spinner-container">
              <svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
                <circle id="arc1" className="circle" cx="150" cy="150" r="120" opacity=".89" fill="none" stroke="#632b26" strokeWidth="12" strokeLinecap="square" strokeOpacity=".99213" paintOrder="fill markers stroke" />
                <circle id="arc2" className="circle" cx="150" cy="150" r="120" opacity=".49" fill="none" stroke="#632b26" strokeWidth="8" strokeLinecap="square" strokeOpacity=".99213" paintOrder="fill markers stroke" />
                <circle id="arc3" className="circle" cx="150" cy="150" r="100" opacity=".49" fill="none" stroke="#632b26" strokeWidth="20" strokeLinecap="square" strokeOpacity=".99213" paintOrder="fill markers stroke" />
                <circle id="arc4" className="circle" cx="150" cy="150" r="120" opacity=".49" fill="none" stroke="#632b26" strokeWidth="30" strokeLinecap="square" strokeOpacity=".99213" paintOrder="fill markers stroke" />
                <circle id="arc5" className="circle" cx="150" cy="150" r="100" opacity=".89" fill="none" stroke="#632b26" strokeWidth="8" strokeLinecap="square" strokeOpacity=".99213" paintOrder="fill markers stroke" />
                <circle id="arc6" className="circle" cx="150" cy="150" r="90" opacity=".49" fill="none" stroke="#632b26" strokeWidth="16" strokeLinecap="square" strokeOpacity=".99213" paintOrder="fill markers stroke" />
                <circle id="arc7" className="circle" cx="150" cy="150" r="90" opacity=".89" fill="none" stroke="#632b26" strokeWidth="8" strokeLinecap="square" strokeOpacity=".99213" paintOrder="fill markers stroke" />
                <circle id="arc8" className="circle" cx="150" cy="150" r="80" opacity=".79" fill="#4DD0E1" fillOpacity="0" stroke="#632b26" strokeWidth="8" strokeLinecap="square" strokeOpacity=".99213" paintOrder="fill markers stroke" />
              </svg>
              <p className="loading-text">{status}</p>
            </div>
          ) : (
            <Form onSubmit={handleSubmit} className="upload-form">
              <Form.Group controlId="formMs6File">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }} >
                  <Form.Label style={{ display: 'flex', alignItems: 'center' }}>Upload College Excel File</Form.Label>
                  <div style={{ marginLeft: '5px', display: 'flex', alignItems: 'center' }}>
                    <IoInformationCircleSharp style={{ cursor: 'pointer' }} data-tooltip-id="collegesheetrequirement" />
                  </div>
                </div>
                <Tooltip id="collegesheetrequirement" place="right" effect="solid">
                  <div>
                    MS6 File Requirements: <br />
                    1. Must be an .xlsx or .xls file <br />
                    2. Must contain the column: COLL_NO<br />
                  </div>
                </Tooltip>

                <Form.Control type="file" name="ms6File" onChange={handleFileChange} required />
              </Form.Group>
              <Form.Group controlId="formBmsFile" style={{ marginTop: '15px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }} >
                  <Form.Label style={{ display: 'flex', alignItems: 'center' }}>Upload Course Excel File</Form.Label>
                  <div style={{ marginLeft: '5px', display: 'flex', alignItems: 'center' }}>
                    <IoInformationCircleSharp style={{ cursor: 'pointer' }} data-tooltip-id="coursesheetrequirement" />
                  </div>
                </div>
                <Tooltip id="coursesheetrequirement" place="right" effect="solid">
                  <div>
                    MS6 File Requirements: <br />
                    1. Must be an .xlsx or .xls file <br />
                    2. Must contain the column: COLL_NO, SEAT_NO, RSLT, SEX, FREM<br />
                  </div>
                </Tooltip>
                <Form.Control type="file" name="bmsFile" onChange={handleFileChange} required />
              </Form.Group>
              <Form.Group controlId="formYear" style={{ marginTop: '10px' }}>
                <Form.Label>Enter Month and Year</Form.Label>
                <Form.Control type="text" name="year" value={year} onChange={handleInputChange} placeholder='e.g., NOVEMBER 2024' required />
              </Form.Group>
              <Form.Group controlId="formCourseName" style={{ marginTop: '10px' }}>
                <Form.Label>Enter Course Name</Form.Label>
                <Form.Control type="text" name="courseName" value={courseName} onChange={handleInputChange} placeholder='e.g., B.Com' required />
              </Form.Group>
              <Form.Group controlId="formSemester" style={{ marginTop: '10px' }}>
                <Form.Label>Enter Semester Number</Form.Label>
                <Form.Control type="text" name="semester" value={semester} onChange={handleInputChange} placeholder='e.g., 6' required />
              </Form.Group>

              <div className="button-container">
                <Button type="button" onClick={validateFiles} className="btn validate-button">Validate Files</Button>
                <Button type="submit" className="btn generate-button" disabled={!isValid}>
                  Generate Certificates
                </Button>
              </div>
            </Form>
          )}
        </Col>
      </Row>
      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>Success</Modal.Title>
        </Modal.Header>
        <Modal.Body>Certificate generated (check in the downloads folder of the device)</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default App;


