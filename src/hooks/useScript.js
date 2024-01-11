import { useEffect, useRef } from 'react';

export default function useScript(
  url,
  { attributes, nodeId },
  dependencies = []
) {
  const script = useRef();

  useEffect(() => {
    const node = document.getElementById(nodeId) || document.head;
    script.current = document.createElement('script');
    if (url) {
      script.current.src = url;
      script.current.type = 'text/javascript';
      script.current.async = true;

      Object.entries(attributes).forEach(([key, value]) => {
        script.current[key] = value;
        script.current.setAttribute(key, value);
      });

      node?.appendChild(script.current);
    }

    return () => {
      const renderedNode = document.getElementById(nodeId);
      if (url)
        while (renderedNode?.firstChild)
          renderedNode?.removeChild(renderedNode?.firstChild);
    };
  }, [url, ...dependencies]);

  return script.current;
}
