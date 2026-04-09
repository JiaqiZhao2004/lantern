import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyClesf_d5K35A28D2LaAil_PXPjSEOMT50",
  authDomain: "family-finance-d31cd.firebaseapp.com",
  projectId: "family-finance-d31cd",
  storageBucket: "family-finance-d31cd.firebasestorage.app",
  messagingSenderId: "3298189826",
  appId: "1:3298189826:web:0533230009376148a6fd1b",
  measurementId: "G-6V5DRHC199",
};

const app = initializeApp(firebaseConfig);
export const analytics = getAnalytics(app);
export const auth = getAuth(app);
