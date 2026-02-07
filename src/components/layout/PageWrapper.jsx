import React from 'react';
import { Box } from '@mui/material';

export default function PageWrapper({ children }) {
  return (
    <Box sx={{
      maxWidth: '1920px',
      width: '100%',
      mx: 'auto',
      p: { xs: 2, md: 4 },
      boxSizing: 'border-box'
    }}>
      {children}
    </Box>
  );
}
