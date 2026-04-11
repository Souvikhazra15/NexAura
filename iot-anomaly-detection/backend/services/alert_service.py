"""
Real-time alert generation service for anomaly detection
Generates critical and warning alerts based on signal thresholds
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AlertService:
    """Service to generate alerts from sensor data based on thresholds"""
    
    def __init__(self):
        # Load anomaly thresholds
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'anomaly_thresholds.json')
        try:
            with open(config_path, 'r') as f:
                self.thresholds = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load thresholds: {e}")
            self.thresholds = {}
    
    def check_signal_value(self, signal_name: str, value: float) -> Dict[str, Any]:
        """
        Check if a signal value is within normal, warning, or critical range
        
        Args:
            signal_name: Name of the signal (e.g., 'temperature', 'vibration_level')
            value: Current value of the signal
            
        Returns:
            Dict with severity level and details
        """
        # Normalize signal name (convert from CamelCase or spaces to snake_case)
        normalized = signal_name.lower().replace(' ', '_').replace('-', '_')
        
        if normalized not in self.thresholds:
            return {'severity': 'unknown', 'message': f'No threshold for {signal_name}'}
        
        threshold = self.thresholds[normalized]
        critical = threshold['critical']
        warning = threshold['warning']
        
        # Check severity
        if value < critical['min'] or value > critical['max']:
            return {
                'severity': 'critical',
                'signal': signal_name,
                'value': value,
                'threshold': critical,
                'message': f'{signal_name.title()} at {value:.2f} - CRITICAL! Threshold: {critical}',
                'anomaly_type': 'out_of_critical_range'
            }
        elif value < warning['min'] or value > warning['max']:
            return {
                'severity': 'warning',
                'signal': signal_name,
                'value': value,
                'threshold': warning,
                'message': f'{signal_name.title()} at {value:.2f} - WARNING! Threshold: {warning}',
                'anomaly_type': 'out_of_warning_range'
            }
        else:
            return {
                'severity': 'normal',
                'signal': signal_name,
                'value': value,
                'message': f'{signal_name.title()} at {value:.2f} - Normal'
            }
    
    def check_multiple_signals(self, signals: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Check multiple signal values and return all critical/warning alerts
        
        Args:
            signals: Dictionary of signal_name -> value
            
        Returns:
            List of alert objects (only critical and warning, not normal)
        """
        alerts = []
        for signal_name, value in signals.items():
            if value is None or (isinstance(value, float) and (value != value)):  # Skip NaN
                continue
            
            check_result = self.check_signal_value(signal_name, float(value))
            
            # Only include critical and warning alerts
            if check_result['severity'] in ['critical', 'warning']:
                alert = {
                    'id': f"{signal_name}_{datetime.now().isoformat()}",
                    'timestamp': datetime.now().isoformat(),
                    'severity': check_result['severity'],
                    'signal': signal_name,
                    'value': value,
                    'message': check_result['message'],
                    'score': 0.9 if check_result['severity'] == 'critical' else 0.6,
                    'anomaly_type': check_result.get('anomaly_type', 'threshold_breach'),
                    'contributing_signals': [{
                        'signal': signal_name,
                        'importance': 1.0
                    }],
                    'suggested_action': self.get_suggested_action(
                        signal_name, 
                        check_result['severity'],
                        value,
                        check_result['threshold']
                    )
                }
                alerts.append(alert)
        
        return alerts
    
    def get_suggested_action(self, signal_name: str, severity: str, 
                           value: float, threshold: Dict) -> str:
        """Get remediation suggestions based on signal and severity"""
        
        actions = {
            'temperature': {
                'critical': f'Temperature at {value:.1f}C is critical! Check cooling system, check for machinery overload.',
                'warning': f'Temperature at {value:.1f}C is elevated. Monitor cooling efficiency.'
            },
            'vibration_level': {
                'critical': f'Vibration at {value:.2f} is critical! Check for mechanical issues, bearing problems.',
                'warning': f'Vibration at {value:.2f} is elevated. Perform preventive maintenance check.'
            },
            'power_consumption': {
                'critical': f'Power consumption at {value:.1f}W is critical! Check for equipment faults.',
                'warning': f'Power consumption at {value:.1f}W is elevated. Review load distribution.'
            },
            'pressure': {
                'critical': f'Pressure at {value:.2f} bar is critical! Check pressure relief valve.',
                'warning': f'Pressure at {value:.2f} bar is elevated. Monitor system pressure levels.'
            },
            'material_flow_rate': {
                'critical': f'Flow rate at {value:.2f} is critical! Check for blockages, pump issues.',
                'warning': f'Flow rate at {value:.2f} is low. Check material supply.'
            },
            'cycle_time': {
                'critical': f'Cycle time at {value:.1f}s is critical! Process is slowing dangerously.',
                'warning': f'Cycle time at {value:.1f}s is extended. Investigate process bottlenecks.'
            },
            'error_rate': {
                'critical': f'Error rate at {value:.2%} is critical! Quality issues detected.',
                'warning': f'Error rate at {value:.2%} is elevated. Review quality control.'
            }
        }
        
        return actions.get(signal_name, {}).get(severity, 
            f'{signal_name} at {value:.2f} requires attention. Current threshold: {threshold}')

# Global alert service instance
alert_service = AlertService()
