import { useCallback, useRef, useState } from 'react';

export default function useRefWithCallback(callback, deps = []) {
  const ref = useRef();
  const [toggle, setToggle] = useState(false);

  const refCallback = useCallback(
    (node) => {
      ref.current = node;
      setToggle((val) => !val);
      if (node) callback(node);
    },
    [...deps]
  );

  return { toggle, refCallback, ref };
}
