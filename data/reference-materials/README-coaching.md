# Overwatch Coaching Website

A production-grade Overwatch coaching platform built with Next.js 14, TypeScript, and PostgreSQL. This project demonstrates sophisticated full-stack development with advanced integrations, custom scheduling logic, real-time notifications, and enterprise-grade deployment automation.

## Overview

This application provides a complete coaching business platform with replay code submissions, custom appointment scheduling, Stripe payment processing, Discord notifications, and a comprehensive admin panel. The codebase showcases modern web development practices including type-safe validation, security hardening, containerization, and CI/CD automation.

### Technical Scope
- **31 API endpoints** with consistent patterns and error handling
- **7 database models** with strategic indexing and relationships
- **600+ line Discord integration** with 6 notification types
- **Multi-stage Docker build** with optimized production image
- **Automated CI/CD pipeline** with GitHub Actions
- **Custom scheduling algorithm** with timezone awareness
- **Background job system** using Next.js instrumentation
- **Comprehensive admin panel** with CRUD operations
- **Rate limiting** and security hardening throughout
- **Type-safe** end-to-end with TypeScript and Zod

## Key Features

### Replay Code Submission System
- Multi-rank submission support with flexible replay code handling
- Payment integration with Stripe for both synchronous and scheduled reviews
- Automatic Discord notifications to admin on new submissions
- Status workflow tracking (Awaiting Payment → Payment Received → In Progress → Completed)
- Friend code system for promotional discounts with usage tracking and expiry dates

### Custom Appointment Scheduling
- **Sophisticated availability system** with weekly recurring slots
- **Timezone-aware slot generation** using `date-fns-tz` (configurable timezone support)
- Exception management for bookings, holidays, and manual blocks
- **Overlap detection** preventing double-booking
- Smart slot generation with configurable duration intervals
- 15-minute buffer for past slots with real-time availability updates

### Automated Notification System
- **Discord bot integration** with singleton client pattern
- Multi-type notifications:
  - VOD request notifications with replay details sent to admin
  - Review completion notifications to users
  - Booking confirmations with session details
  - 24-hour and 30-minute reminders before sessions (both user and admin)
- **Background reminder service** running every 5 minutes via Next.js instrumentation
- Graceful error handling for disconnected users

### Blog System
- Rich markdown support with GitHub Flavored Markdown (`remark-gfm`)
- Syntax highlighting for code blocks (`rehype-highlight` + `highlight.js`)
- XSS protection via `rehype-sanitize`
- Custom React component rendering for all markdown elements
- Publish/draft status management with tag system
- Optimized caching headers (5-minute s-maxage + 10-minute stale-while-revalidate)

### Admin Panel
- Comprehensive submission management with search and filtering
- Blog editor with pagination (up to 100 posts per page)
- Availability slot management with overlap validation
- Booking management with status tracking
- Friend code management with use tracking
- Payment and refund tracking
- Discord integration testing tools

### Payment Processing
- **Stripe integration** with webhook signature verification
- Support for three product types (sync review, scheduled review, VOD request)
- Multi-event handling (checkout.session.completed, payment_intent events, charge.refunded)
- Complex state transitions tied to payment status
- Automatic availability slot cleanup on failed payments

### Security & Authentication
- **NextAuth.js v5** with dual authentication (Credentials + Discord OAuth)
- Rate limiting (5 attempts per 15 minutes) with email-based tracking
- JWT session strategy with 30-day expiration and httpOnly cookies
- Secure password hashing using bcryptjs (cost factor 10)
- Admin route protection via middleware
- Discord OAuth auto-enrollment into guild
- Comprehensive input validation using Zod schemas

## Tech Stack

### Core Framework
- **Next.js 14** with App Router and React Server Components
- **TypeScript** for type-safe development
- **React 18** with modern hooks and patterns

### Database & ORM
- **PostgreSQL 16** (Alpine-based Docker image)
- **Prisma ORM** with strategic indexing and relationship management
- 7 models with complex relationships and cascading operations
- Migration management with versioned schema changes

### Styling & UI
- **Tailwind CSS** with custom dark theme configuration
- **Lucide React** for iconography
- Responsive design with mobile-first approach
- Custom design system with purple accent colors

### Authentication & Security
- **NextAuth.js v5** (Auth.js) with JWT strategy
- **bcryptjs** for password hashing (cost factor 10)
- Discord OAuth integration
- Custom middleware for route protection
- Rate limiting with memory-based strategy (Redis-ready)

### Payment Processing
- **Stripe** integration with webhook support
- Checkout session creation for three product types
- Payment status tracking and refund handling

### Notifications & Integrations
- **Discord.js** bot integration with singleton pattern
- Discord OAuth for user identification
- Automated DM notifications and reminders
- Guild auto-enrollment

### Content Management
- **react-markdown** for markdown rendering
- **remark-gfm** for GitHub Flavored Markdown
- **rehype-highlight** + **highlight.js** for syntax highlighting
- **rehype-sanitize** for XSS protection
- Custom component mapping for all markdown elements

### Date & Time Management
- **date-fns** for date manipulation
- **date-fns-tz** for timezone-aware calculations
- EST timezone handling with UTC storage

### Validation & Error Handling
- **Zod** for schema validation and type inference
- Centralized API error handler with Prisma support
- Custom logger with environment-based levels
- Structured logging (JSON in production, pretty in development)

### Deployment & DevOps
- **Docker** with multi-stage builds (3 stages: deps, builder, runner)
- **Docker Compose** for service orchestration
- **Cloudflare Tunnel** for secure remote access
- **GitHub Actions** for CI/CD automation
- Self-hosted runner deployment
- Automated database migrations and admin setup

### Development Tools
- **ESLint** for code linting
- **Prettier** (implied by consistent formatting)
- **Prisma Studio** for database management
- Environment variable management with comprehensive .env.example

## Getting Started

### Prerequisites

- Node.js 20 LTS
- PostgreSQL 16 (or use Docker)
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies:
```bash
npm install
```

3. Copy `.env.example` to `.env` and fill in your environment variables:
```bash
cp .env.example .env
```

4. Set up the database:
```bash
npm run prisma:migrate
```

5. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run prisma:generate` - Generate Prisma Client
- `npm run prisma:migrate` - Run database migrations
- `npm run prisma:studio` - Open Prisma Studio

## Technical Architecture

### API Routes (31 endpoints)
The application features a comprehensive RESTful API with consistent patterns:

**Public API Routes:**
- `/api/auth/*` - NextAuth.js authentication endpoints (credentials + Discord OAuth)
- `/api/blog/*` - Blog post retrieval with optimized caching
- `/api/contact` - Contact form submission
- `/api/replay-submit` - Replay code submission with validation
- `/api/booking/*` - Availability slots and booking creation
- `/api/stripe/checkout` - Payment session creation
- `/api/webhooks/stripe` - Stripe webhook handler with signature verification

**Admin Protected API Routes:**
- `/api/admin/submissions/*` - CRUD operations on replay submissions
- `/api/admin/blog/*` - Blog management with pagination
- `/api/admin/availability/*` - Weekly slot and exception management
- `/api/admin/bookings/*` - Booking management with reminder tracking
- `/api/admin/friend-codes/*` - Promotional code management
- `/api/admin/config/google-analytics` - Configuration endpoints

**API Design Patterns:**
- Centralized error handling with proper HTTP status codes
- Rate limiting on sensitive endpoints
- Zod validation for all request bodies
- Consistent response formats
- Request logging with structured output

### Database Schema

7 Prisma models with strategic relationships:

**Core Models:**
- **ReplaySubmission** - Replay code submissions with status workflow
  - Relationships: ReplayCode[], Booking?, Payment?
  - Indexed: status, email, createdAt, submissionId
- **ReplayCode** - Individual replay codes associated with submissions
  - Cascading delete on submission removal
- **Booking** - Appointment bookings with reminder tracking
  - Relationships: ReplaySubmission?, Payment?
  - Indexed: userId, dateTime, status
  - Tracks: reminderSent24h, reminderSent30m timestamps
- **Payment** - Stripe payment tracking
  - Status enum: PENDING → PROCESSING → SUCCEEDED → REFUNDED
  - Links to submissions and bookings

**Admin & Configuration:**
- **Admin** - Admin accounts with hashed passwords
  - Indexed: email (unique)
- **AvailabilitySlot** - Weekly recurring availability schedule
  - Fields: dayOfWeek (0-6), startTime, endTime, duration
  - Indexed: dayOfWeek, startTime
- **AvailabilityException** - Specific date blocks and bookings
  - Types: BOOKING, BLOCKED, HOLIDAY
  - Indexed: date

### Background Services

**Reminder Service** ([lib/reminder-service.ts](lib/reminder-service.ts)):
- Runs every 5 minutes via Next.js instrumentation hook
- Checks for upcoming bookings in 24-hour and 30-minute windows
- Sends Discord DMs to users and admin
- Updates reminder tracking flags (reminderSent24h, reminderSent30m)
- Graceful error handling per booking (continues on failure)

**Discord Bot** ([lib/discord.ts](lib/discord.ts)):
- Singleton client pattern preventing multiple instances
- 600+ lines of notification logic
- Functions:
  - `sendVodRequestNotification()` - Admin notification on submission
  - `sendReviewReadyNotification()` - User notification on completion
  - `sendBookingConfirmationNotification()` - Booking confirmation
  - `send24HourReminder()` / `send30MinuteReminder()` - User reminders
  - `send30MinuteAdminReminder()` - Admin reminders
- Handles disconnected users gracefully

### Security Features

**Authentication Flow:**
1. NextAuth.js handles authentication with dual providers
2. JWT tokens stored in httpOnly cookies (30-day expiration)
3. Middleware checks authentication on admin routes
4. Rate limiter tracks login attempts by email (5 per 15 minutes)
5. Discord OAuth auto-enrolls users in guild

**Input Validation:**
- Centralized Zod schemas in [lib/validations/](lib/validations/)
- Separate validators: auth, booking, blog, availability, contact, admin
- Type-safe parsing with detailed error messages
- Reusable primitive validators

**Error Handling:**
- API error handler supports Prisma and Zod errors
- Proper HTTP status codes (400, 401, 403, 404, 409, 429, 500, 503)
- User-friendly messages without leaking sensitive details
- Structured logging for debugging

### Scheduling Algorithm

The availability system ([api/booking/available-slots/route.ts](app/api/booking/available-slots/route.ts)) implements sophisticated slot generation:

1. **Load weekly recurring slots** from AvailabilitySlot table
2. **Generate time slots** for requested date range:
   - Split each availability window by duration (15/30/60 minutes)
   - Convert EST times to UTC for storage
3. **Filter out past slots** with 15-minute buffer
4. **Load exceptions** (bookings, blocks, holidays) for date range
5. **Check conflicts** for each generated slot
6. **Return available slots** in chronological order

**Timezone Handling:**
- Uses `date-fns-tz` for timezone-aware calculations
- Configurable timezone (currently EST/America/New_York)
- Proper conversion between local time and UTC storage
- Prevents edge cases at timezone boundaries

### Payment Webhook Flow

Stripe webhook handler ([api/webhooks/stripe/route.ts](app/api/webhooks/stripe/route.ts)):

1. **Verify signature** using Stripe webhook secret
2. **Handle multiple event types:**
   - `checkout.session.completed` - Initial payment received
   - `payment_intent.succeeded` - Payment processing successful
   - `payment_intent.payment_failed` - Payment failed, cleanup slots
   - `charge.refunded` - Refund processed
3. **Update submission status** based on payment state
4. **Send Discord notifications** on payment success
5. **Cleanup availability exceptions** on failed payments
6. **Complex state transitions** with proper error handling

### Project Structure

```
.
├── app/                           # Next.js App Router
│   ├── api/                      # 31 API route handlers
│   │   ├── auth/                # NextAuth.js endpoints
│   │   ├── admin/               # Admin-protected routes
│   │   ├── booking/             # Availability and booking
│   │   ├── blog/                # Blog retrieval
│   │   ├── contact/             # Contact form
│   │   ├── replay-submit/       # Submission endpoint
│   │   ├── stripe/              # Stripe checkout
│   │   └── webhooks/            # Webhook handlers
│   ├── admin/                    # Admin dashboard pages
│   │   ├── submissions/         # Submission management
│   │   ├── blog/                # Blog editor
│   │   ├── availability/        # Schedule management
│   │   ├── bookings/            # Booking management
│   │   └── friend-codes/        # Promo code management
│   ├── blog/                     # Public blog pages
│   ├── booking/                  # Booking flow pages
│   ├── login/                    # Authentication pages
│   ├── layout.tsx               # Root layout with providers
│   ├── page.tsx                 # Homepage
│   └── globals.css              # Global styles
├── components/                   # React components
│   ├── ui/                      # Reusable UI components
│   ├── forms/                   # Form components with validation
│   ├── admin/                   # Admin-specific components
│   ├── blog/                    # Blog rendering (BlogContent.tsx)
│   └── layout/                  # Layout components
├── lib/                          # Core utilities and business logic
│   ├── auth.ts                  # NextAuth.js configuration
│   ├── auth-helpers.ts          # Password hashing utilities
│   ├── discord.ts               # Discord bot integration (600+ lines)
│   ├── reminder-service.ts      # Background reminder job
│   ├── rate-limiter.ts          # Rate limiting implementation
│   ├── api-error-handler.ts     # Centralized error handling
│   ├── logger.ts                # Logging utility
│   ├── prisma.ts                # Prisma client singleton
│   ├── validations/             # Zod validation schemas
│   │   ├── auth.ts             # Authentication validation
│   │   ├── booking.ts          # Booking validation
│   │   ├── blog.ts             # Blog validation
│   │   ├── availability.ts     # Availability validation
│   │   └── primitives.ts       # Reusable validators
│   ├── utils.ts                 # Helper functions
│   └── types.ts                 # TypeScript types
├── prisma/                       # Database
│   ├── schema.prisma            # Schema with 7 models, indexes
│   └── migrations/              # Versioned migrations
├── public/                       # Static assets
├── scripts/                      # Utility scripts
│   └── create-admin.ts          # Admin account creation
├── .github/workflows/            # CI/CD
│   └── deploy.yml               # Automated deployment
├── Dockerfile                    # Multi-stage build (3 stages)
├── docker-compose.yml            # Service orchestration
├── instrumentation.ts            # Server initialization hook
└── middleware.ts                 # Auth middleware
```

## Design System

The application uses a dark theme with purple accents:

- **Primary Background**: `#0f0f23`
- **Surface**: `#1a1a2e`
- **Purple Primary**: `#8b5cf6`
- **Purple Hover**: `#a78bfa`
- **Text Primary**: `#e5e7eb`
- **Text Secondary**: `#9ca3af`

## Deployment Architecture

### Docker Configuration

**Multi-stage Dockerfile** ([Dockerfile](Dockerfile)):
1. **deps stage**: Install dependencies with necessary system packages (libc6-compat)
2. **builder stage**: Build Next.js application with Prisma generation
3. **runner stage**: Minimal production image
   - Alpine-based Node.js 20
   - Non-root user (nextjs:nodejs)
   - Proper cache permissions for Next.js
   - Exposed port 3000

**Docker Compose** ([docker-compose.yml](docker-compose.yml)):
- **PostgreSQL service**:
  - Alpine-based PostgreSQL 16
  - Health check with 10-second intervals
  - Volume persistence for data
  - Custom IPAM configuration (192.168.16.0/20)
- **Next.js application service**:
  - Depends on database health
  - Environment variable injection
  - Port mapping (3000:3000)
- **Cloudflare Tunnel**:
  - Secure remote access without exposing ports
  - Token-based authentication

### CI/CD Pipeline

**GitHub Actions Workflow** ([.github/workflows/deploy.yml](.github/workflows/deploy.yml)):
1. **Self-hosted runner** deployment on push to production branch
2. **Automated environment setup**:
   - Generate .env file from GitHub Secrets (20+ variables)
   - Inject database credentials, API keys, tokens
3. **Container orchestration**:
   - Pull latest images
   - Rebuild Next.js application
   - Start services with proper dependency order
4. **Database management**:
   - Run Prisma migrations automatically
   - Create admin account if not exists (using scripts/create-admin.ts)
5. **Health validation**:
   - Verify service startup
   - Check database connectivity

**Security Features:**
- All secrets stored in GitHub Secrets
- No hardcoded credentials in repository
- Environment variables injected at runtime
- Proper permission management in containers

### Environment Configuration

Comprehensive `.env.example` with 20+ required variables:
- **Database**: PostgreSQL connection string
- **NextAuth**: URL, secret (OpenSSL-generated)
- **Discord**: Bot token, OAuth client ID/secret, guild ID, admin user ID
- **Stripe**: Secret key, publishable key, webhook secret, 3 price IDs
- **Admin**: Initial admin email and password (bcrypt hashed)
- **Cloudflare**: Tunnel token
- **Analytics**: Google Analytics ID

### Deployment Process

1. Push to production branch triggers GitHub Actions
2. Runner pulls latest code and secrets
3. Docker Compose builds and starts services
4. Database migrations run automatically
5. Admin account created if needed
6. Application accessible via Cloudflare Tunnel
7. Background services (reminder job) start automatically

See [PROJECT_SPEC.md](PROJECT_SPEC.md) for detailed deployment instructions.

## Performance Optimizations

### Caching Strategy
- **Blog posts**: HTTP caching with `s-maxage=300, stale-while-revalidate=600`
- **Static assets**: Next.js automatic optimization
- **Image optimization**: Next.js Image component with lazy loading

### Database Optimizations
- Strategic indexes on frequently queried fields
- Selective field selection (excluding content in list views)
- Efficient relationship includes (only load what's needed)
- Connection pooling via Prisma

### Rate Limiting
- Memory-based limiter with automatic cleanup
- Per-email tracking for login attempts (5 per 15 minutes)
- Redis-ready architecture for horizontal scaling
- Prevents brute force attacks and abuse

## Notable Technical Achievements

### Custom Scheduling System
Built from scratch without using external scheduling libraries:
- Weekly recurring availability with flexible time slots
- Exception-based conflict management (bookings, holidays, blocks)
- Timezone-aware calculations with EST/UTC conversion
- Configurable slot duration (15/30/60 minutes)
- Prevents overbooking with sophisticated conflict detection
- Real-time availability updates with 15-minute buffer

### Background Job System
Implemented using Next.js instrumentation hook:
- Runs reminder service every 5 minutes without external cron
- Stateful tracking with database-backed reminder flags
- Graceful error handling per booking (doesn't halt on failure)
- Multi-window reminders (24-hour and 30-minute)
- Sends notifications to both users and admin

### Discord Bot Integration
Production-ready Discord integration with advanced features:
- Singleton pattern preventing multiple client instances
- Auto-enrollment in Discord guild during OAuth flow
- Multi-type notification system (6 different notification types)
- Async delivery without blocking API responses
- Graceful handling of disconnected/deleted users
- DM-based notifications with rich formatting

### Payment Webhook Architecture
Robust Stripe integration with complex state management:
- Signature verification for webhook security
- Multi-event handling (5 different event types)
- State machine implementation for submission status
- Automatic slot cleanup on payment failure
- Transaction-safe database updates
- Notification triggers on payment success

### Rate Limiting Implementation
Custom rate limiter built for production use:
- Memory-based with automatic cleanup (Redis-ready)
- Support for both IP-based and identifier-based limiting
- Configurable time windows and attempt thresholds
- Prevents brute force attacks on authentication
- Applied to sensitive endpoints (login, submission)

## Development Best Practices

### Type Safety
- Full TypeScript coverage across codebase
- Zod for runtime validation with type inference
- Prisma for type-safe database queries
- No `any` types (strict mode enabled)
- Type-safe environment variables

### Error Handling
- Centralized API error handler
- Consistent error response format
- Proper HTTP status codes (400, 401, 403, 404, 409, 429, 500, 503)
- User-friendly messages without leaking implementation details
- Structured logging for debugging (JSON in production)
- Prisma and Zod error translation

### Code Organization
- Feature-based folder structure in [app/](app/) directory
- Separation of concerns (UI, business logic, data access)
- Reusable components in [components/ui/](components/ui/)
- Centralized utilities in [lib/](lib/) directory
- Clear naming conventions and consistent patterns

### Security Practices
- NextAuth.js v5 for authentication
- JWT with httpOnly cookies (no localStorage)
- bcrypt password hashing (cost factor 10)
- Rate limiting on sensitive endpoints
- Input validation on all API routes
- Zod schema validation for type safety
- Stripe webhook signature verification
- No hardcoded secrets (environment variables only)
- Non-root Docker user (security best practice)

### Testing Considerations
- Type-safe API routes ready for integration testing
- Zod schemas can be reused for test fixtures
- Docker environment suitable for E2E testing
- Prisma Studio for database inspection
- Structured logging aids debugging
- Separation of concerns enables unit testing

## License

Private project - All rights reserved
