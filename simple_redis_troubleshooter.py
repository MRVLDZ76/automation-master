#!/usr/bin/env python3
"""
Simple Redis-Celery Troubleshooter
A lightweight script to diagnose Redis connection issues
"""

import socket
import subprocess
import os

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)

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

def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(command, shell=True, check=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Command failed: {command}")
        print(f"Error: {e}")
        return None, -1

def check_docker_status():
    """Check if Docker is running and verify container status."""
    print_header("Checking Docker Status")
    
    docker_ps, status = run_command("docker ps")
    if status != 0:
        print("❌ Docker might not be running or you don't have permission to use it")
        return False
    
    print("Current running containers:")
    print(docker_ps if docker_ps else "No containers running")
    
    # Check for redis container
    redis_container, _ = run_command("docker ps | grep redis")
    if redis_container:
        print("✅ Redis container found")
    else:
        print("❌ No Redis container found")
    
    return True

def print_recommendations():
    """Print recommendations to fix Redis connection issues."""
    print_header("Recommendations")
    
    print("1. Make sure Redis is running:")
    print("   • As a system service: sudo systemctl status redis-server")
    print("   • As a Docker container: docker run -d -p 6379:6379 --name redis redis")
    
    print("\n2. Update Celery configuration:")
    print("   For containers accessing Redis on the host:")
    print("   • Use 'host.docker.internal' instead of 'localhost':")
    print("     broker_url = 'redis://host.docker.internal:6379/0'")
    print("     result_backend = 'redis://host.docker.internal:6379/0'")
    
    print("\n3. For Redis in another container:")
    print("   • Create a network: docker network create app-network")
    print("   • Connect containers: docker network connect app-network container_name")
    print("   • Use container name: broker_url = 'redis://redis-container-name:6379/0'")
    
    print("\n4. Check for firewalls blocking port 6379")
    
    print("\n5. Verify Redis configuration allows external connections:")
    print("   • Check 'bind' directive in redis.conf")
    print("   • Ensure 'protected-mode' is set appropriately")

def main():
    print_header("Redis-Celery Connection Troubleshooter")
    
    # Basic local Redis check
    local_redis = check_redis_connection()
    
    # Try Docker host address (for containers)
    if not local_redis:
        print("\nTrying Docker host address...")
        docker_host_redis = check_redis_connection("host.docker.internal")
    
    # Check Docker status
    docker_status = check_docker_status()
    
    # Additional checks for Docker container networking
    if docker_status:
        print_header("Testing Redis from Inside a Container")
        cmd = "docker run --rm redis redis-cli -h host.docker.internal ping"
        output, status = run_command(cmd)
        if status == 0 and "PONG" in output:
            print("✅ Redis is accessible from a test container")
        else:
            print("❌ Redis is NOT accessible from a test container")
    
    # Print recommendations
    print_recommendations()

if __name__ == "__main__":
    main()
