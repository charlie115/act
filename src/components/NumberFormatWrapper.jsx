import React, { forwardRef } from 'react';

import { NumericFormat } from 'react-number-format';

const NumberFormatWrapper = forwardRef(({ id, ...rest }, ref) => (
  <NumericFormat id={id} getInputRef={ref} {...rest} />
));

export default NumberFormatWrapper;
