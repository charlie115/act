import React, { useEffect, useState } from 'react';

import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import TextField from '@mui/material/TextField';

import { useGetCoinsQuery } from 'redux/api/websocket';

export default function CoinsSelector() {
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState([]);

  const { data, isLoading } = useGetCoinsQuery();

  useEffect(() => {
    setOptions(data?.coins);
  }, [data]);

  return (
    <Autocomplete
      id="asynchronous-demo"
      open={open}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      isOptionEqualToValue={(option, value) => option.name === value.name}
      getOptionLabel={(option) => option.name}
      options={options}
      loading={isLoading}
      renderInput={(params) => (
        <TextField
          {...params}
          variant="standard"
          // label="Select Coin"
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {isLoading ? (
                  <CircularProgress color="inherit" size={20} />
                ) : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      renderOption={(props, option) => (
        <Box
          component="li"
          sx={{ '& > img': { mr: 2, flexShrink: 0 } }}
          {...props}
        >
          <img
            loading="lazy"
            width="20"
            // eslint-disable-next-line import/no-dynamic-require, global-require
            src={require(`assets/icons/coinicon/${option.name}.png`)}
            alt=""
          />
          {option.name}
        </Box>
      )}
      size="small"
      sx={{ mb: 2, width: 300 }}
    />
  );
}
