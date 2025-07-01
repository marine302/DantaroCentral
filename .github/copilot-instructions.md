# Dantaro Central - Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is the **Dantaro Central** server - a heavyweight central AI trading bot platform that provides market analysis, strategy recommendations, and bot configuration services to multiple lightweight user servers (DantaroEnterprise).

## Key Architecture Principles
- **Central Server Role**: Heavy computational tasks, AI/ML analysis, strategy calculation
- **User Server Communication**: Serve multiple DantaroEnterprise instances via RESTful APIs
- **Modular Design**: Clear separation of concerns with dedicated modules for AI, market analysis, and configuration
- **Scalable**: Designed to handle multiple user servers and high-frequency market data

## Technology Stack
- **Backend**: FastAPI with Python 3.9+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: Dedicated modules for market analysis and strategy generation
- **API**: RESTful APIs for user server communication
- **Authentication**: API key-based authentication for user servers

## Code Standards
- **Type Hints**: Mandatory for all functions and class methods
- **Error Handling**: Comprehensive try-catch blocks with proper logging
- **Documentation**: Docstrings for all public functions and classes
- **Testing**: Unit and integration tests for all critical components
- **Clean Code**: Follow PEP 8 and maintain modular, readable code

## Core Modules
1. **Market Analysis**: Real-time market data processing and technical analysis
2. **AI Strategy Engine**: Machine learning models for trading strategy recommendations
3. **Bot Configuration**: Centralized bot setup and parameter management
4. **User Server API**: Endpoints for DantaroEnterprise communication
5. **Data Pipeline**: ETL processes for market data and user analytics

## Development Guidelines
- Prioritize performance and scalability for heavy computational tasks
- Implement proper caching mechanisms for frequently accessed data
- Use async/await patterns for I/O operations
- Maintain strict API versioning for user server compatibility
- Implement comprehensive logging and monitoring

## Security Considerations
- API key authentication for all user server requests
- Rate limiting to prevent abuse
- Data validation and sanitization
- Secure handling of sensitive trading data
