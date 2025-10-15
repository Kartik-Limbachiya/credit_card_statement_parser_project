// src/DonutAnalytics.js

import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import './DonutAnalytics.css';

ChartJS.register(ArcElement, Tooltip, Legend);

const DonutAnalytics = ({ data }) => {
  if (!data || !data.transactions || data.transactions.length === 0) {
    return null;
  }

  // Process and sort transactions
  const debitTransactions = data.transactions
    .filter(t => t.type === 'debit')
    .sort((a, b) => b.amount - a.amount);

  if (debitTransactions.length === 0) {
    return (
       <div className="analytics-container">
        <h2>Spending Analytics</h2>
        <p className="info-message">No spending transactions found in this statement.</p>
      </div>
    )
  }

  // Group transactions into Top 4 and 'Others'
  const topItems = debitTransactions.slice(0, 4);
  const otherItems = debitTransactions.slice(4);
  const otherItemsSum = otherItems.reduce((sum, t) => sum + t.amount, 0);

  let chartItems = [...topItems];
  if (otherItems.length > 0) {
    chartItems.push({ description: 'Others', amount: otherItemsSum });
  }
  
  const totalSpent = debitTransactions.reduce((sum, t) => sum + t.amount, 0);

  const chartData = {
    labels: chartItems.map(item => item.description),
    datasets: [
      {
        data: chartItems.map(item => item.amount),
        backgroundColor: [
          '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
        ],
        hoverBackgroundColor: [
          '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
        ],
        borderColor: '#ffffff',
        borderWidth: 4,
        hoverBorderWidth: 4,
      },
    ],
  };

  const chartOptions = {
    cutout: '70%', // This creates the donut hole
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function (context) {
            let label = context.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed !== null) {
              label += new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
              }).format(context.parsed);
            }
            return label;
          },
        },
      },
    },
    maintainAspectRatio: false,
  };

  // Custom plugin to draw text in the center
  const centerTextPlugin = {
    id: 'centerText',
    beforeDraw: (chart) => {
      const { ctx, width, height } = chart;
      ctx.restore();
      const fontSize = (height / 114).toFixed(2);
      ctx.font = `bold ${fontSize}em sans-serif`;
      ctx.textBaseline = 'middle';

      const text = `₹${totalSpent.toLocaleString('en-IN')}`;
      const textX = Math.round((width - ctx.measureText(text).width) / 2);
      const textY = height / 2;
      
      ctx.fillStyle = '#2c3e50';
      ctx.fillText(text, textX, textY);
      ctx.save();
    },
  };

  return (
    <div className="analytics-container">
      <h2>Spending Analytics</h2>
      <div className="donut-chart-container">
        <div className="chart-wrapper">
          <Doughnut data={chartData} options={chartOptions} plugins={[centerTextPlugin]} />
        </div>
        <div className="legend-wrapper">
          {chartItems.map((item, index) => {
            const percentage = ((item.amount / totalSpent) * 100).toFixed(1);
            return (
              <div key={index} className="legend-item">
                <div className="legend-color" style={{ backgroundColor: chartData.datasets[0].backgroundColor[index] }}></div>
                <div className="legend-label">
                  <span className="description">{item.description}</span>
                  <span className="amount">₹{item.amount.toLocaleString('en-IN')}</span>
                </div>
                <div className="legend-percentage">{percentage}%</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default DonutAnalytics;