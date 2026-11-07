// Shared API configuration and helpers.

// In production (live deployment), always use same-origin relative URL ('')
// so requests route through the deployed domain over HTTPS without Mixed Content errors.
const isLocalhost = typeof window !== 'undefined' && (
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1'
);

export const BACKEND_URL = isLocalhost
  ? (process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000')
  : '';
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

  if (error?.code === 'auth/unauthorized-domain') {
    return 'Domain unauthorized: please add this domain to Firebase Console > Authentication > Settings > Authorized domains.';
  }

  if (error?.code === 'auth/popup-blocked') {
    return 'Pop-up was blocked by your browser. Please allow pop-ups for this site in your address bar or follow the Google redirect.';
  }

  if (error?.code === 'auth/popup-closed-by-user') {

    return 'Sign-in was cancelled.';
  }

  if (error?.request && !error?.response) {
    return 'Unable to reach the server. Please check your connection and try again.';
  }

  if (typeof error?.message === 'string' && error.message && !error?.response) {
    return error.message;
  }

  return fallback;
};


// Resolve an uploaded file path (e.g. "/uploads/x.jpg") to a full URL.
export const assetUrl = (path) => {
  if (!path) return '';
  return path.startsWith('http') ? path : `${BACKEND_URL}${path}`;
};
