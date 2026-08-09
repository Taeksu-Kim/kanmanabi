/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GOOGLE_CLIENT_ID?: string;
}

interface GoogleCredentialResponse {
  credential: string;
}

interface GoogleIdConfiguration {
  client_id: string;
  callback: (response: GoogleCredentialResponse) => void;
}

interface Window {
  google?: {
    accounts: {
      id: {
        initialize: (options: GoogleIdConfiguration) => void;
        renderButton: (
          parent: HTMLElement,
          options: { theme: "outline"; size: "large"; shape: "pill"; width: number; locale: string },
        ) => void;
      };
    };
  };
}
