# CI/CD Pipeline Documentation

This project includes a comprehensive CI/CD pipeline using GitHub Actions that automatically runs tests, code quality checks, and deployment processes.

## Workflows

### 1. Test Suite (`test.yml`)
**Triggers:** Push to `main`/`develop`, Pull requests to `main`

**What it does:**
- Runs all pytest tests with verbose output
- Generates test coverage reports
- Uploads coverage to Codecov
- Uses Python 3.13

**Key features:**
- Caches pip dependencies for faster builds
- Runs tests with coverage reporting
- Fails fast on test failures

### 2. Code Quality (`code-quality.yml`)
**Triggers:** Push to `main`/`develop`, Pull requests to `main`

**What it does:**
- Runs Black code formatter checks
- Runs isort import sorting checks
- Runs flake8 linting
- Optional mypy type checking

**Key features:**
- Ensures consistent code formatting
- Checks import organization
- Validates code style and complexity

### 3. Full CI/CD Pipeline (`ci.yml`)
**Triggers:** Push to `main`/`develop`, Pull requests to `main`

**What it does:**
- Runs tests on multiple Python versions (3.11, 3.12, 3.13)
- Performs security checks with Safety and Bandit
- Builds and validates the application
- Deploys to staging (develop branch)
- Deploys to production (main branch)

**Key features:**
- Multi-version Python testing
- Security vulnerability scanning
- Automated deployment to different environments

### 4. Deployment (`deploy.yml`)
**Triggers:** Push to `main`, Manual trigger

**What it does:**
- Runs tests before deployment
- Builds Docker image (example)
- Deploys to production
- Runs health checks

**Key features:**
- Requires manual approval for production deployment
- Includes pre-deployment testing
- Health check validation

## Configuration Files

### `pytest.ini`
- Configures pytest behavior
- Sets test discovery patterns
- Configures warnings and output format
- Defines custom markers for test categorization

### `requirements.txt`
- Updated with `pytest-cov` for coverage reporting
- Includes all necessary testing dependencies

## Environment Variables

The workflows use GitHub's built-in environment variables and secrets. For production deployment, you may need to configure:

- `SENTRY_DSN` - Sentry error monitoring
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `RESEND_API_KEY` - Email service API key

## Local Development

To run the same checks locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html

# Run code quality checks
black --check .
isort --check-only .
flake8 .
```

## Workflow Status

You can view the status of all workflows in the GitHub Actions tab of your repository. Each workflow will show:

- ✅ Success (green)
- ❌ Failure (red)
- ⏳ In Progress (yellow)
- ⏸️ Cancelled (grey)

## Customization

### Adding New Tests
Simply add new test files to the `tests/` directory following the naming convention `test_*.py`.

### Modifying Triggers
Edit the `on:` section in any workflow file to change when workflows run.

### Adding Deployment Steps
Modify the deployment workflows to include your specific deployment commands (Docker, Kubernetes, cloud providers, etc.).

### Environment-Specific Configuration
Use GitHub Environments to configure different settings for staging vs production deployments.

## Troubleshooting

### Common Issues

1. **Tests failing in CI but passing locally**
   - Check Python version differences
   - Ensure all dependencies are in requirements.txt
   - Verify environment variables are set

2. **Code quality checks failing**
   - Run `black .` to format code
   - Run `isort .` to organize imports
   - Fix flake8 warnings

3. **Deployment failures**
   - Check environment variables and secrets
   - Verify deployment permissions
   - Review deployment logs

### Getting Help

- Check the GitHub Actions logs for detailed error messages
- Review the workflow files for configuration issues
- Ensure all required secrets are configured in GitHub repository settings
