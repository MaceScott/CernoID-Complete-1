// Component-specific settings types
export interface SettingsFormData {
  theme: 'light' | 'dark';
  language: string;
  notifications: {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
  };
}

export interface SettingsContextType {
  settings: SettingsFormData;
  updateSettings: (newSettings: Partial<SettingsFormData>) => void;
  resetSettings: () => void;
} 