import { useCallback, useRef, useState } from 'react';

export default function useRefWithCallback(callback) {
  const ref = useRef();
  const [toggle, setToggle] = useState(false);

  const refCallback = useCallback((node) => {
    ref.current = node;
    setToggle((val) => !val);
    if (node) callback(node);
  }, []);

  return { toggle, refCallback, ref };
}
