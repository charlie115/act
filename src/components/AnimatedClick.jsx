import React, { useState } from 'react';

import Box from '@mui/material/Box';

export default function AnimatedClick({
  animation,
  children,
  containerStyle,
  speed = 'faster',
  onClick,
}) {
  const [animate, setAnimate] = useState(false);

  return (
    <Box
      className={
        animate
          ? `animate__animated animate__${animation} animate__${speed}`
          : null
      }
      // onAnimationStart={() => onClick()}
      onAnimationEnd={() => {
        setAnimate(false);
        onClick();
      }}
      onClick={() => setAnimate(true)}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        ...containerStyle,
      }}
    >
      {children}
    </Box>
  );
}
