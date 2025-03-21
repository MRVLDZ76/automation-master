#!/usr/bin/env python3
"""
Redis-Celery Connection Troubleshooter

This script helps diagnose and fix Redis connection issues for Celery workers.
It provides:
1. Connectivity checks to Redis
2. Docker container status verification
3. Redis service status verification
4. Network configuration validation
5. Automated fixes for common issues
"""

import os
import sys
import subprocess
import socket
import time
import json

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def run_command(command, shell=False):
    """Run a shell command and return the output."""
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=True, 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                 text=True)
        else:
            result = subprocess.run(command.split(), check=True, 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                 text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {e.stderr}")
        return None

def check_redis_connection(host="localhost", port=6379):
    """Test direct Redis connection."""
    print_header("Testing Redis Connection")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✅ Redis is reachable at {host}:{port}")
            return True
        else:
            print(f"❌ Redis is NOT reachable at {host}:{port}")
            return False
    except Exception as e:
        print(f"❌ Error testing Redis connection: {e}")
        return False

def check_redis_cli():
    """Test Redis connection using redis-cli."""
    print_header("Testing Redis with redis-cli")
    result = run_command("redis-cli ping")
    if result == "PONG":
        print("✅ Redis responded to PING")
        return True
    else:
        print("❌ Redis did not respond to PING")
        return False

def check_docker_status():
    """Check if Docker is running and verify container status."""
    print_header("Checking Docker Status")
    
    docker_ps = run_command("docker ps")
    if docker_ps is None:
        print("❌ Docker might not be running")
        return False
    
    print("Current running containers:")
    print(docker_ps)
    
    # Check for redis container
    redis_container = run_command("docker ps | grep redis")
    if redis_container:
        print("✅ Redis container found")
    else:
        print("❌ No Redis container found")
    
    return True

def check_celery_config():
    """Check Celery configuration files."""
    print_header("Checking Celery Configuration")
    
    # Check for celery.py or similar files
    celery_files = run_command("find . -name 'celery.py' -o -name 'celeryconfig.py'", shell=True)
    if celery_files:
        print("Found Celery configuration files:")
        print(celery_files)
        
        # Try to read and report broker settings
        for file_path in celery_files.split('\n'):
            if os.path.exists(file_path):
                content = open(file_path, 'r').read()
                if 'BROKER_URL' in content or 'broker_url' in content:
                    print(f"\nBroker settings found in {file_path}:")
                    for line in content.split('\n'):
                        if 'BROKER_URL' in line or 'broker_url' in line:
                            print(f"  {line.strip()}")
    else:
        print("❌ No Celery configuration files found")

def test_redis_docker_network():
    """Test network connectivity between Docker containers."""
    print_header("Testing Docker Network Configuration")
    
    # List Docker networks
    networks = run_command("docker network ls")
    print("Docker networks:")
    print(networks)
    
    # Get network details for the containers
    celery_network = run_command("docker inspect ppall_scraping_worker | grep -A 20 'Networks'", shell=True)
    redis_network = run_command("docker ps | grep redis | awk '{print $1}' | xargs -I{} docker inspect {} | grep -A 20 'Networks'", shell=True)
    
    print("\nCelery worker network configuration:")
    print(celery_network or "Unable to determine")
    
    print("\nRedis container network configuration:")
    print(redis_network or "Unable to determine")

def fix_redis_connection():
    """Attempt to fix Redis connection issues."""
    print_header("Attempting to Fix Redis Connection")
    
    # Check if Redis is running
    redis_status = run_command("systemctl status redis-server", shell=True)
    if redis_status and "active (running)" in redis_status:
        print("✅ Redis service is running on the host")
    else:
        print("⚠️  Redis service is not running on the host, attempting to start...")
        start_result = run_command("sudo systemctl start redis-server", shell=True)
        if start_result is not None:
            print("✅ Started Redis service")
        else:
            print("❌ Failed to start Redis service")
    
    # Check if we need to start a Redis container
    redis_container = run_command("docker ps | grep redis")
    if not redis_container:
        print("⚠️  No Redis container found, attempting to start one...")
        start_container = run_command("docker run --name redis -d -p 6379:6379 redis")
        if start_container:
            print("✅ Started Redis container")
        else:
            print("❌ Failed to start Redis container")
    
    # Update Celery configuration if needed
    print("\n⚠️  You may need to update your Celery configuration to point to the correct Redis host.")
    print("   Common configurations:")
    print("   - 'redis://localhost:6379/0' (for host Redis)")
    print("   - 'redis://redis:6379/0' (for container Redis with container name 'redis')")
    print("   - 'redis://host.docker.internal:6379/0' (for host Redis from Docker container)")

def generate_docker_compose():
    """Generate a docker-compose file with proper networking."""
    print_header("Generating Docker Compose File")
    
    docker_compose = {
        "version": "3",
        "services": {
            "redis": {
                "image": "redis:latest",
                "ports": ["6379:6379"],
                "restart": "always",
                "networks": ["app-network"]
            },
            "scraping_worker": {
                "build": ".",
                "command": "celery -A automation worker -l info -Q scraping",
                "volumes": [".:/app"],
                "depends_on": ["redis"],
                "networks": ["app-network"],
                "environment": {
                    "CELERY_BROKER_URL": "redis://redis:6379/0",
                    "CELERY_RESULT_BACKEND": "redis://redis:6379/0"
                }
            },
            "images_worker": {
                "build": ".",
                "command": "celery -A automation worker -l info -Q images",
                "volumes": [".:/app"],
                "depends_on": ["redis"],
                "networks": ["app-network"],
                "environment": {
                    "CELERY_BROKER_URL": "redis://redis:6379/0",
                    "CELERY_RESULT_BACKEND": "redis://redis:6379/0"
                }
            }
        },
        "networks": {
            "app-network": {
                "driver": "bridge"
            }
        }
    }
    
    with open("docker-compose.troubleshoot.yml", "w") as f:
        json.dump(docker_compose, f, indent=2)
    
    print("✅ Generated docker-compose.troubleshoot.yml")
    print("\nTo use this file, run:")
    print("docker-compose -f docker-compose.troubleshoot.yml up -d")

def create_celery_patch():
    """Create a patch for celery.py to use the correct Redis URL."""
    print_header("Creating Celery Configuration Patch")
    
    patch_content = """
# Add this to your celery.py file:

# For Docker container setup:
app.conf.broker_url = 'redis://redis:6379/0'
app.conf.result_backend = 'redis://redis:6379/0'

# For localhost setup (if Redis is on the host):
# app.conf.broker_url = 'redis://localhost:6379/0'
# app.conf.result_backend = 'redis://localhost:6379/0'

# For Docker-to-host communication:
# app.conf.broker_url = 'redis://host.docker.internal:6379/0'
# app.conf.result_backend = 'redis://host.docker.internal:6379/0'
"""
    
    with open("celery_config_patch.py", "w") as f:
        f.write(patch_content)
    
    print("✅ Created celery_config_patch.py")
    print("Add the appropriate configuration to your celery.py file")

def main():
    print_header("Redis-Celery Connection Troubleshooter")
    
    # Run all checks
    redis_connected = check_redis_connection()
    redis_cli_ok = check_redis_cli()
    docker_ok = check_docker_status()
    check_celery_config()
    test_redis_docker_network()
    
    # Try to fix issues
    if not redis_connected or not redis_cli_ok:
        fix_redis_connection()
    
    # Generate helpful files
    generate_docker_compose()
    create_celery_patch()
    
    print_header("Summary and Recommendations")
    if not redis_connected:
        print("1. Start Redis service if it's not running:")
        print("   sudo systemctl start redis-server")
        print("\n2. Or start a Redis Docker container:")
        print("   docker run --name redis -d -p 6379:6379 redis")
    
    print("\n3. Update your Celery configuration to use the correct Redis URL.")
    print("   Check celery_config_patch.py for examples.")
    
    print("\n4. If using Docker, ensure all containers are on the same network:")
    print("   docker network create app-network")
    print("   docker network connect app-network ppall_scraping_worker")
    print("   docker network connect app-network ppall_images_worker")
    print("   docker network connect app-network redis-container-name")
    
    print("\n5. Alternatively, use the generated docker-compose file:")
    print("   docker-compose -f docker-compose.troubleshoot.yml up -d")
    
    print("\n6. Restart your Celery workers after making changes.")

if __name__ == "__main__":
    main()
