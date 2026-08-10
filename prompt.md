
You are a senior AI engineer, full-stack developer, and expert UI/UX designer. Your task is to transform this existing web project into a production-ready, secure, and professional web application that can be deployed to a public hosting environment with a real database.

Please preserve the current project identity and overall structure as much as possible, but upgrade it into a complete web application with modern software engineering quality.

## Main Objective
Build a polished, realistic, and production-grade web app that includes:
- secure user authentication
- user registration and login
- email-based account flow
- protected API routes
- user dashboard after login
- profile management
- score/progress tracking
- quiz activity history
- AI chat history
- photo analysis history
- proper database integration
- bilingual interface (English and Indonesian)
- professional academic-friendly UI

## Important Constraints
1. Do not redesign the whole app drastically.
2. Keep the existing app concept and core flow, but refine the UI minimally and professionally.
3. Improve the current interface with cleaner spacing, better typography, better consistency, and modern polished styling.
4. Remove all informal, local, casual, or decorative text such as:
   - “made with love”
   - “sticker love”
   - any childish footer decoration
   - any non-professional local wording
5. Ensure all visible texts are professional, clean, and suitable for academic publication.
6. Add a language toggle for:
   - Indonesian
   - English
7. Keep the UI stable and avoid unnecessary structural changes.

## Required Functional Improvements
Implement the following production-grade functionality:

### 1. Authentication System
Create a real authentication system with:
- register page
- login page
- email-based registration
- secure password handling
- login session or JWT-based authentication
- protected routes for authenticated users only
- user logout

### 2. Database Migration
Do not rely only on local JSON storage for production.
Replace or upgrade the current data model to a real database-ready approach, ideally:
- PostgreSQL
- SQLAlchemy ORM
- or another realistic production database layer

The system should store:
- users
- user profiles
- quiz progress
- badges
- chat history
- image analysis records
- score history

### 3. Secure Backend Design
The backend must be secure and realistic:
- no hardcoded secrets
- use environment variables for API keys and credentials
- validate all incoming data
- sanitize file uploads
- apply rate limiting
- restrict CORS properly for production
- protect sensitive endpoints so they require authentication
- do not trust client-supplied user_id as the real identity source

### 4. UI/UX Refinement
Refine the current design by making only purposeful and minimal improvements:
- stronger visual hierarchy
- cleaner cards and sections
- polished buttons and forms
- more professional layout balance
- better spacing and readability
- improved responsive behavior
- consistent bilingual support

### 5. Production Readiness
Make the app suitable for public deployment:
- secure configuration
- clean project structure
- proper environment variable handling
- no placeholder or fake functionality
- reliable code organization
- no obvious syntax/runtime issues
- realistic deployment notes

## Technical Guidance
Use the current stack as the baseline if possible:
- FastAPI for backend
- suitable frontend files for UI
- environment-based configuration
- database-backed persistence
- secure password hashing

If a realistic improvement is needed, prefer:
- SQLAlchemy
- PostgreSQL
- bcrypt for password hashing
- JWT or secure session management
- proper response models and validation

## Output Expectations
Provide:
1. the updated project structure
2. the main code files that need to be changed
3. clean, working implementation
4. minimal but meaningful UI polishing
5. a concise deployment/setup guide
6. important production security notes

## Quality Bar
Before finalizing, verify that:
- the code is coherent
- the structure is maintainable
- there are no obvious syntax errors
- the implementation is secure enough for a real deployment scenario
- the result is suitable for academic review and public hosting

## Final Instruction
Do not produce incomplete or fake code. If something is uncertain, implement the safest and most realistic alternative. Make the app look credible, professional, secure, and publication-ready.
