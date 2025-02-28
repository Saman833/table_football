import React from 'react';
import '../cyberpunk-theme.css';

const Ball = ({ x, y, r }) => {
  return (
    <div
      className="ball"
      style={{ left: x - 5, top: y - 5, height: r * 2, width: r * 2 }}
    ></div>
  );
};

export default Ball;