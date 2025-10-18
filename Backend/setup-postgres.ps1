# PostgreSQL Quick Setup Script for Windows
# Run this from Backend directory: .\setup-postgres.ps1

Write-Host "=== Network Chatbot - PostgreSQL Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
$dockerAvailable = $false
try {
    docker --version | Out-Null
    $dockerAvailable = $true
    Write-Host "✓ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Choose setup method:" -ForegroundColor Cyan
Write-Host "1. Docker Compose (Recommended - Easy & Fast)"
Write-Host "2. Manual PostgreSQL Installation"
Write-Host "3. Exit"
Write-Host ""

$choice = Read-Host "Enter choice (1-3)"

switch ($choice) {
    "1" {
        if (-not $dockerAvailable) {
            Write-Host "Docker is not installed. Please install Docker Desktop:" -ForegroundColor Red
            Write-Host "https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
            exit 1
        }

        Write-Host ""
        Write-Host "Starting PostgreSQL with Docker Compose..." -ForegroundColor Cyan
        
        # Start services
        docker-compose up -d postgres redis
        
        Write-Host ""
        Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Check if services are running
        $postgresRunning = docker ps --filter "name=netops-postgres" --format "{{.Status}}" | Select-String "Up"
        
        if ($postgresRunning) {
            Write-Host "✓ PostgreSQL is running!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Database Configuration:" -ForegroundColor Cyan
            Write-Host "  Host: localhost" -ForegroundColor White
            Write-Host "  Port: 5432" -ForegroundColor White
            Write-Host "  Database: netops_db" -ForegroundColor White
            Write-Host "  User: netops_user" -ForegroundColor White
            Write-Host "  Password: netops_pass" -ForegroundColor White
            Write-Host ""
            Write-Host "Update your .env file with:" -ForegroundColor Yellow
            Write-Host "DATABASE_URL=postgresql://netops_user:netops_pass@localhost:5432/netops_db" -ForegroundColor White
            Write-Host ""
            
            # Update .env file
            $envFile = ".\.env"
            if (Test-Path $envFile) {
                Write-Host "Updating .env file..." -ForegroundColor Cyan
                $content = Get-Content $envFile -Raw
                $content = $content -replace "DATABASE_URL=.*", "DATABASE_URL=postgresql://netops_user:netops_pass@localhost:5432/netops_db"
                $content | Set-Content $envFile
                Write-Host "✓ .env file updated" -ForegroundColor Green
            }
            
            Write-Host ""
            Write-Host "Next steps:" -ForegroundColor Cyan
            Write-Host "1. Activate virtual environment: .venv\Scripts\activate" -ForegroundColor White
            Write-Host "2. Install dependencies: pip install -r requirements.txt" -ForegroundColor White
            Write-Host "3. Run migrations: cd netops_backend; python manage.py migrate" -ForegroundColor White
            Write-Host "4. Start server: python manage.py runserver" -ForegroundColor White
            Write-Host ""
            Write-Host "Optional: Start pgAdmin (web UI):" -ForegroundColor Cyan
            Write-Host "  docker-compose --profile tools up -d pgadmin" -ForegroundColor White
            Write-Host "  Access at: http://localhost:5050" -ForegroundColor White
            Write-Host "  Login: admin@netops.local / admin" -ForegroundColor White
        } else {
            Write-Host "✗ Failed to start PostgreSQL" -ForegroundColor Red
            Write-Host "Check logs: docker-compose logs postgres" -ForegroundColor Yellow
            exit 1
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "Manual PostgreSQL Installation:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "1. Download PostgreSQL from:" -ForegroundColor Yellow
        Write-Host "   https://www.postgresql.org/download/windows/" -ForegroundColor White
        Write-Host ""
        Write-Host "2. Or install via Chocolatey:" -ForegroundColor Yellow
        Write-Host "   choco install postgresql14" -ForegroundColor White
        Write-Host ""
        Write-Host "3. After installation, create database:" -ForegroundColor Yellow
        Write-Host "   psql -U postgres" -ForegroundColor White
        Write-Host ""
        Write-Host "   CREATE DATABASE netops_db;" -ForegroundColor Gray
        Write-Host "   CREATE USER netops_user WITH PASSWORD 'secure_password';" -ForegroundColor Gray
        Write-Host "   GRANT ALL PRIVILEGES ON DATABASE netops_db TO netops_user;" -ForegroundColor Gray
        Write-Host "   \q" -ForegroundColor Gray
        Write-Host ""
        Write-Host "4. Update .env file:" -ForegroundColor Yellow
        Write-Host "   DATABASE_URL=postgresql://netops_user:secure_password@localhost:5432/netops_db" -ForegroundColor White
        Write-Host ""
        Write-Host "See POSTGRESQL_MIGRATION.md for detailed instructions." -ForegroundColor Cyan
    }
    
    "3" {
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
