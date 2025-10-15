// src/ResultsDisplay.js

import React from 'react';
import './ResultsDisplay.css';

// Helper to format currency
const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return 'N/A';
  return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const ResultsDisplay = ({ data }) => {
  if (!data) return null;

  const {
    bank_name,
    card_number,
    statement_date,
    payment_due_date,
    credit_limit,
    total_amount_due,
    minimum_amount_due,
    available_credit,
    transactions,
  } = data;

  return (
    <div className="results-container">
      <div className="summary-header">
        <div>
          <h2>{bank_name} Statement</h2>
          <p className="card-number">Card: {card_number || 'N/A'}</p>
        </div>
        <div className="statement-date">
            <strong>Statement Date:</strong> {statement_date || 'N/A'}
        </div>
      </div>

      {/* Key Metrics Highlight */}
      <div className="key-metrics">
        <div className="metric-item total-due">
          <span className="label">Total Amount Due</span>
          <span className="value">{formatCurrency(total_amount_due)}</span>
        </div>
        <div className="metric-item due-date">
          <span className="label">Payment Due Date</span>
          <span className="value">{payment_due_date || 'N/A'}</span>
        </div>
      </div>

      {/* Secondary Details Grid */}
      <div className="details-grid">
        <div className="detail-item">
          <span className="label">Credit Limit</span>
          <span className="value">{formatCurrency(credit_limit)}</span>
        </div>
        <div className="detail-item">
          <span className="label">Available Credit</span>
          <span className="value">{formatCurrency(available_credit)}</span>
        </div>
        <div className="detail-item">
          <span className="label">Minimum Amount Due</span>
          <span className="value">{formatCurrency(minimum_amount_due)}</span>
        </div>
      </div>

      <div className="transactions-section">
        <h3>Recent Transactions</h3>
        {transactions && transactions.length > 0 ? (
          <div className="table-wrapper">
            <table className="transactions-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th className="amount-col">Amount</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((txn, index) => (
                  <tr key={index} className={txn.type}>
                    <td>{txn.date}</td>
                    <td>{txn.description}</td>
                    <td className="amount-col">{formatCurrency(txn.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>No transactions found in this statement.</p>
        )}
      </div>
    </div>
  );
};

export default ResultsDisplay;