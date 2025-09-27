/**
 * Storage Cleanup Utility
 * 
 * Provides utilities for cleaning up corrupted or inconsistent persistent data
 * that may cause authentication issues or infinite loops.
 */

import { config } from "./config";

/**
 * Clear all authentication-related data from localStorage and sessionStorage
 * This can help resolve issues with corrupted authentication state
 */
export function clearAllAuthData(): void {
  const authConfig = config.getAuthConfig();
  
  // Clear from localStorage
  localStorage.removeItem(authConfig.tokenStorageKey);
  localStorage.removeItem(authConfig.userStorageKey);
  
  // Clear from sessionStorage
  sessionStorage.removeItem(authConfig.tokenStorageKey);
  sessionStorage.removeItem(authConfig.userStorageKey);
  
  // Clear any legacy hardcoded keys that might exist
  localStorage.removeItem('authToken');
  localStorage.removeItem('authUser');
  sessionStorage.removeItem('authToken');
  sessionStorage.removeItem('authUser');
  
  console.log('🧹 Cleared all authentication data from storage');
}

/**
 * Clear all session-related data
 */
export function clearAllSessionData(): void {
  // Clear authentication data
  clearAllAuthData();
  
  // Clear any other session-related data
  localStorage.removeItem('currentSession');
  localStorage.removeItem('sessionId');
  sessionStorage.removeItem('currentSession');
  sessionStorage.removeItem('sessionId');
  
  console.log('🧹 Cleared all session data from storage');
}

/**
 * Check for inconsistent authentication data
 * Returns true if there are potential issues
 */
export function hasInconsistentAuthData(): boolean {
  const authConfig = config.getAuthConfig();
  
  // Check if both config-based and hardcoded keys exist
  const configToken = localStorage.getItem(authConfig.tokenStorageKey);
  const configUser = localStorage.getItem(authConfig.userStorageKey);
  const hardcodedToken = localStorage.getItem('authToken');
  const hardcodedUser = localStorage.getItem('authUser');
  
  // If config keys are the same as hardcoded keys, there's no inconsistency
  const configUsesHardcodedKeys = authConfig.tokenStorageKey === 'authToken' && authConfig.userStorageKey === 'authUser';
  
  if (configUsesHardcodedKeys) {
    // No inconsistency if config is using the same keys as hardcoded
    return false;
  }
  
  const hasConfigData = !!(configToken || configUser);
  const hasHardcodedData = !!(hardcodedToken || hardcodedUser);
  
  // Inconsistent if we have data in both formats or only in hardcoded format
  return hasConfigData && hasHardcodedData || (!hasConfigData && hasHardcodedData);
}

/**
 * Migrate hardcoded auth data to config-based keys
 * This helps fix legacy data issues
 */
export function migrateAuthData(): void {
  const authConfig = config.getAuthConfig();
  
  // Check if we have hardcoded data but no config-based data
  const configToken = localStorage.getItem(authConfig.tokenStorageKey);
  const hardcodedToken = localStorage.getItem('authToken');
  const hardcodedUser = localStorage.getItem('authUser');
  
  if (!configToken && hardcodedToken) {
    // Migrate hardcoded data to config-based keys
    localStorage.setItem(authConfig.tokenStorageKey, hardcodedToken);
    if (hardcodedUser) {
      localStorage.setItem(authConfig.userStorageKey, hardcodedUser);
    }
    
    // Remove hardcoded data
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('authUser');
    
    console.log('🔄 Migrated hardcoded auth data to config-based keys');
  }
}

/**
 * Perform a complete storage cleanup and migration
 * Call this if you're experiencing authentication issues
 */
export function performStorageCleanup(): void {
  console.log('🧹 Starting storage cleanup...');
  
  // Check for inconsistencies
  if (hasInconsistentAuthData()) {
    console.log('⚠️ Found inconsistent authentication data');
    
    // Try migration first
    migrateAuthData();
    
    // If still inconsistent, clear everything
    if (hasInconsistentAuthData()) {
      console.log('🧹 Clearing all data due to persistent inconsistencies');
      clearAllAuthData();
    }
  }
  
  console.log('✅ Storage cleanup completed');
}

/**
 * Add a global function for debugging
 * Call window.clearAuthData() in browser console if needed
 */
if (typeof window !== 'undefined') {
  (window as any).clearAuthData = clearAllAuthData;
  (window as any).clearSessionData = clearAllSessionData;
  (window as any).performStorageCleanup = performStorageCleanup;
  (window as any).checkAuthData = hasInconsistentAuthData;
}
