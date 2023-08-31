import { useEffect, useRef } from 'react';

export default function useExternalScript(
  url,
  options = {},
  dependencies = []
) {
  const script = useRef();

  const { attachToHeader = true, attributes = {}, onLoad } = options;

  useEffect(() => {
    const scriptLoadingPromise = new Promise((resolve) => {
      script.current = document.createElement('script');
      script.current.src = url;
      script.current.type = 'text/javascript';
      script.current.async = true;

      Object.entries(attributes).forEach(([key, value]) => {
        script.current[key] = value;
      });

      script.current.onload = resolve;

      if (attachToHeader) document.head.appendChild(script.current);
    });

    scriptLoadingPromise.then(() => {
      if (onLoad) onLoad();
    });
  }, [url, ...dependencies]);

  return script;
}
