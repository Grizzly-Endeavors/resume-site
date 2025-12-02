# OW-Stats (Overwatch Analytics Platform)
**Dates:** Ongoing
**Skills:** Python, Google Gemini Vision AI, Pydantic, SQLite, Streamlit, Altair, Data Visualization, Computer Vision, Database Design, Statistical Analysis

A full-stack data analytics application for tracking and analyzing Overwatch 2 competitive performance using AI-powered screenshot parsing, interactive visualizations, and comprehensive statistical analysis. Demonstrates sophisticated integration of multimodal AI, relational database design, and modern frontend development.

## Technical Achievements

**AI/Machine Learning Integration:**
- Integrated Google Gemini 2.0 Flash Lite multimodal AI to parse game screenshots and extract structured match data
- Engineered type-safe data validation using Pydantic models with custom enum types and nested schema definitions
- Implemented automated JSON schema generation for AI model responses ensuring consistent data structure
- Built robust error detection system handling invalid screenshots, duplicates, and player identification failures

**Database Architecture:**
- Designed normalized SQLite database schema with foreign key relationships across 4 tables (heroes, maps, matches, match_heroes)
- Implemented advanced SQL queries featuring JOINs, GROUP BY aggregations, CTEs, and conditional expressions for statistical analysis
- Built object-oriented data access layer with modular stats classes (RoleStats, HeroStats, MapTypeStats, MapStats) providing clean abstraction over raw SQL
- Created flexible query methods supporting win rate calculations, hero performance metrics, and map-specific analytics

**Frontend Development:**
- Built interactive web UI using Streamlit with multi-tab navigation and responsive layouts
- Implemented interactive charts using Altair (Vega-Lite) with custom encodings, sorting, tooltips, and color schemes
- Integrated real-time database queries with automatic UI refresh and state management
- Developed intuitive input forms with validation, file upload handling, and visual feedback systems

**Data Engineering & Analytics:**
- Calculated complex metrics including win rates by role, hero, map type, and map with percentage-based performance indicators
- Leveraged Pandas DataFrames for efficient data transformation and chart rendering
- Implemented datetime handling with ISO 8601 formatting and human-readable date conversion
- Built multi-stage data aggregation supporting top-N queries and best performer identification with statistical thresholds (minimum 3-10 matches)

## Key Features

**Match Input System:**
- Manual entry interface with cascading selection (Role → Heroes → Map Type → Maps)
- AI-powered screenshot upload accepting post-match summary images
- Automatic data extraction from visual content using computer vision
- Comprehensive validation and error handling for user inputs

**Statistics Dashboard:**
- Overview tab with total matches, win/loss/draw breakdown, most played heroes/maps, and win rates by role and map type
- Role/Hero analysis with per-role statistics, hero-specific win rates, and best maps/map types per hero
- Map analytics showing map type performance, best heroes per map, and historical match data
- Interactive chart/table view toggles for different data presentation preferences

**Advanced Analytics:**
- Win rate calculations with minimum match thresholds ensuring statistical significance
- Best performer identification across multiple dimensions (hero, map, map type)
- Recent match history with hero composition tracking

## Architecture & Code Quality

**Modular Design:**
- Separation of concerns: database.py (data layer), ai.py (ML integration), ui.py (presentation layer)
- Class-based stats modules for different entity types (Role, Hero, MapType, Map)
- Reusable query patterns with parameterized SQL

**Data Quality:**
- Enum-based outcome validation (Win/Loss/Draw)
- Foreign key constraints ensuring referential integrity
- Type hints throughout codebase for maintainability
- Pre-populated reference data (42 heroes, 26 maps across 5 game modes)

**Scalability:**
- Efficient database indexing through primary and foreign key constraints
- Lazy loading of statistics (computed on-demand)
- Chart rendering optimized with Altair's declarative approach

This project demonstrates full-stack development capabilities from AI-powered input to database storage to statistical analysis to interactive visualization, successfully converting unstructured visual data into actionable analytics.