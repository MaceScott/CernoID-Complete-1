export type AccessLevel = 'free' | 'restricted' | 'high-security';

export interface TimeSlot {
    start: string; // HH:mm format
    end: string;   // HH:mm format
    days: number[]; // 0-6 for Sunday-Saturday
}

export interface ZoneAccess {
    zoneId: string;
    name: string;
    description: string;
    accessLevel: AccessLevel;
    allowedTimeSlots: TimeSlot[];
    restrictedTimeSlots: TimeSlot[];
    highSecurityTimeSlots: TimeSlot[];
    allowedRoles: string[];
    maxOccupancy?: number;
    currentOccupancy?: number;
}

export interface AccessAlert {
    id: string;
    timestamp: string;
    type: 'unauthorized' | 'restricted' | 'high-security';
    zoneId: string;
    userId: string;
    userName: string;
    details: {
        attemptedAccess: string;
        currentTime: string;
        allowedTimeSlots: TimeSlot[];
        userRole: string;
        userAccessLevel: number;
    };
    status: 'active' | 'resolved' | 'dismissed';
    resolvedBy?: string;
    resolvedAt?: string;
}

export interface AccessLog {
    id: string;
    timestamp: string;
    userId: string;
    userName: string;
    zoneId: string;
    zoneName: string;
    action: 'enter' | 'exit' | 'denied';
    accessLevel: AccessLevel;
    details: {
        timeSlot: TimeSlot;
        userRole: string;
        userAccessLevel: number;
    };
} 