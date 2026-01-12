export interface WorkEntry {
  id: string;
  date: string;
  startTime: string;
  endTime: string;
  minutes: number;
  description: string;
}

export interface EmailSettings {
  enabled: boolean;
  recipients: string[];
  subject: string;
  body: string;
  dayOfMonth: number
}

export interface Goal {
  id: string;
  name: string;
  description: string;
  targetHours: number;
  completedHours: number;
  hourlyRate: number;
  currency: string;
  startDate: string;
  endDate: string;
  workEntries: WorkEntry[];
  emailSettings: EmailSettings;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  timezone: string;
  currency: string;
  address: string;
  country: string;
  phone: string;
}
