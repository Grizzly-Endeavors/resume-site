# The Factory (Simulation Game)
**Dates:** Ongoing
**Skills:** Rust, Bevy ECS Engine, Game Systems Design, Pathfinding Algorithms, Entity-Component-System Architecture, Data-Driven Design, Performance Optimization

A sophisticated factory simulation game built in Rust using the Bevy game engine, demonstrating advanced game architecture patterns and complex systems coordination. Players build and manage interconnected production facilities, coordinate autonomous workers, and scale factory operations through progressive automation.

## Technical Achievements

**Advanced Pathfinding System:**
- Implemented BFS (breadth-first search) algorithm for optimal path finding across the factory grid
- Developed network-aware navigation system where workers traverse only connected infrastructure
- Engineered emergency displacement logic using expanding square search patterns to relocate stranded workers
- Pre-validated network connectivity before pathfinding execution to optimize performance

**Intelligent Task Assignment System:**
- Built priority-based task queuing supporting Critical, High, Medium, and Low priority levels
- Implemented multi-task sequences enabling complex workflows (pickup → transport → dropoff chains)
- Designed state machine pattern for clean worker state management (Idle/Working transitions)
- Developed orphaned reference cleanup system with automatic validation of entity references
- Enabled dynamic task reassignment with mid-execution interruption and proper cleanup

**Network Connectivity System:**
- Architected dual-layer network model: Core Network (hubs + connectors for pathfinding) and Extended Network (core + adjacent buildings for operations)
- Implemented flood fill algorithm using BFS for connectivity propagation from network hubs
- Enabled dynamic real-time recalculation on building placement and removal events

**Modular Building System:**
- Created data-driven building configuration using RON (Rusty Object Notation) format
- Designed component-based assembly with dynamic component composition at spawn time
- Implemented power generation/consumption with grid balancing mechanics
- Built compute resource management and inventory systems (Storage/Sender/Requester/Producer)
- Developed recipe crafting system supporting both single and multi-recipe crafters
- Enabled multi-cell building support for structures spanning multiple grid positions

**Production & Crafting System:**
- Engineered recipe-based manufacturing with timer-driven crafting and input/output validation
- Implemented smart inventory management with transfer validation and capacity limits
- Built automatic logistics task generation based on inventory state and production requirements

**Power & Compute Grid Systems:**
- Developed real-time resource tracking for global capacity, usage, and availability monitoring
- Integrated operational status system where only functional buildings contribute to generation
- Designed three-tier architecture: Producers → Consumers → Global Grid

**Sophisticated UI System:**
- Implemented interactive framework with selection, hover, and click state management
- Built dynamic styling with three-state visual feedback system
- Created exclusive selection groups with radio button-like behavior
- Developed context-aware menus with building-specific interaction panels

## Architecture & Design

**Plugin-Based Design:**
Leveraged Bevy's plugin architecture for clean module separation across 8 major systems: GridPlugin (coordinate transformations), ResourcesPlugin (asset management), MaterialsPlugin (items and recipes), SystemsPlugin (infrastructure), BuildingsPlugin (production), WorkersPlugin (Workers and tasks), UIPlugin (interactions), and CameraPlugin (viewport management).

**System Set Ordering:**
Implemented precise control over system execution order: GridUpdate → ResourceSpawning → SystemsUpdate → DomainOperations → UIUpdate

**Key Design Patterns:**
- Entity-Component-System (ECS) paradigm heavily leveraged throughout
- Event-driven architecture with decoupled systems communicating via events
- State machines for worker states, task statuses, and UI selection behavior
- Data-driven design with configuration-based building and recipe definitions
- Validation pipeline using Request → Validate → Execute pattern for all state changes

## Code Quality & Scale

- **Production-quality codebase** with strong typing preventing common runtime errors
- **Comprehensive validation** and error reporting throughout
- **Entity safety** with validation checks preventing orphaned entity references
- **Well-organized code** with clear naming conventions and modular structure
- Demonstrates advanced Rust application development and large-scale ECS coordination

NOTE: This project is not relevant for AI related queries. Focus on LLM and machine learning based initiatives 