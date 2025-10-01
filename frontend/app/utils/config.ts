/**
 * Configuration management utility for the frontend application.
 * 
 * This module provides a centralized configuration system that loads settings
 * exclusively from environment variables.
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

/**
 * Configuration manager class
 */
class ConfigManager {
  private config: AppConfig;

  constructor() {
    // Load configuration from environment variables
    this.config = this.loadConfiguration();
  }

  /**
   * Load configuration from environment variables
   */
  private loadConfiguration(): AppConfig {
    const config: AppConfig = {
      api: {
        baseUrl: this.getEnv('VITE_API_BASE_URL', 'http://localhost:8000'),
        timeout: this.getEnvNumber('VITE_API_TIMEOUT', 30000),
        retryAttempts: this.getEnvNumber('VITE_API_RETRY_ATTEMPTS', 3),
        retryDelay: this.getEnvNumber('VITE_API_RETRY_DELAY', 1000),
      },
      websocket: {
        reconnectAttempts: this.getEnvNumber('VITE_WS_RECONNECT_ATTEMPTS', 5),
        reconnectDelay: this.getEnvNumber('VITE_WS_RECONNECT_DELAY', 2000),
        heartbeatInterval: this.getEnvNumber('VITE_WS_HEARTBEAT_INTERVAL', 30000),
        connectionTimeout: this.getEnvNumber('VITE_WS_CONNECTION_TIMEOUT', 10000),
      },
      auth: {
        tokenStorageKey: this.getEnv('VITE_AUTH_TOKEN_KEY', 'puntini_access_token'),
        userStorageKey: this.getEnv('VITE_AUTH_USER_KEY', 'puntini_user_data'),
        tokenExpiryBuffer: this.getEnvNumber('VITE_AUTH_TOKEN_EXPIRY_BUFFER', 300000),
      },
      ui: {
        theme: this.getEnv('VITE_UI_THEME', 'auto') as 'light' | 'dark' | 'auto',
        language: this.getEnv('VITE_UI_LANGUAGE', 'en'),
        autoSave: this.getEnvBoolean('VITE_UI_AUTO_SAVE', true),
        autoSaveInterval: this.getEnvNumber('VITE_UI_AUTO_SAVE_INTERVAL', 30000),
      },
      features: {
        enableDebugMode: this.getEnvBoolean('VITE_DEBUG_MODE', this.isDevelopmentMode()),
        enableAnalytics: this.getEnvBoolean('VITE_ANALYTICS_ENABLED', false),
        enableOfflineMode: this.getEnvBoolean('VITE_OFFLINE_MODE', false),
        enablePushNotifications: this.getEnvBoolean('VITE_PUSH_NOTIFICATIONS', false),
      },
      development: {
        enableHotReload: this.getEnvBoolean('VITE_DEV_HOT_RELOAD', true),
        enableSourceMaps: this.getEnvBoolean('VITE_DEV_SOURCE_MAPS', true),
        enableConsoleLogging: this.getEnvBoolean('VITE_DEV_CONSOLE_LOGGING', this.isDevelopmentMode()),
      },
    };

    // Validate configuration
    this.validateConfiguration(config);

    return config;
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
    const wsBaseUrl = this.environment.VITE_WS_BASE_URL || 
                     this.config.api.baseUrl.replace(/^http/, 'ws');
    return wsBaseUrl;
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
    return this.config.features.enableDebugMode || this.isDevelopment();
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
