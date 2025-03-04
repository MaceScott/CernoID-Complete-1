"""
Door access control system database schema
"""
from typing import Dict
from datetime import datetime

async def upgrade(session) -> None:
    """Create door access control tables"""
    
    # Create door configurations table
    await session.execute("""
        CREATE TABLE IF NOT EXISTS door_configs (
            door_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(20) NOT NULL,
            controller_ip VARCHAR(15) NOT NULL,
            controller_port INTEGER NOT NULL,
            zone_id INTEGER NOT NULL REFERENCES zones(id),
            emergency_unlock BOOLEAN DEFAULT false,
            auto_close_delay INTEGER DEFAULT 5,
            requires_confirmation BOOLEAN DEFAULT false,
            active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create access logs table
    await session.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id SERIAL PRIMARY KEY,
            door_id VARCHAR(50) REFERENCES door_configs(door_id),
            user_id INTEGER REFERENCES users(id),
            granted BOOLEAN NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            details JSONB
        )
    """)
    
    # Create user notifications preferences table
    await session.execute("""
        CREATE TABLE IF NOT EXISTS user_notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            zone_id INTEGER REFERENCES zones(id),
            notify_access BOOLEAN DEFAULT true,
            notify_denied BOOLEAN DEFAULT true,
            notify_emergency BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, zone_id)
        )
    """)
    
    # Create indexes
    await session.execute("""
        CREATE INDEX idx_access_logs_door_id ON access_logs(door_id);
        CREATE INDEX idx_access_logs_user_id ON access_logs(user_id);
        CREATE INDEX idx_access_logs_timestamp ON access_logs(timestamp);
        CREATE INDEX idx_door_configs_zone_id ON door_configs(zone_id);
        CREATE INDEX idx_user_notifications_user_zone ON user_notifications(user_id, zone_id);
    """)

async def downgrade(session) -> None:
    """Remove door access control tables"""
    
    # Drop tables in reverse order
    await session.execute("DROP TABLE IF EXISTS user_notifications")
    await session.execute("DROP TABLE IF EXISTS access_logs")
    await session.execute("DROP TABLE IF EXISTS door_configs") 