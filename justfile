default:
    @just --list --list-prefix ...

# Format code
style:
    @echo "Formatting code..."
    poetry run poe lint

# Clean project and style code
clean: style
    @echo "Cleaning project..."
    bash helper_scripts/clean.sh 2> /dev/null

# Fix git untracked files
git-fix: clean
    @echo "Fixing git untracked files..."
    git rm -r --cached .
    git add .
    git commit -m "build: Fix untracked project files."

# Setup pre-commit hooks
setup-pre-commit: clean
    @echo "Setting up pre-commit hooks..."
    poetry run pre-commit install --install-hooks
    @echo "Setting up pre-commit commit-msg hooks..."
    poetry run pre-commit install --hook-type commit-msg

# Update project dependencies
update: clean
    poetry update --with dev
    poetry run pre-commit autoupdate

# Run tests
test: clean
    poetry run poe test

# Run tests with coverage
coverage: clean
    poetry run poe coverage

# Quick test no clean
qtest:
    poetry run poe quicktest

# Quick coverage no clean
qcoverage:
    poetry run poe quickcoverage

# Quick coverage with html report
coverage-html:
    poetry run poe htmlcov
    open htmlcov/index.html
