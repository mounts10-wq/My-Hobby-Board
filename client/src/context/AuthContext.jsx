/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState } from "react";
import { apiRequest } from "../services/api";

const AuthContext = createContext();

const USER_STORAGE_KEY = "myhobbyboard_user";

function getStoredUser() {
  const rawUser = localStorage.getItem(USER_STORAGE_KEY);

  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser);
  } catch {
    localStorage.removeItem(USER_STORAGE_KEY);
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    async function checkCurrentUser() {
      const token = localStorage.getItem("token");

      if (!token) {
        setAuthLoading(false);
        return;
      }

      try {
        const data = await apiRequest("/me");
        setUser(data.user);
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user));
      } catch (error) {
        const authErrorStatuses = [401, 422];

        if (authErrorStatuses.includes(error?.status)) {
          localStorage.removeItem("token");
          localStorage.removeItem(USER_STORAGE_KEY);
          setUser(null);
        }
      } finally {
        setAuthLoading(false);
      }
    }

    checkCurrentUser();
  }, []);

  async function signup(formData) {
    const data = await apiRequest("/signup", {
      method: "POST",
      body: JSON.stringify(formData),
    });

    localStorage.setItem("token", data.access_token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user));
    setUser(data.user);

    return data;
  }

  async function login(formData) {
    const data = await apiRequest("/login", {
      method: "POST",
      body: JSON.stringify(formData),
    });

    localStorage.setItem("token", data.access_token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user));
    setUser(data.user);

    return data;
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem(USER_STORAGE_KEY);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        authLoading,
        signup,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}