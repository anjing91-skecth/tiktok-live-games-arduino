"""
Arduino Stage Management System
==============================

Handles stage progression, validation, and timer management.
Extracted from arduino_tab.py for better maintainability.
"""

from typing import Dict, Any, Optional
import time
from datetime import datetime


class ArduinoStageManager:
    """Manages Arduino stage progression and validation"""
    
    def __init__(self, log_callback=None):
        """Initialize stage manager"""
        self.log_message = log_callback or print
        
        # Default stage configuration
        self.stages_config = {
            1: {'active': True, 'viewer_min': 0, 'delay': 0, 'retention': 0, 'bonus': 0},
            2: {'active': False, 'viewer_min': 30, 'delay': 5, 'retention': 5, 'bonus': 20},
            3: {'active': False, 'viewer_min': 80, 'delay': 10, 'retention': 10, 'bonus': 50}
        }
        
        # Stage progression state
        self.current_stage = 1
        self.manual_stage_override = False
        self.manual_locked_stage = None
        self.last_auto_stage = 1
        
        # Timer system
        self.stage_timer_active = False
        self.stage_timer_target = None
        self.stage_timer_start_time = None
        self.stage_timer_duration = 0
        
        # Retention tracking
        self.last_retention_check = {}
    
    def validate_stage_settings(self, stage_num: int, viewer_min: int, retention: int) -> Optional[str]:
        """Validate stage settings with +10 buffer requirement"""
        try:
            # Check against lower stages - WITH +10 BUFFER REQUIREMENT
            if stage_num == 2:
                # Stage 2 must be > Stage 1 + retention + 10 buffer
                stage1_min = self.stages_config[1]['viewer_min']  # Always 0
                stage1_retention = self.stages_config[1]['retention']  # Always 0
                min_required = stage1_min + stage1_retention + 10  # +10 buffer
                if viewer_min <= min_required:
                    return f"❌ Stage 2 min viewers must be > {min_required} (Stage 1 min + retention + 10 buffer)"
                    
            elif stage_num == 3:
                # Stage 3 must be > Stage 2 min + retention + 10 buffer
                stage2_min = self.stages_config[2]['viewer_min']
                stage2_retention = self.stages_config[2]['retention']
                min_required = stage2_min + stage2_retention + 10  # +10 buffer
                
                if viewer_min <= min_required:
                    return f"❌ Stage 3 min viewers must be > {min_required} (Stage 2: {stage2_min} + retention: {stage2_retention} + 10 buffer)"
            
            # Validate retention cannot be >= min_viewers (logical)
            if retention >= viewer_min and viewer_min > 0:
                return f"❌ Retention ({retention}) must be < Min viewers ({viewer_min})"
            
            return None  # No validation error
            
        except Exception:
            return "❌ Validation error occurred"
    
    def update_stage_config(self, stage_num: int, config: Dict[str, Any]) -> bool:
        """Update stage configuration"""
        try:
            if stage_num in self.stages_config:
                # Validate before updating
                validation_error = self.validate_stage_settings(
                    stage_num, 
                    config.get('viewer_min', 0), 
                    config.get('retention', 0)
                )
                
                if validation_error:
                    self.log_message(validation_error)
                    return False
                    
                self.stages_config[stage_num].update(config)
                self.log_message(f"✅ Stage {stage_num} configuration updated")
                return True
            else:
                self.log_message(f"❌ Invalid stage number: {stage_num}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error updating stage config: {e}")
            return False
    
    def check_stage_progression(self, current_viewers: int) -> Optional[int]:
        """Check if stage should change based on viewer count"""
        if self.manual_stage_override:
            return None
            
        # Check if current stage is disabled - auto fallback
        current_config = self.stages_config[self.current_stage]
        if not current_config['active']:
            fallback_stage = self.get_highest_enabled_stage()
            if fallback_stage != self.current_stage:
                self.log_message(f"🔄 Auto fallback: Stage {self.current_stage} disabled, moving to Stage {fallback_stage}")
                return fallback_stage
            
        # Check for stage progression UP
        for stage_num in [3, 2]:  # Check highest to lowest
            config = self.stages_config[stage_num]
            
            if (config['active'] and 
                current_viewers >= config['viewer_min'] and 
                stage_num > self.current_stage):
                
                return stage_num
        
        # Check for stage progression DOWN
        current_config = self.stages_config[self.current_stage]
        if (current_viewers < current_config['viewer_min'] and 
            self.current_stage > 1):
            
            # Find appropriate lower stage
            for stage_num in [1, 2]:
                config = self.stages_config[stage_num]
                if config['active'] and current_viewers >= config['viewer_min']:
                    return stage_num
            
            return 1  # Default to stage 1
        
        return None  # No change needed
    
    def get_highest_enabled_stage(self) -> int:
        """Get the highest enabled stage number"""
        for stage_num in [3, 2, 1]:  # Check from highest to lowest
            if self.stages_config[stage_num]['active']:
                return stage_num
        return 1  # Stage 1 is always fallback
    
    def check_retention_triggers(self, current_viewers: int, current_stage: int) -> Dict[str, Any]:
        """Check retention boundary triggers"""
        config = self.stages_config[current_stage]
        retention = config['retention']
        min_viewers = config['viewer_min']
        
        # Calculate retention boundaries
        upper_boundary = min_viewers + retention
        lower_boundary = min_viewers - retention
        
        result = {
            'trigger': False,
            'direction': None,
            'boundary': None,
            'action': None
        }
        
        # Check upper boundary (instant progression up)
        if current_viewers >= upper_boundary and current_stage < 3:
            next_stage = current_stage + 1
            if self.stages_config[next_stage]['active']:
                result.update({
                    'trigger': True,
                    'direction': 'up',
                    'boundary': upper_boundary,
                    'action': f'instant_stage_{next_stage}'
                })
        
        # Check lower boundary (instant progression down)
        elif current_viewers <= lower_boundary and current_stage > 1:
            prev_stage = current_stage - 1
            result.update({
                'trigger': True,
                'direction': 'down',
                'boundary': lower_boundary,
                'action': f'instant_stage_{prev_stage}'
            })
        
        return result
    
    def start_stage_timer(self, target_stage: int, delay_seconds: int):
        """Start stage progression timer"""
        self.stage_timer_active = True
        self.stage_timer_target = target_stage
        self.stage_timer_start_time = time.time()
        self.stage_timer_duration = delay_seconds
        
        self.log_message(f"⏰ Stage timer started: {delay_seconds}s to Stage {target_stage}")
    
    def cancel_stage_timer(self):
        """Cancel active stage timer"""
        if self.stage_timer_active:
            self.stage_timer_active = False
            self.stage_timer_target = None
            self.stage_timer_start_time = None
            self.log_message("❌ Stage timer cancelled")
    
    def check_stage_timer_completion(self) -> Optional[int]:
        """Check if stage timer is complete"""
        if not self.stage_timer_active or self.stage_timer_start_time is None:
            return None
            
        elapsed = time.time() - self.stage_timer_start_time
        
        if elapsed >= self.stage_timer_duration:
            target_stage = self.stage_timer_target
            self.stage_timer_active = False
            self.stage_timer_target = None
            self.stage_timer_start_time = None
            
            self.log_message(f"⏰ Stage timer completed: Moving to Stage {target_stage}")
            return target_stage
            
        return None
    
    def get_stage_info(self) -> Dict[str, Any]:
        """Get current stage information"""
        return {
            'current_stage': self.current_stage,
            'manual_override': self.manual_stage_override,
            'timer_active': self.stage_timer_active,
            'timer_target': self.stage_timer_target,
            'timer_remaining': (
                self.stage_timer_duration - (time.time() - self.stage_timer_start_time)
                if self.stage_timer_active and self.stage_timer_start_time is not None else 0
            ),
            'stages_config': self.stages_config.copy()
        }
    
    def set_current_stage(self, stage_num: int, manual: bool = False):
        """Set current stage"""
        self.current_stage = stage_num
        if manual:
            self.manual_stage_override = True
        else:
            self.last_auto_stage = stage_num
            
        self.log_message(f"🎯 Stage set to {stage_num} ({'Manual' if manual else 'Auto'})")
    
    def reset_to_auto_mode(self):
        """Reset to automatic stage management"""
        self.manual_stage_override = False
        self.manual_locked_stage = None
        self.cancel_stage_timer()
        self.log_message("🔄 Stage management reset to automatic mode")
    
    def validate_stage_dependencies(self, stage_num: int, enable: bool) -> Optional[str]:
        """Validate stage enable/disable dependencies"""
        try:
            if stage_num == 1:
                if not enable:
                    return "❌ Stage 1 cannot be disabled (always required)"
            
            elif stage_num == 2:
                if not enable:
                    # If Stage 2 disabled, Stage 3 must be disabled
                    if self.stages_config[3]['active']:
                        return "⚠️ Disabling Stage 2 will also disable Stage 3"
            
            elif stage_num == 3:
                if enable:
                    # Stage 3 can only be enabled if Stage 2 is enabled
                    if not self.stages_config[2]['active']:
                        return "❌ Stage 3 cannot be enabled unless Stage 2 is enabled"
            
            return None  # No validation error
            
        except Exception as e:
            return f"❌ Validation error: {e}"
    
    def update_stage_enable_with_dependencies(self, stage_num: int, enable: bool) -> Dict[str, Any]:
        """Update stage enable status with dependency cascade"""
        result = {
            'success': False,
            'changes': [],
            'warnings': []
        }
        
        try:
            # Validate the change
            validation_error = self.validate_stage_dependencies(stage_num, enable)
            if validation_error and not validation_error.startswith("⚠️"):
                result['warnings'].append(validation_error)
                return result
            
            # Stage 1 is always enabled
            if stage_num == 1:
                self.stages_config[1]['active'] = True
                result['changes'].append("Stage 1 kept enabled (always required)")
                result['success'] = True
                return result
            
            # Update the requested stage
            self.stages_config[stage_num]['active'] = enable
            result['changes'].append(f"Stage {stage_num} {'enabled' if enable else 'disabled'}")
            
            # Handle cascading dependencies
            if stage_num == 2 and not enable:
                # Disable Stage 3 if Stage 2 is disabled
                if self.stages_config[3]['active']:
                    self.stages_config[3]['active'] = False
                    result['changes'].append("Stage 3 auto-disabled (dependency)")
                    
                # If currently in manual mode on Stage 3, reset to auto
                if self.manual_stage_override and self.manual_locked_stage == 3:
                    self.reset_to_auto_mode()
                    result['changes'].append("Reset to auto mode (Stage 3 disabled)")
            
            # Auto fallback if current stage becomes disabled
            if not enable and self.current_stage == stage_num:
                if not self.manual_stage_override:
                    fallback_stage = self.get_highest_enabled_stage()
                    if fallback_stage != stage_num:
                        self.current_stage = fallback_stage
                        result['changes'].append(f"Auto fallback to Stage {fallback_stage}")
                else:
                    # In manual mode, fallback to highest enabled stage
                    fallback_stage = self.get_highest_enabled_stage()
                    if fallback_stage != stage_num:
                        self.current_stage = fallback_stage
                        self.manual_locked_stage = fallback_stage
                        result['changes'].append(f"Manual mode fallback to Stage {fallback_stage}")
            
            result['success'] = True
            self.log_message(f"✅ Stage dependencies updated: {', '.join(result['changes'])}")
            
        except Exception as e:
            result['warnings'].append(f"❌ Error updating dependencies: {e}")
        
        return result
    
    def set_manual_stage_override(self, target_stage: int) -> bool:
        """Set manual stage override to specific stage"""
        try:
            # Validate target stage is enabled
            if not self.stages_config[target_stage]['active']:
                self.log_message(f"❌ Cannot override to Stage {target_stage} - not enabled")
                return False
            
            # Set manual override
            self.manual_stage_override = True
            self.manual_locked_stage = target_stage
            self.current_stage = target_stage
            self.cancel_stage_timer()
            
            self.log_message(f"🔒 Manual override activated - locked to Stage {target_stage}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error setting manual override: {e}")
            return False
    
    def toggle_override_mode(self, selected_stage: int) -> Dict[str, Any]:
        """Toggle between auto and manual mode based on current state and selected stage"""
        result = {
            'success': False,
            'mode': 'auto',
            'stage': self.current_stage,
            'message': ''
        }
        
        try:
            if self.manual_stage_override:
                # Currently in manual mode
                if self.manual_locked_stage == selected_stage:
                    # Same stage selected - toggle back to auto
                    self.reset_to_auto_mode()
                    result.update({
                        'success': True,
                        'mode': 'auto',
                        'stage': self.current_stage,
                        'message': '🔄 Switched to AUTO mode'
                    })
                else:
                    # Different stage selected - switch to that stage
                    if self.set_manual_stage_override(selected_stage):
                        result.update({
                            'success': True,
                            'mode': 'manual',
                            'stage': selected_stage,
                            'message': f'🔒 Locked to Stage {selected_stage}'
                        })
            else:
                # Currently in auto mode - switch to manual with selected stage
                if self.set_manual_stage_override(selected_stage):
                    result.update({
                        'success': True,
                        'mode': 'manual',
                        'stage': selected_stage,
                        'message': f'🔒 Manual override - Stage {selected_stage}'
                    })
                    
        except Exception as e:
            result['message'] = f"❌ Error toggling override: {e}"
        
        return result
    
    def get_override_button_state(self, selected_stage: int) -> Dict[str, Any]:
        """Get current state for override button"""
        if self.manual_stage_override:
            if self.manual_locked_stage == selected_stage:
                return {
                    'text': '🔄 Auto Mode',
                    'tooltip': 'Click to return to automatic stage management',
                    'style': 'warning'
                }
            else:
                return {
                    'text': f'🔒 Lock Stage {selected_stage}',
                    'tooltip': f'Click to lock to Stage {selected_stage}',
                    'style': 'primary'
                }
        else:
            return {
                'text': f'🔒 Lock Stage {selected_stage}',
                'tooltip': f'Click to manually lock to Stage {selected_stage}',
                'style': 'primary'
            }
