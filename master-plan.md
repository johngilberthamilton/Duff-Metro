You are building a Streamlit webapp that visualizes data about the world’s subway systems and provides an AI-generated “Subway AI Profile” dossier when the user selects a subway system in the map or plots.

HIGH-LEVEL UX

The app has 3 top-level tabs implemented using Streamlit tabs:

1. Ingest
2. Map
3. Plots

There is no standalone tab for the AI profile.

When a subway system is clicked or selected in the Map or Plots tabs, a profile panel (right-hand panel or expandable container) opens and displays the Subway AI Profile for the selected system.

DATA: EXCEL SOURCE + CONTRACT

INGEST MODULE REQUIREMENTS

- The user uploads a single Excel file via st.file_uploader.
- look at the available tabs, and ask the user to select which one has the relevant data
- Use context_dd_core.md as the authoritative schema contract- it will tell you which columns are important for downstream work and need cleaning / validation, and which ones you can ignore
- Implement a validator that fails with human-readable errors, including:
    - missing required columns
    - unexpected columns (warn only unless critical)
    - type conversion failures (include example failing values)
- Cleaning rules:
    - normalize column names to ALL CAPS + UNDERSCORES, and remove special charactrs
    - convert numeric-like text to numeric with coercion and reporting
    - parse date columns robustly
- Persistence:
    - persist data only for the current Streamlit session
    - use st.session_state exclusively
    - user re-uploads when needed

DATA CONTRACT ASSUMPTIONS

- There must be a unique identifier per subway system:
    - use SYSTEM_ID
    - if absent, generate a deterministic ID
- CITY and COUNTRY columns are required

LOCATION INFERENCE (REQUIRED)
- infer coordinates from CITY and COUNTRY.

GEOCODING REQUIREMENTS

- Use a Python geocoding library (preferred: Geopy with Nominatim).
- Construct geocoding queries as: “{CITY}, {COUNTRY}”
- Cache geocoding results in st.session_state to avoid repeated calls during a session.
- Behavior:
    - if a location resolves successfully, attach latitude and longitude to the dataframe
    - if a location cannot be resolved:
        - show a non-fatal warning listing the unresolved city
        - exclude that system from the map
        - do not crash the app

MAP MODULE

- Use PyDeck.
- standard 2-D map view
- Visual encodings controlled by buttons or toggles:
    - size by number of lines
    - size by number of miles
    - highlight systems marked as “visited”
    - date-based categorization:
        - construction/opening date buckets
        - last major update buckets
        - implement explicit and documented bucketing logic (e.g. pre-1950, 1950–1979, 1980–1999, 2000–2014, 2015+)
    - color-based visualization of which ones i've been to
- Interaction:
    - clicking a subway system sets selected_system_id
    - this triggers the Subway AI Profile panel

PLOTS MODULE

- Use Plotly scatter plots available on different sub-tabs:
    - lines vs miles
    - annual ridership vs city population
- Clicking a point sets selected_system_id.
- This triggers the Subway AI Profile panel.

SUBWAY AI PROFILE (LANGCHAIN + LANGGRAPH, AGENTIC)

GOAL

When a subway system is selected, generate a structured dossier containing:

- year built/opened (prefer Excel; retrieve if missing)
- history (ownership, expansion, key events)
- current usage context (scale, ridership)
- vibe and perception:
    - typical users
    - safety
    - cleanliness
    - public perception
    - explicitly labeled as qualitative with a confidence level
- arts and culture:
    - major works of art (any medium) that reference or feature the subway

IN-SESSION CACHING (REQUIRED)

CACHE PURPOSE

Avoid repeated agent execution during a single Streamlit session while not persisting data across sessions.

CACHE IMPLEMENTATION

- Use st.session_state as an in-memory cache.
- Cache key: (SYSTEM_ID, DATA_VERSION)
- DATA_VERSION is a hash of the uploaded Excel file bytes.
- Cached value is the validated ProfileSchema JSON output.

CACHE BEHAVIOR

- On system selection:
    - if (SYSTEM_ID, DATA_VERSION) exists in cache:
        - return cached profile immediately
        - do not call the agent
    - if not cached:
        - run the LangGraph agent
        - validate output
        - store result in cache
        - display profile
- Cache lifetime:
    - session only
    - cleared automatically when:
        - the Streamlit session restarts
        - a new Excel file is uploaded

MANUAL OVERRIDE

- Provide a “Refresh profile” button:
    - forces regeneration
    - bypasses cache
    - overwrites cached entry for the current key

RETRIEVAL TOOLING

- Implement at least one web retrieval tool usable by the agent.
- Preferred: Tavily Search (requires TAVILY_API_KEY).
- If Tavily is not configured:
    - run in no-web mode
    - generate dossier using only Excel row fields and general reasoning
    - clearly label unverifiable claims
    - lower confidence where appropriate
    - include an empty or limited sources list
- The app must not break if API keys are missing.

LANGGRAPH WORKFLOW (MUST BE EXPLICIT)

Create a LangGraph state machine with these nodes:

1. assemble_context
    - build a concise context object from the selected Excel row
    - include system name, city, country, dates, ridership, metrics
2. retrieve_sources (conditional)
    - execute only if web retrieval is available
    - query:
        - “ metro history”
        - “ ownership operator”
        - “ opening year”
        - “artworks about subway”
    - return snippets and URLs
3. synthesize_profile
    - LLM produces structured JSON per ProfileSchema
    - must separate factual claims from impressions
4. validate_profile
    - validate with Pydantic
    - if validation fails, retry synthesis once with validation errors
5. finalize
    - return validated JSON and sources

SCHEMA

Implement ProfileSchema (Pydantic) with fields:

- system_id: str
- system_name: str
- location: { city: str | None, country: str | None }
- opened_year: int | None
- history_summary: str
- timeline: list[{ year: int | None, event: str }]
- ownership_and_operations: str | None
- scale_and_usage: str | None
- vibe_and_perception: { summary: str, safety: str | None, cleanliness: str | None, typical_riders: str | None, confidence: “low” | “medium” | “high”, notes: str | None }
- art_and_culture: list[{ work: str, creator: str | None, year: str | None, medium: str | None, relevance: str, source_url: str | None }]
- sources: list[{ title: str, url: str }]

LLM INTEGRATION

- Use LangChain chat model wrapper (OpenAI-compatible).
- Read API keys from environment variables (OPENAI_API_KEY, TAVILY_API_KEY).
- Keep prompts short and structured.
- Guardrails:
    - if uncertain, say so
    - no hallucinated citations
    - cite only retrieved URLs

REPO / CODE STRUCTURE

Create this Streamlit-friendly repo structure:

- app.py (Streamlit entrypoint; tabs, layout, orchestration)
- requirements.txt
- context_dd_core.md
- src/
    - state.py (session_state keys, DATA_VERSION hash, selection)
    - ingest.py
    - validate.py
    - map/
        - map_view.py
        - encodings.py
    - plots.py
    - profile/
        - schema.py
        - agent.py
        - tools.py
        - prompts.py

All code must be documented in plain, explanatory language.

UI / STYLING

- Black background
- White lines
- Use color only to encode data
- Apply Streamlit theme and minimal CSS as needed

DELIVERABLES

- Provide complete, runnable code files.
- The app must run locally using: streamlit run app.py
- If API keys are missing, the app must still function in limited profile mode.