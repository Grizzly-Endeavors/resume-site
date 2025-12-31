# Overwatch Coaching Platform
**Dates:** Ongoing
**Skills:** Next.js 14, TypeScript, React, PostgreSQL, Prisma ORM, NextAuth.js, Stripe, Discord.js, Docker, GitHub Actions, Tailwind CSS, Zod, Cloudflare Tunnel

A production-grade Overwatch coaching platform featuring replay code submissions, custom appointment scheduling, Stripe payment processing, Discord notifications, and comprehensive admin panel. Demonstrates sophisticated full-stack development with advanced integrations, custom scheduling logic, real-time notifications, and enterprise-grade deployment automation. Available at coaching.bearflinn.com. Repo: https://github.com/Grizzly-Endeavors/coaching-website

## Technical Achievements

**Full-Stack Application Architecture:**
- Architected complete web application using Next.js 14 with App Router and React Server Components
- Built 31 API endpoints with consistent patterns, centralized error handling, and proper HTTP status codes
- Designed 7 Prisma database models with strategic indexing and complex relationships
- Implemented comprehensive type safety with TypeScript and Zod validation throughout entire codebase
- Created responsive dark theme UI using Tailwind CSS with custom purple accent design system

**Custom Scheduling System:**
- Built from-scratch appointment scheduling without external libraries
- Implemented weekly recurring availability with flexible time slots (15/30/60 minute durations)
- Developed timezone-aware slot generation using date-fns-tz with EST/UTC conversion
- Created exception-based conflict management system for bookings, holidays, and manual blocks
- Engineered sophisticated overlap detection preventing double-booking
- Implemented real-time availability updates with 15-minute buffer for past slots

**Payment Processing Integration:**
- Integrated Stripe with webhook signature verification for secure payment processing
- Implemented support for three product types (sync review, scheduled review, VOD request)
- Built multi-event handler supporting checkout.session.completed, payment_intent events, and charge.refunded
- Designed complex state transitions tied to payment status
- Developed automatic availability slot cleanup on failed payments
- Created payment and refund tracking system

**Discord Bot Integration:**
- Built production-ready 600+ line Discord integration with singleton client pattern
- Implemented 6 notification types: VOD requests, review completion, booking confirmations, 24-hour reminders, 30-minute reminders for users and admin
- Developed async delivery system not blocking API responses
- Created graceful error handling for disconnected/deleted users
- Enabled automatic Discord guild enrollment during OAuth flow
- Built DM-based notification system with rich formatting

**Background Job System:**
- Implemented reminder service using Next.js instrumentation hook running every 5 minutes
- Designed stateful tracking with database-backed reminder flags (reminderSent24h, reminderSent30m)
- Built multi-window reminder system checking 24-hour and 30-minute windows
- Implemented graceful error handling per booking without halting on failures
- Created notification system sending to both users and admin

**Authentication & Security:**
- Integrated NextAuth.js v5 with dual authentication providers (Credentials + Discord OAuth)
- Implemented rate limiting (5 attempts per 15 minutes) with email-based tracking
- Configured JWT session strategy with 30-day expiration and httpOnly cookies
- Applied secure password hashing using bcryptjs (cost factor 10)
- Built admin route protection via middleware
- Created comprehensive input validation using Zod schemas

**Blog System:**
- Implemented rich markdown support with GitHub Flavored Markdown (remark-gfm)
- Added syntax highlighting for code blocks using rehype-highlight and highlight.js
- Configured XSS protection via rehype-sanitize
- Built custom React component rendering for all markdown elements
- Developed publish/draft status management with tag system
- Optimized with caching headers (5-minute s-maxage + 10-minute stale-while-revalidate)

**DevOps & Deployment:**
- Created multi-stage Docker build with 3 stages (deps, builder, runner) for optimized production image
- Configured Docker Compose for service orchestration with PostgreSQL 16 and Cloudflare Tunnel
- Built automated CI/CD pipeline with GitHub Actions on self-hosted runner
- Implemented automated database migrations and admin account setup
- Generated environment configuration from 20+ GitHub Secrets at runtime
- Configured health validation for service startup and database connectivity

**Database Design:**
- Designed normalized schema with strategic relationships and cascade operations
- Created 7 models: ReplaySubmission, ReplayCode, Booking, Payment, Admin, AvailabilitySlot, AvailabilityException
- Implemented strategic indexes on frequently queried fields (status, email, createdAt, dateTime, dayOfWeek)
- Built complex query optimization with selective field selection and efficient relationship includes
- Configured foreign key constraints ensuring referential integrity

**Admin Panel:**
- Built comprehensive submission management with search and filtering
- Created blog editor with pagination (up to 100 posts per page)
- Developed availability slot management with overlap validation
- Implemented booking management with status tracking and reminder flags
- Built friend code management with usage tracking and expiry dates
- Created payment and refund tracking interface

## Architecture & Code Quality

**API Design Patterns:**
- Centralized error handling with Prisma and Zod error translation
- Rate limiting on sensitive endpoints
- Consistent response formats across all endpoints
- Request logging with structured output (JSON in production, pretty in development)

**Performance Optimizations:**
- HTTP caching strategy for blog posts (s-maxage=300, stale-while-revalidate=600)
- Database connection pooling via Prisma
- Efficient relationship loading with selective includes
- Strategic database indexing
- Next.js automatic static asset optimization

**Security Best Practices:**
- No hardcoded secrets (environment variables only)
- JWT with httpOnly cookies (no localStorage)
- Stripe webhook signature verification
- Input validation on all API routes
- Non-root Docker user for container security
- Proper permission management in containers

**Development Practices:**
- Full TypeScript coverage with strict mode enabled
- Type-safe database queries with Prisma
- No any types throughout codebase
- Feature-based folder structure in app directory
- Separation of concerns (UI, business logic, data access)
- Reusable components and centralized utilities
- Clear naming conventions and consistent patterns

This project demonstrates enterprise-grade full-stack development, complex third-party integrations, custom algorithm implementation, and production deployment automation at scale.