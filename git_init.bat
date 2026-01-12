@echo off
REM ============================================================
REM Git Initialization Script for ACC CAN Test Suite
REM ============================================================
REM This script initializes a Git repository and creates an
REM initial commit with all project files.
REM
REM Usage: Double-click or run from command prompt
REM ============================================================

echo.
echo ============================================================
echo   ACC CAN Test Suite - Git Initialization
echo ============================================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Git is not installed or not in PATH.
    echo Please install Git from https://git-scm.com/downloads
    pause
    exit /b 1
)

REM Check if already a git repo
if exist .git (
    echo WARNING: Git repository already exists in this directory.
    echo Skipping initialization.
    goto :commit
)

REM Initialize git repository
echo Initializing Git repository...
git init

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to initialize Git repository.
    pause
    exit /b 1
)

echo.
echo Git repository initialized successfully!
echo.

:commit
REM Create .gitignore if it doesn't exist
if not exist .gitignore (
    echo Creating .gitignore...
    (
        echo # Python
        echo __pycache__/
        echo *.py[cod]
        echo *$py.class
        echo *.so
        echo .Python
        echo venv/
        echo ENV/
        echo env/
        echo .venv/
        echo.
        echo # Testing
        echo .pytest_cache/
        echo htmlcov/
        echo .coverage
        echo coverage.xml
        echo *.cover
        echo.
        echo # IDE
        echo .idea/
        echo .vscode/
        echo *.swp
        echo *.swo
        echo.
        echo # Generated files
        echo test_results.json
        echo test_results_dashboard.html
        echo.
        echo # OS
        echo .DS_Store
        echo Thumbs.db
    ) > .gitignore
    echo .gitignore created.
)

REM Stage all files
echo.
echo Staging files...
git add .

REM Create initial commit
echo.
echo Creating initial commit...
git commit -m "Initial commit: ACC CAN Test Suite" -m "- Added CAN log parser (parse_log.py)" -m "- Added 5 test cases for ACC validation (test_cases.py)" -m "- Added pytest test suite (test_acc.py)" -m "- Added Plotly dashboard generator (dashboard.py)" -m "- Added orchestration script (run_all.py)" -m "- Added sample DBC and ASC log files" -m "- Added documentation and README"

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create commit.
    echo Make sure you have configured git user.name and user.email:
    echo   git config --global user.name "Your Name"
    echo   git config --global user.email "your@email.com"
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   SUCCESS! Git repository initialized with initial commit.
echo ============================================================
echo.
echo Next steps:
echo   1. Create a GitHub/GitLab repository
echo   2. Add remote: git remote add origin ^<repository-url^>
echo   3. Push: git push -u origin main
echo.
pause
