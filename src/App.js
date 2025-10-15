// src/App.js

import React, { useState } from 'react';
import './App.css';
import ResultsDisplay from './ResultsDisplay';
import DonutAnalytics from './DonutAnalytics'; // Corrected typo
import Banner from './Banner';

function App() {
  const [bank, setBank] = useState('axis');
  const [file, setFile] = useState(null);
  const [parsedData, setParsedData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file) {
      setError('Please select a PDF file to upload.');
      return;
    }

    setIsLoading(true);
    setParsedData(null);
    setError('');

    const formData = new FormData();
    formData.append('bank', bank);
    formData.append('file', file);

    const apiUrl = 'https://credit-card-statement-parser.onrender.com/parse-statement/';

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `API Error: ${response.statusText}`);
      }

      const data = await response.json();
      setParsedData(data);

    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // The main container is now the single top-level element
    <div className="container">
      {/* Banner is now inside the card */}
      <Banner /> 

      <h1>Credit Card Statement Parser 💳</h1>
      <p>Upload a PDF statement, select the bank, and view the extracted data.</p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="bank">Select Bank:</label>
          <select id="bank" value={bank} onChange={(e) => setBank(e.target.value)} required>
            <option value="axis">Axis Bank</option>
            <option value="bob">Bank of Baroda</option>
            <option value="kotak">Kotak Bank</option>
            <option value="sbi">SBI</option>
            <option value="yes">Yes Bank</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="file">Upload PDF Statement:</label>
          <input
            type="file"
            id="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            required
          />
        </div>
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Parsing...' : 'Parse Statement'}
        </button>
      </form>

      {isLoading && <div className="loading">Parsing your statement... 🚀</div>}
      {error && <div className="error">{error}</div>}
      
      {parsedData && (
        <>
          <ResultsDisplay data={parsedData} />
          <DonutAnalytics data={parsedData} /> 
        </>
      )}
    </div>
  );
}

export default App;