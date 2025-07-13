#!/usr/bin/env python3
"""
Setup Script for Distributed Tracing
Helps install dependencies and configure the tracing system
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def install_dependencies():
    """Install tracing dependencies"""
    print("📦 Installing OpenTelemetry dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements_tracing.txt"
        ])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True


def setup_jaeger_docker():
    """Setup Jaeger using Docker"""
    print("🐳 Setting up Jaeger with Docker...")
    
    jaeger_command = [
        "docker", "run", "-d", "--name", "jaeger",
        "-e", "COLLECTOR_ZIPKIN_HOST_PORT=:9411",
        "-p", "5775:5775/udp",
        "-p", "6831:6831/udp", 
        "-p", "6832:6832/udp",
        "-p", "5778:5778",
        "-p", "16686:16686",
        "-p", "14268:14268",
        "-p", "14250:14250",
        "-p", "9411:9411",
        "jaegertracing/all-in-one:latest"
    ]
    
    try:
        # Check if Jaeger is already running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=jaeger", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        
        if "jaeger" in result.stdout:
            print("✅ Jaeger is already running!")
            return True
        
        # Start Jaeger
        subprocess.check_call(jaeger_command)
        print("✅ Jaeger started successfully!")
        print("🌐 Jaeger UI available at: http://localhost:16686")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Jaeger: {e}")
        print("💡 Make sure Docker is installed and running")
        return False
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker first.")
        return False


def create_env_file():
    """Create or update .env file with tracing configuration"""
    print("⚙️ Creating tracing configuration...")
    
    env_path = Path(".env")
    env_content = []
    
    # Read existing content if file exists
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.readlines()
    
    # Tracing configuration
    tracing_config = """
# Distributed Tracing Configuration
JAEGER_ENDPOINT=http://localhost:14268/api/traces
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831

# Service Configuration
SERVICE_NAME=aictive-platform
SERVICE_VERSION=2.0.0
ENVIRONMENT=production

# Tracing Configuration
TRACE_SAMPLING_RATE=0.1
TRACE_EMERGENCY_SAMPLING_RATE=1.0
TRACE_SLOW_QUERY_THRESHOLD_MS=1000
TRACE_SLOW_API_THRESHOLD_MS=5000
"""
    
    # Check if tracing config already exists
    has_tracing_config = any("JAEGER_ENDPOINT" in line for line in env_content)
    
    if not has_tracing_config:
        env_content.append(tracing_config)
        
        with open(env_path, 'w') as f:
            f.writelines(env_content)
        
        print("✅ Tracing configuration added to .env file")
    else:
        print("✅ Tracing configuration already exists in .env file")


def create_docker_compose():
    """Create docker-compose.yml for Jaeger and supporting services"""
    print("🐳 Creating docker-compose.yml for tracing infrastructure...")
    
    docker_compose_content = """version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # HTTP collector
      - "6831:6831/udp"  # UDP agent
      - "6832:6832/udp"  # UDP agent
      - "5778:5778"  # Config server
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
    networks:
      - tracing

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - tracing

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"  # Use 3001 to avoid conflicts
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
    networks:
      - tracing

networks:
  tracing:
    driver: bridge

volumes:
  grafana-storage:
"""
    
    with open("docker-compose-tracing.yml", "w") as f:
        f.write(docker_compose_content)
    
    print("✅ docker-compose-tracing.yml created")
    
    # Create Prometheus config
    prometheus_config = """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'aictive-platform'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
"""
    
    with open("prometheus.yml", "w") as f:
        f.write(prometheus_config)
    
    print("✅ prometheus.yml created")


def run_tests():
    """Run tracing tests"""
    print("🧪 Running tracing tests...")
    
    try:
        subprocess.check_call([sys.executable, "test_tracing.py"])
        print("✅ All tests passed!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False
    return True


def validate_setup():
    """Validate that tracing is working"""
    print("🔍 Validating tracing setup...")
    
    # Check if required files exist
    required_files = [
        "distributed_tracing.py",
        "trace_middleware.py", 
        "tracing_integration_example.py"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Missing required file: {file}")
            return False
    
    print("✅ All required files present")
    
    # Try importing the modules
    try:
        import distributed_tracing
        import trace_middleware
        print("✅ Modules can be imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Setup distributed tracing for Aictive platform")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker setup")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--test", action="store_true", help="Run tests only")
    parser.add_argument("--validate", action="store_true", help="Validate setup only")
    
    args = parser.parse_args()
    
    print("🚀 Setting up Distributed Tracing for Aictive Platform\n")
    
    # Validate only
    if args.validate:
        success = validate_setup()
        sys.exit(0 if success else 1)
    
    # Test only
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # Full setup
    steps_passed = 0
    total_steps = 5
    
    # Step 1: Install dependencies
    if not args.skip_deps:
        if install_dependencies():
            steps_passed += 1
        print()
    else:
        steps_passed += 1
    
    # Step 2: Create environment configuration
    create_env_file()
    steps_passed += 1
    print()
    
    # Step 3: Setup Docker infrastructure
    if not args.skip_docker:
        if setup_jaeger_docker():
            steps_passed += 1
        print()
    else:
        steps_passed += 1
    
    # Step 4: Create Docker Compose files
    create_docker_compose()
    steps_passed += 1
    print()
    
    # Step 5: Validate setup
    if validate_setup():
        steps_passed += 1
    print()
    
    # Summary
    print("=" * 50)
    print(f"Setup Summary: {steps_passed}/{total_steps} steps completed")
    
    if steps_passed == total_steps:
        print("🎉 Distributed tracing setup completed successfully!")
        print("\nNext steps:")
        print("1. Start your FastAPI application with tracing enabled")
        print("2. Visit http://localhost:16686 to view traces in Jaeger")
        print("3. Check the DISTRIBUTED_TRACING_GUIDE.md for usage instructions")
        print("4. Run 'python test_tracing.py' to validate the implementation")
    else:
        print("⚠️ Setup completed with some issues. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()