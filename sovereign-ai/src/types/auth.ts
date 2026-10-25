export type ClearanceLevel = 'Level 1 (Operator)' | 'Level 2 (Inspection & NDT)' | 'Level 3 (Root Sovereign Admin)';

export interface EmployeeUser {
  id: string;
  employeeId: string;
  name: string;
  fullName: string;
  role: string;
  department: string;
  clearance: ClearanceLevel;
  clearanceCode: 'L3' | 'L2' | 'L1';
  initials: string;
  badgeColor: string;
  password?: string;
}

export interface LocalUser {
  id?: number | string;
  username: string;
  name: string;
  fullName: string;
  employeeId?: string;
  role: string;
  department: string;
  clearance: ClearanceLevel;
  clearanceCode: 'L3' | 'L2' | 'L1';
  initials: string;
  badgeColor: string;
  createdAt?: string;
}

export interface AuthContextType {
  currentUser: LocalUser | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (username: string, password: string, displayName?: string) => Promise<{ success: boolean; error?: string }>;
  checkAuthStatus: () => Promise<{ has_users: boolean }>;
  logout: () => void;
}
