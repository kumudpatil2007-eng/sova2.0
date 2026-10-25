import React, { createContext, useContext, useState } from 'react';
import type { LocalUser, AuthContextType } from '../types/auth';
import { loginUser, registerLocalAccount, logoutUser, getAuthStatus } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to provide clean engineering profile metadata for local users
const USER_PROFILES: Record<string, Partial<LocalUser>> = {
  deepak: {
    fullName: 'Deepak Sharma',
    role: 'Lead Mechanical Integrity Engineer',
    department: 'Refinery Pressure Equipment & Asset Integrity',
    clearance: 'Level 3 (Root Sovereign Admin)',
    clearanceCode: 'L3',
    initials: 'DS',
    badgeColor: 'linear-gradient(135deg, #2563EB, #0D9488)',
  },
  anish: {
    fullName: 'Anish Varma',
    role: 'Senior Piping & Corrosion Specialist',
    department: 'Piping Systems & Non-Destructive Testing',
    clearance: 'Level 2 (Inspection & NDT)',
    clearanceCode: 'L2',
    initials: 'AV',
    badgeColor: 'linear-gradient(135deg, #7C3AED, #2563EB)',
  },
  yash: {
    fullName: 'Yash Patel',
    role: 'Reliability & Process Safety Engineer',
    department: 'Process Safety & Fitness-For-Service Diagnostics',
    clearance: 'Level 2 (Inspection & NDT)',
    clearanceCode: 'L2',
    initials: 'YP',
    badgeColor: 'linear-gradient(135deg, #059669, #0284C7)',
  },
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // CRITICAL REQUIREMENT (Section 5):
  // Every application start / page reload must begin LOCKED.
  // The first screen must always be the Lock Screen.
  // Even if a previous session existed, do not directly expose the workspace on reload.
  const [currentUser, setCurrentUser] = useState<LocalUser | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);

  const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
    const cleanUsername = username.trim().toLowerCase();
    if (!cleanUsername) {
      return { success: false, error: 'Please enter your username.' };
    }
    if (!password.trim()) {
      return { success: false, error: 'Password is required.' };
    }

    try {
      const res = await loginUser(cleanUsername, password);
      if (!res.success || !res.user) {
        return {
          success: false,
          error: res.error || 'Incorrect username or password.',
        };
      }

      const meta = USER_PROFILES[cleanUsername] || {};
      const initials = (meta.initials) || cleanUsername.slice(0, 2).toUpperCase();
      const displayName = res.user.display_name || meta.fullName || cleanUsername.toUpperCase();

      const userObj: LocalUser = {
        id: res.user.id,
        username: res.user.username,
        name: displayName.split(' ')[0],
        fullName: displayName,
        role: meta.role || 'Mechanical Integrity Engineer',
        department: meta.department || 'Refinery Asset Integrity & Plant Security',
        clearance: meta.clearance || 'Level 3 (Root Sovereign Admin)',
        clearanceCode: meta.clearanceCode || 'L3',
        initials,
        badgeColor: meta.badgeColor || 'linear-gradient(135deg, #2563EB, #0D9488)',
        createdAt: res.user.created_at,
      };

      setCurrentUser(userObj);
      if (res.token) {
        setSessionToken(res.token);
      }
      return { success: true };
    } catch {
      return {
        success: false,
        error: 'Incorrect username or password.',
      };
    }
  };

  const register = async (
    username: string,
    password: string,
    displayName?: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const res = await registerLocalAccount(username, password, displayName);
      if (!res.success) {
        return { success: false, error: res.error || 'Registration failed.' };
      }
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e.message || 'Registration failed.' };
    }
  };

  const checkAuthStatus = async () => {
    return getAuthStatus();
  };

  const logout = () => {
    if (sessionToken) {
      logoutUser(sessionToken);
    }
    // Clear authenticated state immediately and lock
    setCurrentUser(null);
    setSessionToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        isAuthenticated: !!currentUser,
        login,
        register,
        checkAuthStatus,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
