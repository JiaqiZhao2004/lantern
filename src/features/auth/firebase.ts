// firebase.ts
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyClesf_d5K35A28D2LaAil_PXPjSEOMT50",
  authDomain: "family-finance-d31cd.firebaseapp.com",
  projectId: "family-finance-d31cd",
  storageBucket: "family-finance-d31cd.firebasestorage.app",
  messagingSenderId: "3298189826",
  appId: "1:3298189826:web:0533230009376148a6fd1b",
  measurementId: "G-6V5DRHC199"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const analytics = getAnalytics(app);
export const auth = getAuth(app);
