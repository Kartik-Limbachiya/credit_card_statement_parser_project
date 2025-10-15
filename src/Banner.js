// src/Banner.js

import React from 'react';
import './Banner.css';

const logos = [
  { name: 'Kotak', url: 'https://zerocreativity0.wordpress.com/wp-content/uploads/2016/05/kotak-logo.jpg?w=736' },
  { name: 'SBI', url: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhYRXE6uVI5pYMigHf_QpMYtLBobOMXs2kCg&s' },
  { name: 'Yes Bank', url: 'https://www.livemint.com/lm-img/img/2024/06/27/1600x900/YES_BANK_logo_1718090520171_1719461044556.jpg' },
  { name: 'Bank of Baroda', url: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT2La5Q_xYCFAJqeytE2pf6SsJAOuo9Pu5KZQ&s' },
  { name: 'Axis Bank', url: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRV-cq_bSdsBTQQEsGwA-QKFR_tu32wL1f0Yg&s' },
];

const Banner = () => {
  // We duplicate the logos to create a seamless loop
  const extendedLogos = [...logos, ...logos];

  return (
    <div className="banner-container">
      <div className="banner-track">
        {extendedLogos.map((logo, index) => (
          <div className="banner-item" key={index}>
            <img src={logo.url} alt={`${logo.name} logo`} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default Banner;