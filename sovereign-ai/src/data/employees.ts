import type { EmployeeUser } from '../types/auth';

export const VERIFIED_EMPLOYEES: EmployeeUser[] = [
  {
    id: 'deepak',
    employeeId: 'EMP-1042',
    name: 'Deepak',
    fullName: 'Deepak Sharma',
    role: 'Lead Mechanical Integrity Engineer',
    department: 'Refinery Pressure Equipment & Asset Integrity',
    clearance: 'Level 3 (Root Sovereign Admin)',
    clearanceCode: 'L3',
    initials: 'DS',
    badgeColor: 'linear-gradient(135deg, #2563EB, #0D9488)',
    password: 'deepak123',
  },
  {
    id: 'anish',
    employeeId: 'EMP-2088',
    name: 'Anish',
    fullName: 'Anish Varma',
    role: 'Senior Piping & Corrosion Specialist',
    department: 'Piping Systems & Non-Destructive Testing',
    clearance: 'Level 2 (Inspection & NDT)',
    clearanceCode: 'L2',
    initials: 'AV',
    badgeColor: 'linear-gradient(135deg, #7C3AED, #2563EB)',
    password: 'anish123',
  },
  {
    id: 'yash',
    employeeId: 'EMP-3315',
    name: 'Yash',
    fullName: 'Yash Patel',
    role: 'Reliability & Process Safety Engineer',
    department: 'Process Safety & Fitness-For-Service Diagnostics',
    clearance: 'Level 2 (Inspection & NDT)',
    clearanceCode: 'L2',
    initials: 'YP',
    badgeColor: 'linear-gradient(135deg, #059669, #0284C7)',
    password: 'yash123',
  },
];

export function findEmployee(identifier: string): EmployeeUser | undefined {
  const clean = identifier.trim().toLowerCase();
  return VERIFIED_EMPLOYEES.find(
    (e) =>
      e.id.toLowerCase() === clean ||
      e.employeeId.toLowerCase() === clean ||
      e.name.toLowerCase() === clean ||
      e.fullName.toLowerCase() === clean
  );
}
