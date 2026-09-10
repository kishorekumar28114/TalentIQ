import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('job_matcher_token') || null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);

  // Synchronize axios default Authorization header
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('job_matcher_token', token);
      fetchCurrentUser();
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('job_matcher_token');
      setUser(null);
      setIsLoadingAuth(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      setIsLoadingAuth(true);
      const res = await axios.get('/api/auth/me');
      if (res.data) {
        setUser(res.data);
      }
    } catch (err) {
      console.warn('Session expired or invalid token:', err);
      logout();
    } finally {
      setIsLoadingAuth(false);
    }
  };

  const login = async (email, password) => {
    const res = await axios.post('/api/auth/login', { email, password });
    if (res.data && res.data.access_token) {
      setToken(res.data.access_token);
      setUser(res.data.user);
      return res.data.user;
    }
    throw new Error(res.data?.message || 'Login failed');
  };

  const register = async (fullName, email, password) => {
    const res = await axios.post('/api/auth/register', {
      full_name: fullName,
      email,
      password
    });
    if (res.data && res.data.access_token) {
      setToken(res.data.access_token);
      setUser(res.data.user);
      return res.data.user;
    }
    throw new Error(res.data?.message || 'Registration failed');
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    localStorage.removeItem('job_matcher_token');
  };

  const refreshUser = async () => {
    if (token) {
      await fetchCurrentUser();
    }
  };

  const unlinkResume = async () => {
    try {
      await axios.delete('/api/auth/resume');
      if (user) {
        setUser({ ...user, resume: null });
      }
    } catch (err) {
      console.error('Failed to unlink resume:', err);
      throw err;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoadingAuth,
        login,
        register,
        logout,
        refreshUser,
        unlinkResume,
        setUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
