// import React, {useEffect, useState, useRef, useCallback} from 'react';
// import Player from './Player';
// import Ball from './Ball';
// import '../cyberpunk-theme.css';
//
// const HockeyField = () => {
//   const [player1, setPlayer1] = useState({ x: 400, y: 150, r: 20 });
//   const [player2, setPlayer2] = useState({ x: 400, y: 450, r: 20 });
//   const [ball, setBall] = useState({ x: 400, y: 295, r: 10 });
//
//   const ws = useRef(null);
//
//   const updateState = useCallback((data) => {
//     setPlayer1({ x: data.player1.position[0], y: data.player1.position[1], r: data.player1.radius });
//     setPlayer2({ x: data.player2.position[0], y: data.player2.position[1], r: data.player2.radius });
//     setBall({ x: data.ball.position[0], y: data.ball.position[1], r: data.ball.radius });
//   }, []);
//
//   useEffect(() => {
//     ws.current = new WebSocket('ws://192.168.21.25:8080');
//
//     ws.current.onopen = () => {
//       const elem = document.getElementById("connection")
//       elem.innerText = 'WebSocket opened'
//       elem.style.color = "green"
//       console.log('WebSocket connection opened');
//     };
//
//     ws.current.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       console.log(data);
//       requestAnimationFrame(() => {
//         updateState(data);
//       });
//     };
//
//     ws.current.onclose = () => {
//       const elem = document.getElementById("connection")
//       elem.innerText = 'WebSocket closed'
//       elem.style.color = "red"
//       console.log('WebSocket connection closed');
//     };
//
//     return () => {
//       ws.current.close();
//     };
//   }, [updateState]);
//
//   useEffect(() => {
//     const handleKeyDown = (event) => {
//       const { key } = event;
//       let { x, y, r } = player1;
//
//       switch (key) {
//         case 'ArrowUp':
//           y -= 10;
//           break;
//         case 'ArrowDown':
//           y += 10;
//           break;
//         case 'ArrowLeft':
//           x -= 10;
//           break;
//         case 'ArrowRight':
//           x += 10;
//           break;
//         default:
//           break;
//       }
//
//       // Send player1 position to backend
//       if (ws.current && ws.current.readyState === WebSocket.OPEN) {
//         ws.current.send(JSON.stringify({ dx: (x - player1.x)/10, dy: (y - player1.y)/10 }));
//       }
//     };
//
//     window.addEventListener('keydown', handleKeyDown);
//
//     return () => {
//       window.removeEventListener('keydown', handleKeyDown);
//     };
//   }, [player1]);
//
//   return (
//       <>
//         <h1 className="main_text">React Hockey</h1>
//         <div id="connection"></div>
//         <div className="hockey-field">
//           <div className="line"
//                style={{background: "white", height: "1px", width: "100%", position: "absolute", top: "300px"}}></div>
//           <Player x={player1.x} y={player1.y} r={player1.r} isOpponent/>
//           <Player x={player2.x} y={player2.y} r={player2.r}/>
//           <Ball x={ball.x} y={ball.y} r={ball.r}/>
//         </div>
//       </>
//   );
// };
//
// export default HockeyField;


import React, { useEffect, useState, useRef, useCallback } from 'react';
import Player from './Player';
import Ball from './Ball';
import '../cyberpunk-theme.css';

const HockeyField = () => {
  const [player1, setPlayer1] = useState({ x: 400, y: 150, r: 20 });
  const [player2, setPlayer2] = useState({ x: 400, y: 450, r: 20 });
  const [ball, setBall] = useState({ x: 400, y: 295, r: 10 });

  const ws = useRef(null);
  const keysPressed = useRef({});

  const updateState = useCallback((data) => {
    setPlayer1({ x: data.player1.position[0], y: data.player1.position[1], r: data.player1.radius });
    setPlayer2({ x: data.player2.position[0], y: data.player2.position[1], r: data.player2.radius });
    setBall({ x: data.ball.position[0], y: data.ball.position[1], r: data.ball.radius });
  }, []);

  useEffect(() => {
    ws.current = new WebSocket('ws://192.168.21.25:8080');

    ws.current.onopen = () => {
      const elem = document.getElementById("connection");
      elem.innerText = 'WebSocket opened';
      elem.style.color = "green";
      console.log('WebSocket connection opened');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log(data);
      requestAnimationFrame(() => {
        updateState(data);
      });
    };

    ws.current.onclose = () => {
      const elem = document.getElementById("connection");
      elem.innerText = 'WebSocket closed';
      elem.style.color = "red";
      console.log('WebSocket connection closed');
    };

    return () => {
      ws.current.close();
    };
  }, [updateState]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      keysPressed.current[event.key] = true;
    };

    const handleKeyUp = (event) => {
      keysPressed.current[event.key] = false;
    };

    const movePlayer = () => {
      let { x, y } = player1;

      if (keysPressed.current['ArrowUp']) y = Math.max(y - 5, 0);
      if (keysPressed.current['ArrowDown']) y = Math.min(y + 5, 600); // Assuming the field height is 600
      if (keysPressed.current['ArrowLeft']) x = Math.max(x - 5, 0);
      if (keysPressed.current['ArrowRight']) x = Math.min(x + 5, 800); // Assuming the field width is 800

      // setPlayer1((prevState) => ({ ...prevState, x, y }));

      // Send player1 position to backend
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ dx: (x - player1.x) / 10, dy: (y - player1.y) / 10 }));
      }

      requestAnimationFrame(movePlayer);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    requestAnimationFrame(movePlayer);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [player1]);

  return (
    <>
      <h1 className="main_text">React Hockey</h1>
      <div id="connection"></div>
      <div className="hockey-field">
        <div className="line" style={{background: "white", height: "1px", width: "100%", position: "absolute", top: "300px"}}></div>
        <Player x={player1.x} y={player1.y} r={player1.r} isOpponent />
        <Player x={player2.x} y={player2.y} r={player2.r} />
        <Ball x={ball.x} y={ball.y} r={ball.r} />
      </div>
    </>
  );
};

export default HockeyField;