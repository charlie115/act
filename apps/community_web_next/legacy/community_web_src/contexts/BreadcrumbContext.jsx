import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

const BreadcrumbContext = createContext({
  dynamicTitle: null,
  setDynamicTitle: () => {},
});

/**
 * BreadcrumbProvider - Provides context for dynamic breadcrumb titles
 *
 * Use this when you need to set a dynamic title for breadcrumbs,
 * such as a post title on dynamic route pages.
 */
export function BreadcrumbProvider({ children }) {
  const [dynamicTitle, setDynamicTitle] = useState(null);

  const updateTitle = useCallback((title) => {
    setDynamicTitle(title);
  }, []);

  const contextValue = useMemo(
    () => ({
      dynamicTitle,
      setDynamicTitle: updateTitle,
    }),
    [dynamicTitle, updateTitle]
  );

  return (
    <BreadcrumbContext.Provider value={contextValue}>
      {children}
    </BreadcrumbContext.Provider>
  );
}

/**
 * useBreadcrumbTitle - Hook to access and set dynamic breadcrumb title
 *
 * Usage in a page component:
 * const { setDynamicTitle } = useBreadcrumbTitle();
 *
 * useEffect(() => {
 *   if (post?.title) {
 *     setDynamicTitle(post.title);
 *   }
 *   return () => setDynamicTitle(null);
 * }, [post?.title, setDynamicTitle]);
 */
export const useBreadcrumbTitle = () => {
  const context = useContext(BreadcrumbContext);

  if (!context) {
    throw new Error('useBreadcrumbTitle must be used within a BreadcrumbProvider');
  }

  return context;
};

export default BreadcrumbContext;
