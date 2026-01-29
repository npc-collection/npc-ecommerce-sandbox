# NPC E-commerce Sandbox - Quick Start Script
# This script helps you set up and run the project quickly

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  NPC E-commerce Sandbox Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker Desktop from https://www.docker.com/" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green

    # Check if OpenAI API key is set
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "OPENAI_API_KEY=sk-") {
        Write-Host "✓ OpenAI API key appears to be configured" -ForegroundColor Green
    } else {
        Write-Host "⚠ OpenAI API key not configured in .env file" -ForegroundColor Yellow
        Write-Host "  Please edit .env and add your OpenAI API key" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ .env file not found" -ForegroundColor Red
    Write-Host "  Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created. Please edit it and add your OpenAI API key" -ForegroundColor Green
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Installation Options" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Full setup (recommended for first time)" -ForegroundColor White
Write-Host "2. Start infrastructure only (Docker services)" -ForegroundColor White
Write-Host "3. Start application only (API + Dashboard)" -ForegroundColor White
Write-Host "4. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting full setup..." -ForegroundColor Cyan
        
        # Create virtual environment
        Write-Host ""
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        if (Test-Path "venv") {
            Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
        } else {
            python -m venv venv
            Write-Host "✓ Virtual environment created" -ForegroundColor Green
        }
        
        # Activate virtual environment
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & ".\venv\Scripts\Activate.ps1"
        
        # Upgrade pip
        Write-Host "Upgrading pip..." -ForegroundColor Yellow
        python -m pip install --upgrade pip --quiet
        Write-Host "✓ pip upgraded" -ForegroundColor Green
        
        # Install dependencies
        Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
        pip install -e ".[dev]" --quiet
        Write-Host "✓ Dependencies installed" -ForegroundColor Green
        
        # Start Docker services
        Write-Host ""
        Write-Host "Starting Docker services..." -ForegroundColor Yellow
        docker-compose up -d postgres redis
        Write-Host "✓ Docker services started" -ForegroundColor Green
        
        # Wait for services to be ready
        Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Check service status
        Write-Host ""
        Write-Host "Service Status:" -ForegroundColor Cyan
        docker-compose ps
        
        Write-Host ""
        Write-Host "=====================================" -ForegroundColor Green
        Write-Host "  Setup Complete!" -ForegroundColor Green
        Write-Host "=====================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "To start the application:" -ForegroundColor White
        Write-Host "  python main.py all" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Access points:" -ForegroundColor White
        Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "  Dashboard: http://localhost:8501" -ForegroundColor Cyan
        Write-Host ""
    }
    
    "2" {
        Write-Host ""
        Write-Host "Starting Docker services..." -ForegroundColor Cyan
        docker-compose up -d postgres redis
        Write-Host ""
        Write-Host "✓ Docker services started" -ForegroundColor Green
        Write-Host ""
        Write-Host "Service Status:" -ForegroundColor Cyan
        docker-compose ps
        Write-Host ""
        Write-Host "Optional services (pgAdmin, Redis Commander):" -ForegroundColor Yellow
        Write-Host "  docker-compose up -d pgadmin redis-commander" -ForegroundColor Cyan
        Write-Host ""
    }
    
    "3" {
        Write-Host ""
        Write-Host "Starting application..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Make sure Docker services are running first!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Starting API and Dashboard..." -ForegroundColor Yellow
        
        # Activate virtual environment if it exists
        if (Test-Path "venv\Scripts\Activate.ps1") {
            & ".\venv\Scripts\Activate.ps1"
        }
        
        python main.py all
    }
    
    "4" {
        Write-Host ""
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Host "Invalid choice. Exiting..." -ForegroundColor Red
        exit 1
    }
}
