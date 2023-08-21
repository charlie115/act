import { useEffect, useRef, useState } from 'react';

export default function useScript(url, options = {}, dependencies = []) {
  const {
    attachToHeader = true,
    containerRef = null,
    name = null,
    scriptAttributes = {},
  } = options;

  const [lib, setLib] = useState({});
  console.log('lib: ', lib);

  useEffect(() => {
    let script;

    const removeScript = () => {
      if (script)
        try {
          if (containerRef?.current) containerRef.current.removeChild(script);
        } catch (e) {
          while (containerRef?.current.firstChild) {
            containerRef.current.removeChild(containerRef.current.firstChild);
          }
        }
    };

    if (name && window[name]) {
      setLib({ [name]: window[name] });
    } else {
      const scriptLoadingPromise = new Promise((resolve) => {
        script = document.createElement('script');
        script.src = url;
        script.type = 'text/javascript';
        script.async = true;

        Object.entries(scriptAttributes).forEach(([key, value]) => {
          script[key] = value;
        });

        script.onload = resolve;

        if (!attachToHeader) {
          removeScript();
          containerRef?.current?.appendChild(script);
        } else document.head.appendChild(script);
      });

      scriptLoadingPromise.then(() => {
        if (name) setLib({ [name]: window[name] });
      });
    }

    return () => {
      if (!attachToHeader) removeScript();
    };
  }, [url, ...dependencies]);

  return lib[name] ?? null;
}
