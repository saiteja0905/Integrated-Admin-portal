#!/bin/bash

# Docker Helper Script for Shidhaan Application
# This script provides convenient commands for managing the Docker environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Main commands
case "$1" in
    start|up)
        print_header "Starting Shidhaan Application"
        check_docker
        docker-compose up -d
        print_success "Services started in detached mode"
        print_info "Access the app at http://localhost:8000"
        print_info "Access MongoDB Express at http://localhost:8081"
        ;;
    
    build)
        print_header "Building Shidhaan Application"
        check_docker
        docker-compose build --no-cache
        print_success "Build completed"
        ;;
    
    rebuild)
        print_header "Rebuilding and Restarting Shidhaan Application"
        check_docker
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        print_success "Services rebuilt and restarted"
        ;;
    
    stop|down)
        print_header "Stopping Shidhaan Application"
        check_docker
        docker-compose down
        print_success "Services stopped"
        ;;
    
    restart)
        print_header "Restarting Shidhaan Application"
        check_docker
        docker-compose restart
        print_success "Services restarted"
        ;;
    
    logs)
        print_header "Viewing Application Logs"
        check_docker
        if [ -z "$2" ]; then
            docker-compose logs -f
        else
            docker-compose logs -f "$2"
        fi
        ;;
    
    status|ps)
        print_header "Service Status"
        check_docker
        docker-compose ps
        ;;
    
    shell)
        print_header "Opening Shell in App Container"
        check_docker
        docker-compose exec app bash
        ;;
    
    db-shell|mongo)
        print_header "Opening MongoDB Shell"
        check_docker
        docker-compose exec mongodb mongosh -u admin -p password123
        ;;
    
    create-users|demo)
        print_header "Creating Demo Users"
        check_docker
        docker-compose exec app python create_demo_users.py
        print_success "Demo users created"
        ;;
    
    clean)
        print_header "Cleaning Docker Resources"
        print_warning "This will remove all containers, volumes, and images"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            docker system prune -a -f
            print_success "Cleanup completed"
        else
            print_info "Cleanup cancelled"
        fi
        ;;
    
    health)
        print_header "Health Check"
        check_docker
        print_info "Checking backend health..."
        if curl -f -s http://localhost:8000/api/health > /dev/null; then
            print_success "Backend is healthy"
        else
            print_error "Backend is not responding"
        fi
        ;;
    
    backup-db)
        print_header "Backing Up Database"
        check_docker
        BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        docker-compose exec -T mongodb mongodump \
            --username admin \
            --password password123 \
            --authenticationDatabase admin \
            --archive > "$BACKUP_DIR/backup.archive"
        print_success "Database backed up to $BACKUP_DIR"
        ;;
    
    restore-db)
        print_header "Restoring Database"
        check_docker
        if [ -z "$2" ]; then
            print_error "Please provide backup file path"
            print_info "Usage: $0 restore-db <backup-file>"
            exit 1
        fi
        if [ ! -f "$2" ]; then
            print_error "Backup file not found: $2"
            exit 1
        fi
        docker-compose exec -T mongodb mongorestore \
            --username admin \
            --password password123 \
            --authenticationDatabase admin \
            --archive < "$2"
        print_success "Database restored from $2"
        ;;
    
    reset-db)
        print_header "Resetting Database"
        print_warning "This will DELETE all data in the database"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            docker-compose up -d
            sleep 10
            docker-compose exec app python create_demo_users.py
            print_success "Database reset and demo users created"
        else
            print_info "Reset cancelled"
        fi
        ;;
    
    help|*)
        print_header "Shidhaan Docker Helper"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start, up          - Start all services in detached mode"
        echo "  build              - Build Docker images"
        echo "  rebuild            - Rebuild images and restart services"
        echo "  stop, down         - Stop all services"
        echo "  restart            - Restart all services"
        echo "  logs [service]     - View logs (optionally for specific service)"
        echo "  status, ps         - Show service status"
        echo "  shell              - Open bash shell in app container"
        echo "  db-shell, mongo    - Open MongoDB shell"
        echo "  create-users, demo - Create demo users"
        echo "  health             - Check backend health"
        echo "  backup-db          - Backup MongoDB database"
        echo "  restore-db <file>  - Restore database from backup"
        echo "  reset-db           - Reset database and create demo users"
        echo "  clean              - Clean all Docker resources (⚠️ destructive)"
        echo "  help               - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start           # Start services"
        echo "  $0 logs app        # View app logs"
        echo "  $0 rebuild         # Rebuild and restart"
        echo "  $0 create-users    # Create demo users"
        echo ""
        ;;
esac

exit 0

