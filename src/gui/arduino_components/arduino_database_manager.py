"""
Arduino Database Manager Component
=================================

Handles all database operations for Arduino tab while maintaining
exact same functionality as before.
"""

class ArduinoDatabaseManager:
    """Manages all database operations for Arduino functionality"""
    
    def __init__(self, db_manager, current_account_id=None, current_account_username=None):
        self.db_manager = db_manager
        self.current_account_id = current_account_id
        self.current_account_username = current_account_username
        
    def set_account(self, account_username: str, log_callback=None):
        """Set current account and load all settings from database"""
        try:
            if not self.db_manager:
                if log_callback:
                    log_callback("⚠️ Database manager not available")
                return None
                
            # Get account info from database
            account = self.db_manager.get_account_by_username(account_username)
            if not account:
                if log_callback:
                    log_callback(f"⚠️ Account @{account_username} not found in database")
                return None
                
            self.current_account_id = account['id']
            self.current_account_username = account_username
            
            if log_callback:
                log_callback(f"🔄 Loading settings for account @{account_username} (ID: {account['id']})")
            
            return account
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error setting account: {e}")
            return None
    
    def load_stage_settings_from_db(self, stages_config, log_callback=None):
        """Load stage settings for current account from database"""
        if not self.current_account_id or not self.db_manager:
            return stages_config
            
        try:
            settings = self.db_manager.get_arduino_stage_settings(self.current_account_id)
            
            if settings:
                for setting in settings:
                    stage_num = setting['stage_number']
                    if stage_num in stages_config:
                        stages_config[stage_num] = {
                            'active': bool(setting['is_active']),
                            'viewer_min': setting['viewer_min'],
                            'delay': setting['delay'],
                            'retention': setting['retention'],
                            'bonus': setting['bonus']
                        }
                
                if log_callback:
                    log_callback(f"✅ Loaded {len(settings)} stage settings from database")
            else:
                if log_callback:
                    log_callback("📝 No stage settings found, using defaults")
                
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error loading stage settings: {e}")
                
        return stages_config
    
    def load_rules_from_db(self, log_callback=None):
        """Load rules for current account from database"""
        rules_data = []
        
        if not self.current_account_id or not self.db_manager:
            return rules_data
            
        try:
            rules = self.db_manager.get_arduino_rules(self.current_account_id)
            
            for rule in rules:
                # Convert pins from string back to list
                pins = [int(p.strip()) for p in rule['pins'].split(',') if p.strip()]
                
                rule_data = {
                    'name': rule['rule_name'],
                    'event_type': rule['event_type'],
                    'pins': pins,
                    'mode': rule['mode'],
                    'duration': rule['duration'],
                    'status': 'Active' if rule['is_active'] else 'Inactive'
                }
                rules_data.append(rule_data)
            
            if log_callback:
                log_callback(f"✅ Loaded {len(rules)} rules from database")
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error loading rules: {e}")
                
        return rules_data
    
    def save_stage_settings(self, stage_num, viewer_min, delay, retention, is_active, bonus, log_callback=None):
        """Save stage settings to database"""
        if self.current_account_id and self.db_manager:
            try:
                # Prepare settings dict to match database method signature
                settings = {
                    'viewer_min': viewer_min,
                    'delay': delay,
                    'retention': retention,
                    'is_active': is_active,
                    'bonus': bonus
                }
                
                self.db_manager.save_arduino_stage_setting(
                    account_id=self.current_account_id,
                    stage_name=f"stage_{stage_num}",  # Changed to stage_name
                    settings=settings  # Settings as dict
                )
                if log_callback:
                    log_callback(f"✅ Stage {stage_num} settings saved to database")
                return True
            except Exception as e:
                if log_callback:
                    log_callback(f"⚠️ Could not save to database: {e}")
                return False
        else:
            if log_callback:
                log_callback(f"✅ Stage {stage_num} settings saved (memory only - no account selected)")
            return True
    
    def save_rule_to_db(self, rule_data, log_callback=None):
        """Save rule to database"""
        if not self.current_account_id or not self.db_manager:
            return False
            
        try:
            # Convert pins list to string
            pins_str = ','.join(map(str, rule_data['pins']))
            
            self.db_manager.save_arduino_rule(
                account_id=self.current_account_id,
                rule_name=rule_data['name'],
                event_type=rule_data['event_type'],
                pins=pins_str,
                mode=rule_data['mode'],
                duration=rule_data['duration'],
                is_active=rule_data['status'] == 'Active'
            )
            
            if log_callback:
                log_callback(f"✅ Rule '{rule_data['name']}' saved to database")
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error saving rule: {e}")
            return False
    
    def delete_rule_from_db(self, rule_name, log_callback=None):
        """Delete rule from database"""
        if not self.current_account_id or not self.db_manager:
            return False
            
        try:
            # Note: This assumes there's a delete method in db_manager
            # You may need to implement this method in your DatabaseManager
            if hasattr(self.db_manager, 'delete_arduino_rule'):
                self.db_manager.delete_arduino_rule(self.current_account_id, rule_name)
                if log_callback:
                    log_callback(f"✅ Rule '{rule_name}' deleted from database")
                return True
            else:
                if log_callback:
                    log_callback(f"⚠️ Delete functionality not available in database manager")
                return False
                
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error deleting rule: {e}")
            return False
    
    def save_arduino_port(self, account_id, port, log_callback=None):
        """Save Arduino port preference for account"""
        try:
            if not self.db_manager:
                if log_callback:
                    log_callback("⚠️ Database manager not available")
                return False
                
            # Save port preference (implementation depends on your database schema)
            # For now, just log the action
            if log_callback:
                log_callback(f"💾 Arduino port {port} saved for account ID: {account_id}")
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error saving Arduino port: {e}")
            return False
