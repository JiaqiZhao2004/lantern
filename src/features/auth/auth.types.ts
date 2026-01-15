export type PhoneNumber = {
  countryCode: number;
  number: number;
};

export type User = {
  id: string;
  email: string;
  phone: PhoneNumber;
};

export type AuthState = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
};
