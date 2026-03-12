import React from 'react';

import Box from '@mui/material/Box';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import { VariableSizeList } from 'react-window';

function renderRow(props) {
  const { index, style } = props;

  return (
    <ListItem style={style} key={index} component="div" disablePadding>
      <ListItemButton>
        <ListItemText primary={`Item ${index + 1}`} />
      </ListItemButton>
    </ListItem>
  );
}

export default function VirtualizedList({ items }) {
  return (
    <Box sx={{ width: '100%', height: '100%' }}>
      <VariableSizeList
        height={window.innerHeight * 0.75}
        width="100%"
        itemSize={(index) => 40}
        itemCount={items.length}
        // overscanCount={5}
      >
        {renderRow}
      </VariableSizeList>
    </Box>
  );
}
