/**
 * Configuration management utility for the frontend application.
 * 
 * This module provides a centralized configuration system that loads settings
 * from environment variables with fallback defaults.
 */

// Configuration interfaces
export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

export interface WebSocketConfig {
  reconnectAttempts: number;
  reconnectDelay: number;
  heartbeatInterval: number;
  connectionTimeout: number;
}

export interface AuthConfig {
  tokenStorageKey: string;
  userStorageKey: string;
  tokenExpiryBuffer: number;
}

export interface UIConfig {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  autoSave: boolean;
  autoSaveInterval: number;
}

export interface FeaturesConfig {
  enableDebugMode: boolean;
  enableAnalytics: boolean;
  enableOfflineMode: boolean;
  enablePushNotifications: boolean;
}

export interface DevelopmentConfig {
  enableHotReload: boolean;
  enableSourceMaps: boolean;
  enableConsoleLogging: boolean;
}

export interface AppConfig {
  api: ApiConfig;
  websocket: WebSocketConfig;
  auth: AuthConfig;
  ui: UIConfig;
  features: FeaturesConfig;
  development: DevelopmentConfig;
}

// Environment variable interface
interface EnvironmentVariables {
  // API Configuration
  VITE_API_BASE_URL?: string;
  VITE_API_TIMEOUT?: string;
  VITE_API_RETRY_ATTEMPTS?: string;
  VITE_API_RETRY_DELAY?: string;
  
  // WebSocket Configuration
  VITE_WS_BASE_URL?: string;
  VITE_WS_RECONNECT_ATTEMPTS?: string;
  VITE_WS_RECONNECT_DELAY?: string;
  VITE_WS_HEARTBEAT_INTERVAL?: string;
  VITE_WS_CONNECTION_TIMEOUT?: string;
  
  // Authentication Configuration
  VITE_AUTH_TOKEN_STORAGE_KEY?: string;
  VITE_AUTH_USER_STORAGE_KEY?: string;
  VITE_AUTH_TOKEN_EXPIRY_BUFFER?: string;
  
  // UI Configuration
  VITE_UI_THEME?: string;
  VITE_UI_LANGUAGE?: string;
  VITE_UI_AUTO_SAVE?: string;
  VITE_UI_AUTO_SAVE_INTERVAL?: string;
  
  // Feature Flags
  VITE_FEATURES_DEBUG_MODE?: string;
  VITE_FEATURES_ANALYTICS_ENABLED?: string;
  VITE_FEATURES_OFFLINE_MODE?: string;
  VITE_FEATURES_PUSH_NOTIFICATIONS?: string;
  
  // Development Configuration
  VITE_DEV_HOT_RELOAD?: string;
  VITE_DEV_SOURCE_MAPS?: string;
  VITE_DEV_CONSOLE_LOGGING?: string;
  
  // Application Environment
  NODE_ENV?: string;
  VITE_APP_ENV?: string;
}
/**
 * Configuration manager class
 */
class ConfigManager {
  private config: AppConfig;
  private environment: EnvironmentVariables;

  constructor() {
    this.environment = {
      // API Configuration
      VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
      VITE_API_TIMEOUT: import.meta.env.VITE_API_TIMEOUT,
      VITE_API_RETRY_ATTEMPTS: import.meta.env.VITE_API_RETRY_ATTEMPTS,
      VITE_API_RETRY_DELAY: import.meta.env.VITE_API_RETRY_DELAY,
      
      // WebSocket Configuration
      VITE_WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL,
      VITE_WS_RECONNECT_ATTEMPTS: import.meta.env.VITE_WS_RECONNECT_ATTEMPTS,
      VITE_WS_RECONNECT_DELAY: import.meta.env.VITE_WS_RECONNECT_DELAY,
      VITE_WS_HEARTBEAT_INTERVAL: import.meta.env.VITE_WS_HEARTBEAT_INTERVAL,
      VITE_WS_CONNECTION_TIMEOUT: import.meta.env.VITE_WS_CONNECTION_TIMEOUT,
      
      // Authentication Configuration
      VITE_AUTH_TOKEN_STORAGE_KEY: import.meta.env.VITE_AUTH_TOKEN_STORAGE_KEY,
      VITE_AUTH_USER_STORAGE_KEY: import.meta.env.VITE_AUTH_USER_STORAGE_KEY,
      VITE_AUTH_TOKEN_EXPIRY_BUFFER: import.meta.env.VITE_AUTH_TOKEN_EXPIRY_BUFFER,
      
      // UI Configuration
      VITE_UI_THEME: import.meta.env.VITE_UI_THEME,
      VITE_UI_LANGUAGE: import.meta.env.VITE_UI_LANGUAGE,
      VITE_UI_AUTO_SAVE: import.meta.env.VITE_UI_AUTO_SAVE,
      VITE_UI_AUTO_SAVE_INTERVAL: import.meta.env.VITE_UI_AUTO_SAVE_INTERVAL,
      
      // Feature Flags
      VITE_FEATURES_DEBUG_MODE: import.meta.env.VITE_FEATURES_DEBUG_MODE,
      VITE_FEATURES_ANALYTICS_ENABLED: import.meta.env.VITE_FEATURES_ANALYTICS_ENABLED,
      VITE_FEATURES_OFFLINE_MODE: import.meta.env.VITE_FEATURES_OFFLINE_MODE,
      VITE_FEATURES_PUSH_NOTIFICATIONS: import.meta.env.VITE_FEATURES_PUSH_NOTIFICATIONS,
      
      // Development Configuration
      VITE_DEV_HOT_RELOAD: import.meta.env.VITE_DEV_HOT_RELOAD,
      VITE_DEV_SOURCE_MAPS: import.meta.env.VITE_DEV_SOURCE_MAPS,
      VITE_DEV_CONSOLE_LOGGING: import.meta.env.VITE_DEV_CONSOLE_LOGGING,
      
      // Application Environment
      NODE_ENV: import.meta.env.NODE_ENV,
      VITE_APP_ENV: import.meta.env.VITE_APP_ENV,
    };
    // Load configuration from environment variables
    this.config = this.loadConfiguration();
  }

  /**
   * Load configuration from environment variables with fallback defaults
   */
  private loadConfiguration(): AppConfig {
    const config: AppConfig = {
      api: {
        baseUrl: this.environment.VITE_API_BASE_URL || "http://localhost:8009",
        timeout: this.parseInt(this.environment.VITE_API_TIMEOUT, 30000),
        retryAttempts: this.parseInt(this.environment.VITE_API_RETRY_ATTEMPTS, 3),
        retryDelay: this.parseInt(this.environment.VITE_API_RETRY_DELAY, 1000),
      },
      websocket: {
        reconnectAttempts: this.parseInt(this.environment.VITE_WS_RECONNECT_ATTEMPTS, 5),
        reconnectDelay: this.parseInt(this.environment.VITE_WS_RECONNECT_DELAY, 2000),
        heartbeatInterval: this.parseInt(this.environment.VITE_WS_HEARTBEAT_INTERVAL, 30000),
        connectionTimeout: this.parseInt(this.environment.VITE_WS_CONNECTION_TIMEOUT, 10000),
      },
      auth: {
        tokenStorageKey: this.environment.VITE_AUTH_TOKEN_STORAGE_KEY || "authToken",
        userStorageKey: this.environment.VITE_AUTH_USER_STORAGE_KEY || "authUser",
        tokenExpiryBuffer: this.parseInt(this.environment.VITE_AUTH_TOKEN_EXPIRY_BUFFER, 300000),
      },
      ui: {
        theme: (this.environment.VITE_UI_THEME as 'light' | 'dark' | 'auto') || "light",
        language: this.environment.VITE_UI_LANGUAGE || "en",
        autoSave: this.parseBoolean(this.environment.VITE_UI_AUTO_SAVE, true),
        autoSaveInterval: this.parseInt(this.environment.VITE_UI_AUTO_SAVE_INTERVAL, 30000),
      },
      features: {
        enableDebugMode: this.parseBoolean(this.environment.VITE_FEATURES_DEBUG_MODE, false),
        enableAnalytics: this.parseBoolean(this.environment.VITE_FEATURES_ANALYTICS_ENABLED, false),
        enableOfflineMode: this.parseBoolean(this.environment.VITE_FEATURES_OFFLINE_MODE, false),
        enablePushNotifications: this.parseBoolean(this.environment.VITE_FEATURES_PUSH_NOTIFICATIONS, false),
      },
      development: {
        enableHotReload: this.parseBoolean(this.environment.VITE_DEV_HOT_RELOAD, true),
        enableSourceMaps: this.parseBoolean(this.environment.VITE_DEV_SOURCE_MAPS, true),
        enableConsoleLogging: this.parseBoolean(this.environment.VITE_DEV_CONSOLE_LOGGING, false),
      },
    };

    // Validate configuration
    this.validateConfiguration(config);

    return config;
  }

  /**
   * Parse integer environment variable
   */
  private parseInt(value: string | undefined, defaultValue: number): number {
    if (value === undefined) return defaultValue;
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? defaultValue : parsed;
  }

  /**
   * Parse boolean environment variable
   */
  private parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
    if (value === undefined) return defaultValue;
    return value.toLowerCase() === 'true' || value === '1';
  }

  /**
   * Get environment variable with fallback
   */
  private getEnv(key: string, defaultValue: string): string {
    return import.meta.env[key] || defaultValue;
  }

  /**
   * Get environment variable as number with fallback
   */
  private getEnvNumber(key: string, defaultValue: number): number {
    const value = import.meta.env[key];
    if (value === undefined || value === '') return defaultValue;
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? defaultValue : parsed;
  }

  /**
   * Get environment variable as boolean with fallback
   */
  private getEnvBoolean(key: string, defaultValue: boolean): boolean {
    const value = import.meta.env[key];
    if (value === undefined || value === '') return defaultValue;
    return value.toLowerCase() === 'true' || value === '1';
  }

  /**
   * Check if running in development mode
   */
  private isDevelopmentMode(): boolean {
    return import.meta.env.NODE_ENV === 'development' || 
           import.meta.env.NODE_ENV === 'dev' ||
           import.meta.env.DEV;
  }

  /**
   * Validate configuration
   */
  private validateConfiguration(config: AppConfig): void {
    if (!config.api.baseUrl) {
      throw new Error('API base URL is required');
    }

    if (!config.api.baseUrl.startsWith('http://') && !config.api.baseUrl.startsWith('https://')) {
      throw new Error('API base URL must start with http:// or https://');
    }

    if (config.api.timeout <= 0) {
      throw new Error('API timeout must be greater than 0');
    }

    if (config.websocket.reconnectAttempts < 0) {
      throw new Error('WebSocket reconnect attempts must be non-negative');
    }

    if (config.auth.tokenExpiryBuffer < 0) {
      throw new Error('Token expiry buffer must be non-negative');
    }
  }

  /**
   * Get the complete configuration
   */
  getConfig(): AppConfig {
    return { ...this.config };
  }

  /**
   * Get API configuration
   */
  getApiConfig(): ApiConfig {
    return { ...this.config.api };
  }

  /**
   * Get WebSocket configuration
   */
  getWebSocketConfig(): WebSocketConfig {
    return { ...this.config.websocket };
  }

  /**
   * Get authentication configuration
   */
  getAuthConfig(): AuthConfig {
    return { ...this.config.auth };
  }

  /**
   * Get UI configuration
   */
  getUIConfig(): UIConfig {
    return { ...this.config.ui };
  }

  /**
   * Get features configuration
   */
  getFeaturesConfig(): FeaturesConfig {
    return { ...this.config.features };
  }

  /**
   * Get development configuration
   */
  getDevelopmentConfig(): DevelopmentConfig {
    return { ...this.config.development };
  }

  /**
   * Get API base URL
   */
  getApiBaseUrl(): string {
    return this.config.api.baseUrl;
  }

  /**
   * Get WebSocket URL
   */
  getWebSocketUrl(): string {
    return this.environment.VITE_WS_BASE_URL || 
           this.config.api.baseUrl.replace(/^http/, 'ws');
  }

  /**
   * Get full API endpoint URL
   */
  getApiUrl(endpoint: string): string {
    const baseUrl = this.getApiBaseUrl();
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${cleanEndpoint}`;
  }

  /**
   * Get full WebSocket endpoint URL
   */
  getWebSocketEndpoint(endpoint: string): string {
    const baseUrl = this.getWebSocketUrl();
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${cleanEndpoint}`;
  }

  /**
   * Check if debug mode is enabled
   */
  isDebugMode(): boolean {
    return this.config.features.enableDebugMode;
  }

  /**
   * Check if analytics is enabled
   */
  isAnalyticsEnabled(): boolean {
    return this.config.features.enableAnalytics;
  }

  /**
   * Check if running in development mode
   */
  isDevelopment(): boolean {
    return this.isDevelopmentMode();
  }

  /**
   * Log configuration (for debugging)
   */
  logConfiguration(): void {
    if (this.isDebugMode()) {
      console.group('🔧 Application Configuration');
      console.log('API Base URL:', this.getApiBaseUrl());
      console.log('WebSocket URL:', this.getWebSocketUrl());
      console.log('Debug Mode:', this.isDebugMode());
      console.log('Analytics:', this.isAnalyticsEnabled());
      console.log('Development:', this.isDevelopment());
      console.groupEnd();
    }
  }
}

// Create and export singleton instance
export const config = new ConfigManager();

// Export configuration getters for convenience
export const getApiBaseUrl = () => config.getApiBaseUrl();
export const getWebSocketUrl = () => config.getWebSocketUrl();
export const getApiUrl = (endpoint: string) => config.getApiUrl(endpoint);
export const getWebSocketEndpoint = (endpoint: string) => config.getWebSocketEndpoint(endpoint);
export const isDebugMode = () => config.isDebugMode();
export const isAnalyticsEnabled = () => config.isAnalyticsEnabled();
export const isDevelopment = () => config.isDevelopment();

// Export default configuration
export default config;
