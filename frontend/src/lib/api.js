// Shared API configuration and helpers.

// Empty means "same origin" (the production image serves the API and the SPA together).
export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
export const API = `${BACKEND_URL}/api`;

// Turn an axios error into a human-readable string. FastAPI returns `detail` as a
// string for HTTPException but as an array of objects for validation errors (422);
// passing that array straight to a toast crashes React.
export const getErrorMessage = (error, fallback = 'Something went wrong') => {
  const detail = error?.response?.data?.detail;

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        const field = Array.isArray(item?.loc)
          ? item.loc.filter((part) => part !== 'body' && part !== 'query').join('.')
          : '';
        const message = typeof item?.msg === 'string'
          ? item.msg.replace(/^Value error, /, '')
          : 'Invalid value';
        return field ? `${field}: ${message}` : message;
      })
      .join('; ');
  }

  if (error?.request && !error?.response) {
    return 'Unable to reach the server. Please check your connection and try again.';
  }

  return fallback;
};

// Resolve an uploaded file path (e.g. "/uploads/x.jpg") to a full URL.
export const assetUrl = (path) => {
  if (!path) return '';
  return path.startsWith('http') ? path : `${BACKEND_URL}${path}`;
};
