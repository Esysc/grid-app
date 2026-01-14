import { useState, useEffect } from 'react';

/**
 * Custom hook for managing API mode toggle between REST and GraphQL
 * Persists preference in localStorage
 */
export function useApiToggle() {
  const [useGraphQL, setUseGraphQL] = useState(() => {
    // Load saved preference from localStorage
    const saved = localStorage.getItem('apiMode');
    return saved === 'graphql';
  });

  useEffect(() => {
    // Save preference to localStorage whenever it changes
    localStorage.setItem('apiMode', useGraphQL ? 'graphql' : 'rest');
  }, [useGraphQL]);

  const toggleApi = () => {
    setUseGraphQL(prev => !prev);
  };

  return {
    useGraphQL,
    toggleApi,
    apiMode: useGraphQL ? 'GraphQL' : 'REST'
  };
}
