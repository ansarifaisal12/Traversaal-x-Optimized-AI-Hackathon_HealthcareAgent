# HealthGuard Agent Architecture

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   HealthGuard AI Assistant                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Agent (HealthGuardAgent)                │
│                                                                  │
│  ┌──────────────┐   ┌─────────────┐   ┌─────────────────────┐   │
│  │ ReAct Loop   │   │ Memory      │   │ Response Generator  │   │
│  │              │   │             │   │                     │   │
│  │ Thought →    │   │ Patient     │   │ Medical Context     │   │
│  │ Action →     │◄──┤ History     │◄──┤ Awareness           │   │
│  │ Observation →│   │             │   │                     │   │
│  │ Response     │   │ Conversation│   │ Empathetic          │   │
│  │              │   │             │   │ Communication       │   │
│  │              │   │             │   │                     │   │
│  └──────────────┘   └─────────────┘   └─────────────────────┘   │
└───────┬─────────────────┬─────────────────┬───────────────┬─────┘
        │                 │                 │               │
        ▼                 ▼                 ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Medication    │ │ Symptom       │ │ Medical Info  │ │ Health        │
│ Tool          │ │ Tool          │ │ Tool          │ │ Analysis Tool │
│               │ │               │ │               │ │               │
│ - Add/Track   │ │ - Log         │ │ - Search      │ │ - Generate    │
│   Medications │ │   Symptoms    │ │   Medical     │ │   Charts      │
│ - Schedule    │ │ - Symptom     │ │   Information │ │ - Analyze     │
│   Reminders   │ │   Analysis    │ │ - Medication  │ │   Trends      │
│ - Adherence   │ │ - Pattern     │ │   Details     │ │ - Health      │
│   Tracking    │ │   Detection   │ │ - Treatment   │ │   Insights    │
│               │ │               │ │   Options     │ │               │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │                 │
        └────────────────┼─────────────────┼─────────────────┘
                         │                 │
                         ▼                 ▼
               ┌───────────────────────────────────┐
               │           Streamlit UI            │
               │                                   │
               │  - Interactive Chat Interface     │
               │  - Patient Dashboard              │
               │  - Data Visualizations            │
               │  - Medication Calendar            │
               │  - Symptom Tracker                │
               └───────────────────────────────────┘
```

## Key Components

### 1. Core Agent (HealthGuardAgent)
The central orchestration layer that coordinates:
- ReAct Loop: Decision-making cycle of reasoning and action
- Memory System: Stores patient data and conversation context
- Response Generator: Creates empathetic, medically-informed responses

### 2. Specialized Healthcare Tools
Modular tools that provide specific healthcare functionalities:
- **Medication Tool**: Manages medication schedules and adherence
- **Symptom Tool**: Tracks symptoms and identifies patterns
- **Medical Info Tool**: Retrieves reliable medical information
- **Health Analysis Tool**: Generates visualizations and insights

### 3. Streamlit UI Layer
User-facing interface providing:
- Interactive chat with the AI agent
- Patient dashboards with health data
- Interactive visualizations and charts
- Medication calendars and reminders

## Data Flow

1. User inputs health query or data via the Streamlit UI
2. HealthGuardAgent processes the input through its ReAct loop
3. Agent selects and calls appropriate healthcare tools
4. Tools perform specific functions and return results
5. Agent formats the response and presents it through the UI

## Technology Stack

- **Agent Framework**: Custom extension of Traversaal's AgentPro
- **LLM Backend**: OpenAI GPT-4o
- **Database**: SQLite for local storage
- **UI Framework**: Streamlit
- **Data Visualization**: Matplotlib, Plotly
- **Medical Information**: Traversaal Ares API integration 