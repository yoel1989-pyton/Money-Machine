#!/bin/bash
# ============================================================
# MONEY MACHINE - DEPLOY SCRIPT
# One-command deployment for local testing and emergency redeploy
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="money-machine"
CONTAINER_NAME="money-machine"
DATA_DIR="$(pwd)/data"

echo -e "${BLUE}🚀 MONEY MACHINE DEPLOYMENT SCRIPT${NC}"
echo "============================================"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check for .env file
check_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found!"
        if [ -f ".env.example" ]; then
            echo "Creating .env from .env.example..."
            cp .env.example .env
            print_warning "Please edit .env with your API keys before running again."
            exit 1
        else
            print_error "No .env.example found. Create .env manually."
            exit 1
        fi
    fi
    print_status ".env file found"
}

# Create data directories
create_data_dirs() {
    echo "Creating data directories..."
    mkdir -p "${DATA_DIR}/logs"
    mkdir -p "${DATA_DIR}/metrics"
    mkdir -p "${DATA_DIR}/reports"
    mkdir -p "${DATA_DIR}/cache"
    mkdir -p "${DATA_DIR}/videos"
    print_status "Data directories created"
}

# Stop existing container
stop_existing() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Stopping existing container..."
        docker stop ${CONTAINER_NAME} 2>/dev/null || true
        docker rm ${CONTAINER_NAME} 2>/dev/null || true
        print_status "Existing container removed"
    fi
}

# Build Docker image
build_image() {
    echo "Building Docker image..."
    docker build -t ${IMAGE_NAME}:latest .
    print_status "Docker image built: ${IMAGE_NAME}:latest"
}

# Run container
run_container() {
    echo "Starting container..."
    docker run -d \
        --name ${CONTAINER_NAME} \
        --env-file .env \
        -v ${DATA_DIR}:/data \
        -p 5678:5678 \
        --restart unless-stopped \
        ${IMAGE_NAME}:latest
    print_status "Container started: ${CONTAINER_NAME}"
}

# Health check
health_check() {
    echo "Waiting for health check..."
    sleep 5
    
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_status "Container is running"
        echo ""
        echo -e "${GREEN}🎉 MONEY MACHINE IS ONLINE${NC}"
        echo "============================================"
        echo "n8n UI: http://localhost:5678"
        echo "Logs:   docker logs -f ${CONTAINER_NAME}"
        echo "Stop:   docker stop ${CONTAINER_NAME}"
        echo ""
    else
        print_error "Container failed to start"
        echo "Check logs: docker logs ${CONTAINER_NAME}"
        exit 1
    fi
}

# Main execution
main() {
    case "${1:-deploy}" in
        deploy)
            check_env
            create_data_dirs
            stop_existing
            build_image
            run_container
            health_check
            ;;
        build)
            build_image
            ;;
        start)
            check_env
            create_data_dirs
            run_container
            health_check
            ;;
        stop)
            stop_existing
            print_status "Money Machine stopped"
            ;;
        restart)
            stop_existing
            run_container
            health_check
            ;;
        logs)
            docker logs -f ${CONTAINER_NAME}
            ;;
        status)
            if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
                print_status "Money Machine is running"
                docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Status}}\t{{.Ports}}"
            else
                print_warning "Money Machine is not running"
            fi
            ;;
        shell)
            docker exec -it ${CONTAINER_NAME} bash
            ;;
        *)
            echo "Usage: $0 {deploy|build|start|stop|restart|logs|status|shell}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Full deployment (build + run)"
            echo "  build    - Build Docker image only"
            echo "  start    - Start container (uses existing image)"
            echo "  stop     - Stop and remove container"
            echo "  restart  - Restart container"
            echo "  logs     - Follow container logs"
            echo "  status   - Check if running"
            echo "  shell    - Open bash shell in container"
            exit 1
            ;;
    esac
}

main "$@"
