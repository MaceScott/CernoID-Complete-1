# Alert Settings
alert_preferences: Dict[str, Any] = {
    'enabled': True,
    'channels': ['EMAIL'],
    'minSeverity': 'MEDIUM',
    'quietHours': {
        'enabled': False,
        'start': '22:00',
        'end': '07:00'
    },
    'thresholds': {
        'cpu': 80,
        'memory': 80,
        'disk': 90,
        'network': 1000
    }
}

smtp_config: Dict[str, Any] = {
    'host': 'smtp.gmail.com',
    'port': 587,
    'username': '',
    'password': '',
    'from_email': '',
    'to_email': '',
    'use_tls': True
}