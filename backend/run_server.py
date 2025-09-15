#!/usr/bin/env python3
"""Example script to run the Puntini Agent API server with configuration.

This script demonstrates how to use the new server configuration system
to start the FastAPI server with settings from config.json.
"""

from puntini.utils.settings import Settings
from puntini.api.app import run_server


def main():
    """Main function to run the server with configuration."""
    print("Starting Puntini Agent API Server...")
    print("Configuration will be loaded from config.json")
    
    # Create settings instance (loads from config.json)
    settings = Settings()
    
    # Display server configuration
    server_config = settings.get_server_config()
    print(f"\nServer Configuration:")
    print(f"  Host: {server_config['host']}")
    print(f"  Port: {server_config['port']}")
    print(f"  Reload: {server_config['reload']}")
    print(f"  Workers: {server_config['workers']}")
    print(f"  Access Log: {server_config['access_log']}")
    print(f"  Log Level: {server_config['log_level']}")
    print(f"  Docs URL: {server_config['docs_url']}")
    print(f"  OpenAPI URL: {server_config['openapi_url']}")
    
    # Run the server
    print(f"\nStarting server on http://{server_config['host']}:{server_config['port']}")
    print(f"API documentation will be available at: http://{server_config['host']}:{server_config['port']}{server_config['docs_url']}")
    print("Press Ctrl+C to stop the server\n")
    
    run_server(settings)


if __name__ == "__main__":
    main()
