# Local LLM Integration Plan

## Overview
Integrate a small, local LLM to generate automated insights and reports without user interaction. The LLM runs completely in the background, analyzing Jira data to detect patterns and issues.

## Use Cases

### 1. **Scope Creep Detection**
- Monitor story point changes after sprint start
- Detect stories with growing acceptance criteria
- Flag when "small" stories become "large"
- **Output**: Alert when >20% of stories grow by >30%

### 2. **Missed Targets Analysis**
- Track sprint commitments vs completions
- Identify patterns in incomplete work
- Analyze reasons for spillover
- **Output**: Weekly report on completion rates and patterns

### 3. **Defect Leakage Tracking**
- Monitor bugs linked to "Done" stories
- Track bugs found in production vs caught in QA
- Calculate defect escape rate
- **Output**: Alert when defect leakage exceeds threshold

### 4. **Team Health Indicators**
- Stale tickets (no activity in X days)
- Missing story points/estimates
- Blocked items duration
- Stories in "In Progress" too long
- **Output**: Daily hygiene score + specific issues

### 5. **Velocity & Flow Insights**
- Predict next sprint velocity based on trends
- Identify velocity drops and potential causes
- Calculate cycle time trends
- **Output**: Predictive metrics and anomaly alerts

## Technical Approach

### Recommended Models

#### Option 1: **LLaMA 3.2 1B/3B** (Recommended)
- **Size**: 1-3GB
- **Speed**: Fast on CPU
- **Strengths**: General reasoning, pattern detection
- **Use**: Text analysis, anomaly detection
- **Python**: `llama-cpp-python` or `transformers`

#### Option 2: **Phi-3 Mini (3.8B)**
- **Size**: ~2GB
- **Speed**: Very fast inference
- **Strengths**: Instruction following, summarization
- **Use**: Generate insight summaries
- **Python**: `transformers` library

#### Option 3: **TinyLlama (1.1B)**
- **Size**: ~600MB
- **Speed**: Extremely fast
- **Strengths**: Lightweight, good for simple tasks
- **Use**: Quick pattern matching
- **Python**: `llama-cpp-python`

### Architecture

```
┌─────────────────────────────────────┐
│         Jira Data Scraper           │
│  (Selenium → Extract structured)    │
└──────────────┬──────────────────────┘
               │ JSON/CSV
               ▼
┌─────────────────────────────────────┐
│       Data Aggregator               │
│  (Calculate metrics, build context) │
└──────────────┬──────────────────────┘
               │ Structured Data
               ▼
┌─────────────────────────────────────┐
│      LLM Insight Engine             │
│  • Load model once at startup       │
│  • Run on schedule (daily/hourly)   │
│  • Generate insights via prompts    │
│  • No user interaction              │
└──────────────┬──────────────────────┘
               │ Insights JSON
               ▼
┌─────────────────────────────────────┐
│      UI Display Layer               │
│  • Show insights in SM persona      │
│  • Auto-refresh insights            │
│  • Export reports                   │
└─────────────────────────────────────┘
```

### Implementation Steps

#### Phase 1: Data Preparation
```python
# insights_engine.py
class InsightsDataPrep:
    def prepare_scope_creep_data(self, jira_data):
        """Extract story point changes, acceptance criteria edits"""
        return {
            'stories_modified': [...],
            'avg_growth_percent': 35,
            'sprints_affected': [...]
        }
    
    def prepare_defect_leakage_data(self, jira_data):
        """Link bugs to original stories, calculate escape rate"""
        return {
            'total_bugs': 15,
            'production_bugs': 5,
            'escape_rate': 0.33
        }
```

#### Phase 2: LLM Integration
```python
# llm_engine.py
from llama_cpp import Llama

class LocalLLM:
    def __init__(self):
        # Load model once at startup
        self.model = Llama(
            model_path="models/llama-3.2-1b.gguf",
            n_ctx=2048,
            n_threads=4
        )
    
    def generate_insight(self, prompt, data):
        """Generate insight from structured data"""
        context = f"""
        You are analyzing software team data. Based on the following metrics:
        {json.dumps(data, indent=2)}
        
        {prompt}
        
        Provide a brief, actionable insight (2-3 sentences).
        """
        
        response = self.model(context, max_tokens=150)
        return response['choices'][0]['text']
```

#### Phase 3: Scheduled Insights
```python
# insights_scheduler.py
import schedule
import threading

class InsightsScheduler:
    def __init__(self, llm_engine, data_prep):
        self.llm = llm_engine
        self.prep = data_prep
        self.insights = []
    
    def run_daily_insights(self):
        """Run all insight checks"""
        jira_data = scrape_jira_data()
        
        # Scope creep
        scope_data = self.prep.prepare_scope_creep_data(jira_data)
        if scope_data['avg_growth_percent'] > 20:
            insight = self.llm.generate_insight(
                "Analyze this scope creep data and provide actionable feedback.",
                scope_data
            )
            self.insights.append({
                'type': 'scope_creep',
                'severity': 'warning',
                'message': insight
            })
        
        # Defect leakage
        defect_data = self.prep.prepare_defect_leakage_data(jira_data)
        if defect_data['escape_rate'] > 0.2:
            insight = self.llm.generate_insight(
                "Analyze this defect leakage and suggest improvements.",
                defect_data
            )
            self.insights.append({
                'type': 'defect_leakage',
                'severity': 'error',
                'message': insight
            })
        
        return self.insights
    
    def start(self):
        """Start scheduled insights (runs in background)"""
        schedule.every().day.at("08:00").do(self.run_daily_insights)
        
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_schedule, daemon=True)
        thread.start()
```

#### Phase 4: UI Integration
```python
# Add API endpoint in app.py
def handle_get_insights():
    """Return generated insights for UI"""
    return json.dumps(insights_scheduler.insights)
```

### Prompts for Common Insights

#### Scope Creep
```
Analyze sprint scope changes:
- {num_stories} stories grew by avg {percent}%
- {affected_sprints} sprints impacted
- Stories: {story_list}

Identify the root cause and provide 1-2 actionable recommendations.
```

#### Defect Leakage
```
Review defect data:
- Total bugs: {total}
- Production bugs: {prod_bugs}
- Escape rate: {rate}%
- Affected features: {features}

What process improvements would reduce production defects?
```

#### Velocity Prediction
```
Historical velocity data:
- Last 5 sprints: {velocities}
- Trend: {trend}
- Team size: {size}

Predict next sprint velocity and flag any concerns.
```

## Resource Requirements

### Model Storage
- **1B model**: ~600MB-1GB disk space
- **3B model**: ~2-3GB disk space
- Store in `models/` directory

### RAM Usage
- **1B model**: ~2-3GB RAM during inference
- **3B model**: ~4-6GB RAM during inference
- Run inference only when needed (scheduled)

### CPU/GPU
- **CPU only**: Works fine, 1-5 seconds per insight
- **GPU (optional)**: <1 second per insight
- Use GGUF quantized models for efficiency

## Installation

```bash
# Install LLM library
pip install llama-cpp-python

# Download model (one-time)
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
mv llama-2-7b-chat.Q4_K_M.gguf models/

# Or use smaller model
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
mv tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf models/
```

## User Experience

### Users See:
- **SM Persona → AI Insights card**
- Auto-updated insights (daily)
- Severity badges (info, warning, error)
- "View Details" buttons for more context
- No LLM interaction or configuration

### Users Don't See:
- Model loading
- Prompt engineering
- Inference process
- Model selection
- Any LLM terminology

## Benefits

1. **No Cloud Dependency**: Fully offline, no API costs
2. **Privacy**: Data never leaves local machine
3. **Fast**: Insights ready in seconds
4. **Proactive**: Identifies issues before they escalate
5. **Context-Aware**: Uses team-specific patterns

## Limitations

1. **Static Prompts**: Insights quality depends on prompt design
2. **No Learning**: Model doesn't learn from feedback (yet)
3. **Resource Use**: Requires 2-4GB RAM for model
4. **Initial Setup**: User must download model file

## Future Enhancements

- [ ] Fine-tune model on anonymized Jira data
- [ ] Add more insight types (burnout risk, knowledge silos)
- [ ] Implement feedback loop (user marks insights helpful/not)
- [ ] Multi-model approach (use different models for different tasks)
- [ ] Natural language queries ("Why is velocity dropping?")
