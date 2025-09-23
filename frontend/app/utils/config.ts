/**
 * Configuration management utility for the frontend application.
 * 
 * This module provides a centralized configuration system that loads settings
 * from a JSON configuration file and supports environment variable overrides.
 */

import configData from '../../config.json';

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

// Environment variable overrides
interface EnvironmentOverrides {
  VITE_API_BASE_URL?: string;
  VITE_WS_BASE_URL?: string;
  VITE_DEBUG_MODE?: string;
  VITE_ANALYTICS_ENABLED?: string;
  NODE_ENV?: string;
}

/**
 * Configuration manager class
 */
class ConfigManager {
  private config: AppConfig;
  private environment: EnvironmentOverrides;

  constructor() {
    this.environment = {
      VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
      VITE_WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL,
      VITE_DEBUG_MODE: import.meta.env.VITE_DEBUG_MODE,
      VITE_ANALYTICS_ENABLED: import.meta.env.VITE_ANALYTICS_ENABLED,
      NODE_ENV: import.meta.env.NODE_ENV,
    };

    // Load and merge configuration
    this.config = this.loadConfiguration();
  }

  /**
   * Load configuration with environment variable overrides
   */
  private loadConfiguration(): AppConfig {
    const baseConfig = configData as AppConfig;

    // Apply environment variable overrides
    const mergedConfig: AppConfig = {
      ...baseConfig,
      api: {
        ...baseConfig.api,
        baseUrl: this.environment.VITE_API_BASE_URL || baseConfig.api.baseUrl,
      },
      features: {
        ...baseConfig.features,
        enableDebugMode: this.parseBoolean(this.environment.VITE_DEBUG_MODE, baseConfig.features.enableDebugMode),
        enableAnalytics: this.parseBoolean(this.environment.VITE_ANALYTICS_ENABLED, baseConfig.features.enableAnalytics),
      },
      development: {
        ...baseConfig.development,
        enableConsoleLogging: this.isDevelopmentMode() ? true : baseConfig.development.enableConsoleLogging,
      },
    };

    // Validate configuration
    this.validateConfiguration(mergedConfig);

    return mergedConfig;
  }

  /**
   * Parse boolean environment variable
   */
  private parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
    if (value === undefined) return defaultValue;
    return value.toLowerCase() === 'true' || value === '1';
  }

  /**
   * Check if running in development mode
   */
  private isDevelopmentMode(): boolean {
    return this.environment.NODE_ENV === 'development' || 
           this.environment.NODE_ENV === 'dev' ||
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
