import { useCallback, useLayoutEffect, useRef, useState } from 'react';

export default function useElementScroll(deps = []) {
  const ref = useRef();

  const [state, setState] = useState({
    x: null,
    y: null,
    height: null,
    width: null,
  });

  const scrollTo = useCallback((...args) => {
    if (typeof args[0] === 'object') ref?.current?.scrollTo(args[0]);
    else if (typeof args[0] === 'number' && typeof args[1] === 'number')
      ref?.current?.scrollTo(args[0], args[1]);
  }, []);

  useLayoutEffect(() => {
    const handleScroll = (e) => {
      setState({
        x: e?.target.scrollLeft,
        y: e?.target.scrollTop,
        height: e?.target.scrollHeight,
        width: e?.target.scrollWidth,
      });
    };
    handleScroll();
    ref?.current?.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      ref?.current?.removeEventListener('scroll', handleScroll);
    };
  }, [...deps]);

  return [ref, state, scrollTo];
}
