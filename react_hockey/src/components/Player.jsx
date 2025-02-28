import React from 'react';
import '../cyberpunk-theme.css';

const Player = ({ x, y, r, isOpponent }) => {
  return (
    <div
      className={`player ${isOpponent ? 'opponent' : 'player1'}`}
      style={{ left: x - 10, top: y - 10, height: r * 2, width: r * 2 }}
    ></div>
  );
};

export default Player;