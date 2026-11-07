import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "AIzaSyCbB7nTLYYfaJ6tPOfCHuERxaC5uBwhCF4",
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "sanyuth-dc2d5.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "sanyuth-dc2d5",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "sanyuth-dc2d5.firebasestorage.app",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "219053408708",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "1:219053408708:web:34af0147e258f81931a491"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

export const signInWithGoogle = async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    return result.user;
  } catch (error) {
    if (error.code === 'auth/popup-blocked') {
      console.warn('Popup blocked, falling back to redirect...');
      await signInWithRedirect(auth, googleProvider);
      return null;
    }
    console.error('Google Sign-In Error:', error);
    throw error;
  }
};

export const checkRedirectResult = async () => {
  try {
    const result = await getRedirectResult(auth);
    return result ? result.user : null;
  } catch (error) {
    console.error('Redirect sign-in error:', error);
    return null;
  }
};
