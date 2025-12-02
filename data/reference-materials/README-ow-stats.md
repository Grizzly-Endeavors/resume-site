# OW-Stats: Overwatch Match Analytics Platform

A full-stack data analytics application for tracking and analyzing Overwatch 2 competitive performance using AI-powered screenshot parsing, interactive visualizations, and comprehensive statistical analysis.

## Technical Highlights

### AI/Machine Learning Integration
- **Google Gemini Vision AI Integration**: Implemented multimodal AI using Google's Gemini 2.0 Flash Lite model to parse game screenshots and extract structured match data
- **Structured Output with Pydantic**: Engineered type-safe data validation using Pydantic models with custom enum types and nested schema definitions
- **JSON Schema Generation**: Automated schema generation for AI model responses ensuring consistent data structure across the application
- **Error Handling & Validation**: Robust error detection for invalid screenshots, duplicates, and player identification failures

### Database Architecture
- **Relational Database Design**: Designed normalized SQLite database schema with foreign key relationships across 4 tables (heroes, maps, matches, match_heroes)
- **Complex SQL Queries**: Implemented advanced SQL queries featuring JOINs, GROUP BY aggregations, CTEs, and conditional expressions for statistical analysis
- **Object-Oriented Data Access Layer**: Built modular stats classes (RoleStats, HeroStats, MapTypeStats, MapStats) providing clean abstraction over raw SQL queries
- **Dynamic Filtering & Aggregation**: Created flexible query methods supporting win rate calculations, hero performance metrics, and map-specific analytics

### Frontend Development
- **Streamlit Framework**: Built interactive web UI using Streamlit with multi-tab navigation and responsive layouts
- **Data Visualization**: Implemented interactive charts using Altair (Vega-Lite) with custom encodings, sorting, tooltips, and color schemes
- **Real-time Data Updates**: Integrated live database queries with automatic UI refresh and state management
- **User Experience Design**: Developed intuitive input forms with validation, file upload handling, and visual feedback systems

### Data Engineering & Analytics
- **Statistical Computing**: Calculated complex metrics including win rates by role, hero, map type, and map with percentage-based performance indicators
- **Pandas Integration**: Leveraged Pandas DataFrames for efficient data transformation and chart rendering
- **Time Series Processing**: Implemented datetime handling with ISO 8601 formatting and human-readable date conversion
- **Aggregation Pipeline**: Built multi-stage data aggregation supporting top-N queries, best performer identification (min 3-10 matches threshold), and recent match history

## Key Features

### Match Input System
- Manual entry interface with cascading selection (Role → Heroes → Map Type → Maps)
- AI-powered screenshot upload accepting post-match summary images
- Automatic data extraction from visual content using computer vision
- Validation and error handling for user inputs

### Comprehensive Statistics Dashboard
- **Overview Tab**: Total matches, win/loss/draw breakdown, most played heroes/maps, win rates by role and map type
- **Role/Hero Analysis**: Per-role statistics, hero-specific win rates, best maps/map types for each hero
- **Map Analytics**: Map type performance, best heroes per map, historical match data

### Advanced Analytics
- Win rate calculations with minimum match thresholds to ensure statistical significance
- Best performer identification across multiple dimensions (hero, map, map type)
- Recent match history with hero composition tracking
- Interactive chart/table view toggles for different data presentation preferences

## Tech Stack

**Backend**
- Python 3.12
- SQLite3 with custom ORM layer
- Pydantic for data validation
- Google Generative AI SDK

**Frontend**
- Streamlit 1.44.1
- Altair/Vega-Lite for declarative visualizations
- Pandas for data manipulation

**Data & AI**
- Google Gemini 2.0 Flash Lite (multimodal vision model)
- PIL/Pillow for image handling
- JSON Schema for structured outputs

## Architecture Highlights

### Modular Design
- Separation of concerns: `database.py` (data layer), `ai.py` (ML integration), `ui.py` (presentation layer)
- Class-based stats modules for different entity types (Role, Hero, MapType, Map)
- Reusable query patterns with parameterized SQL

### Scalability Considerations
- Efficient database indexing through primary and foreign key constraints
- Lazy loading of statistics (computed on-demand)
- Chart rendering optimized with Altair's declarative approach

### Data Quality
- Enum-based outcome validation (Win/Loss/Draw)
- Foreign key constraints ensuring referential integrity
- Type hints throughout codebase for maintainability
- Pre-populated reference data (42 heroes, 26 maps across 5 game modes)

## Technical Accomplishments

1. **Full-Stack Development**: Designed and implemented complete data pipeline from AI-powered input → database storage → statistical analysis → interactive visualization

2. **AI Integration**: Successfully integrated cutting-edge multimodal AI for practical computer vision task, converting unstructured visual data into structured analytics

3. **Database Engineering**: Architected normalized relational schema supporting complex analytical queries with performant aggregations

4. **Statistical Analysis**: Built comprehensive analytics engine computing multi-dimensional performance metrics with statistical thresholds

5. **UI/UX Implementation**: Created intuitive, responsive web interface with dynamic data updates and multiple visualization modes

## Installation & Setup

### Prerequisites
- Python 3.12 or higher
- Google Gemini API key (for AI screenshot parsing feature)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/OW-Stats.git
   cd OW-Stats
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv

   # On Windows
   .venv\Scripts\activate

   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Google Gemini API key:
     ```
     GOOGLE_API_KEY=your_actual_api_key_here
     ```
   - Get your API key from: [Google AI Studio](https://aistudio.google.com/app/apikey)

5. **Run the application**
   ```bash
   streamlit run ui.py
   ```

6. **Access the application**
   - Open your browser and navigate to `http://localhost:8501`

### Configuration

The application uses environment variables for sensitive configuration:
- `GOOGLE_API_KEY`: Required for AI-powered screenshot parsing (optional if only using manual entry)

### Database

The application automatically creates a SQLite database (`overwatch_stats.db`) on first run with pre-populated hero and map data.

## Usage

### Manual Match Entry
1. Select your role (Tank/Damage/Support)
2. Choose the heroes you played
3. Select the map type and specific map
4. Select the match outcome (Win/Loss/Draw)
5. Click "Submit Match"

### AI Screenshot Upload
1. Enter your player name
2. Upload exactly two post-match screenshots:
   - Post-match summary screen
   - Post-match teams screen
3. Click "Submit Screenshots"
4. The AI will automatically extract match data

### Viewing Statistics
Navigate through the Stats tabs:
- **Overview**: Overall performance metrics, most played heroes/maps, win rates
- **Role/Hero**: Detailed statistics by role and individual heroes
- **Map**: Performance analysis by map type and specific maps

## Future Enhancement Opportunities

- RESTful API layer for external integrations
- Advanced ML models for performance prediction and recommendations
- Real-time match tracking via game API integration
- Export functionality (CSV, PDF reports)
- User authentication and multi-user support
- Time-series trend analysis and performance tracking over time

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).

## Disclaimer

This project is not affiliated with or endorsed by Blizzard Entertainment. Overwatch is a trademark of Blizzard Entertainment, Inc.

---

**Project Status**: Functional MVP with core analytics features implemented

**Development Period**: 2025 (Active Development)