# ================== DuDraw Code Generator ==================
import streamlit as st
st.set_page_config(page_title="DuDraw Code Generator", layout="wide")

import os
import json
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

# Import the DuDraw function data
from du_draw_functions_data import DU_DRAW_FUNCTIONS
from agent_tools import calculate_expression

# ================== Configuration ==================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")
TEMPERATURE = 0.3
MAX_TOKENS = 2000
MAX_AGENT_STEPS = 5

# ================== Groq client ==================
def _init_groq() -> Optional[OpenAI]:
    if not GROQ_API_KEY:
        st.error("Missing GROQ_API_KEY. Add it via environment variable or Streamlit secrets.")
        return None
    try:
        return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"Failed to init Groq client: {e}")
        return None

groq_client = _init_groq()

# ================== DuDraw Function Retriever ==================
class DuDrawFunctionRetriever:
    """A tool to retrieve relevant DuDraw function information from a ChromaDB vector store."""
    
    def __init__(self):
        import os
        import shutil

        # Do NOT auto-delete the DB here. Use the sidebar "Reset Database" button instead.
        self.chroma_client = PersistentClient(path="./chroma_db")
        self.collection_name = "du_draw_functions_collection"

        # Embeddings without any API key
        try:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction()
            st.info("Using SentenceTransformer embeddings (no API key required)")
        except Exception as e:
            st.warning(f"SentenceTransformer unavailable: {e} — falling back.")
            try:
                self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            except Exception as e2:
                st.warning(f"Default embedding unavailable: {e2} — continuing without embeddings.")
                self.embedding_function = None

        try:
            if self.embedding_function:
                self.collection = self.chroma_client.get_or_create_collection(
                    self.collection_name,
                    embedding_function=self.embedding_function  # type: ignore
                )
            else:
                self.collection = self.chroma_client.get_or_create_collection(self.collection_name)
            self.populate_functions()
        except Exception as e:
            st.error(f"Failed to initialize ChromaDB collection: {e}")
            self.collection = None

    def populate_functions(self):
        """Populates the ChromaDB collection with DuDraw function data."""
        if not self.collection:
            st.warning("ChromaDB collection not available - using fallback validation")
            return
            
        try:
            if self.collection.count() == 0:
                st.info("Populating DuDraw functions into ChromaDB... (This happens once)")
                documents = []
                metadatas = []
                ids = []

                for func in DU_DRAW_FUNCTIONS:
                    doc_content = f"{func['description']}. Keywords: {', '.join(func.get('keywords', []))}"
                    documents.append(doc_content)

                    metadata_for_chroma = func.copy()
                    if 'keywords' in metadata_for_chroma and isinstance(metadata_for_chroma['keywords'], list):
                        metadata_for_chroma['keywords'] = ', '.join(metadata_for_chroma['keywords'])
                    if 'params' in metadata_for_chroma and isinstance(metadata_for_chroma['params'], list):
                        metadata_for_chroma['params'] = ', '.join(metadata_for_chroma['params'])

                    metadatas.append(metadata_for_chroma)
                    ids.append(func["id"])

                self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
                st.success(f"Added {len(DU_DRAW_FUNCTIONS)} DuDraw functions to ChromaDB.")
            else:
                st.info("ChromaDB already contains DuDraw functions.")
        except Exception as e:
            st.warning(f"Failed to populate ChromaDB: {e} - using fallback validation")

    def retrieve_functions(self, query: str, n_results: int = 6):
        """Retrieves relevant DuDraw function information based on a query."""
        st.write(f"**Tool: DuDraw Function Retriever** - Querying: `{query}`")
        
        # If no collection available, use fallback search
        if not self.collection:
            return self._fallback_function_search(query, n_results)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['metadatas']
            )
            retrieved_functions = []
            if results and results['metadatas'] and results['metadatas'][0]:
                for meta in results['metadatas'][0]:
                    retrieved_functions.append(meta)
            
            formatted_retrieval = self._format_retrieved_tools_for_llm_response(retrieved_functions)
            st.success(f"**Found DuDraw functions:**\n```\n{formatted_retrieval}\n```")
            return formatted_retrieval
        except Exception as e:
            st.warning(f"ChromaDB retrieval failed: {e} - Using fallback search")
            return self._fallback_function_search(query, n_results)
    
    def _fallback_function_search(self, query: str, n_results: int = 6):
        """Fallback function search without database dependency"""
        query_lower = query.lower()
        relevant_functions = []
        
        # Simple keyword-based search
        for func in DU_DRAW_FUNCTIONS:
            score = 0
            func_text = f"{func.get('description', '')} {func.get('keywords', [])} {func.get('id', '')}".lower()
            
            # Check for keyword matches
            if 'canvas' in query_lower and 'canvas' in func_text:
                score += 3
            if 'draw' in query_lower and 'draw' in func_text:
                score += 3
            if 'color' in query_lower and 'color' in func_text:
                score += 3
            if 'keyboard' in query_lower and 'key' in func_text:
                score += 3
            if 'mouse' in query_lower and 'mouse' in func_text:
                score += 3
            if 'text' in query_lower and 'text' in func_text:
                score += 2
            if 'display' in query_lower and 'show' in func_text:
                score += 2
            if 'setup' in query_lower and 'setup' in func_text:
                score += 2
            
            if score > 0:
                relevant_functions.append((score, func))
        
        # Sort by relevance score and take top results
        relevant_functions.sort(key=lambda x: x[0], reverse=True)
        top_functions = [func for score, func in relevant_functions[:n_results]]
        
        formatted_retrieval = self._format_retrieved_tools_for_llm_response(top_functions)
        st.success(f"**Found DuDraw functions (fallback search):**\n```\n{formatted_retrieval}\n```")
        return formatted_retrieval

    def _format_retrieved_tools_for_llm_response(self, tools_list):
        """Helper to format retrieved functions for LLM consumption."""
        if not tools_list:
            return "No specific DuDraw functions were found for this request."
        formatted_list = []
        for tool in tools_list:
            formatted_list.append(
                f"Function ID: {tool.get('id', 'N/A')}\n"
                f"Description: {tool.get('description', 'N/A')}\n"
                f"Syntax: {tool.get('syntax', 'N/A')}\n"
                f"Parameters: {tool.get('params', 'N/A')}\n"
                f"Example: {tool.get('example', 'N/A')}\n"
                "---"
            )
        return "\n".join(formatted_list)

# ================== Enhanced Code Generator ==================
def generate_dudraw_code(user_request: str, retriever: DuDrawFunctionRetriever) -> str:
    """Generate DuDraw code based on user request with step-by-step agent thinking"""
    
    system_prompt = """You are an expert DuDraw programmer with solid foundational programming knowledge and access to specialized DuDraw function documentation.

**CRITICAL WORKFLOW - ALWAYS FOLLOW THIS PATTERN:**

1. **FIRST: Use Your Programming Foundation & Common Sense**
   - You understand basic programming concepts: loops, conditionals, functions, variables
   - You know general game development patterns: game loops, state management, collision detection
   - **COMMON SENSE IMPORTS:** Apply logical thinking about what imports are needed:
     * Snake/Pong/Breakout games → Need `import random` for food/ball positioning
     * Any game → Need `import random` for randomization
     * Animations with math → May need `import math` for trigonometry
     * Timing-critical apps → May need `import time`
   - You understand graphics programming: coordinate systems, drawing primitives, animations
   - You can structure code properly: imports, constants, functions, main execution

2. **SECOND: MANDATORY - Query ALL Relevant DuDraw Functions**
   - **ALWAYS START:** Query DuDraw functions for EVERY aspect of your project
   - **COMPREHENSIVE QUERIES:** Don't just query one thing - query ALL function types you'll need
   - **CRITICAL:** Use ONE simple query string per tool call, like "drawing shapes" or "keyboard input"
   - **STRATEGY:** Think about your project needs, then query each category:
     * Games → Query: "canvas", "drawing", "colors", "keyboard input", "display"
     * Animations → Query: "canvas", "drawing", "colors", "display", "math functions"
     * Interactive → Query: "canvas", "drawing", "mouse input", "keyboard input", "display"

3. **THIRD: Apply Common Sense + Retrieved Functions**
   - Use your programming knowledge for overall structure and logic
   - **SMART IMPORTS:** Add necessary imports based on project type (random for games, math for animations)
   - Use retrieved DuDraw functions for the exact syntax and function calls
   - **VALIDATE YOUR APPROACH:** Does this make sense for the type of project requested?

**Tool Usage Examples (FOLLOW THESE PATTERNS):**
- retrieve_dudraw_functions(query="canvas setup") ✓
- retrieve_dudraw_functions(query="drawing shapes") ✓
- retrieve_dudraw_functions(query="keyboard input") ✓
- retrieve_dudraw_functions(query="colors") ✓
- retrieve_dudraw_functions(query="display timing") ✓

**Common Sense Import Logic (APPLY THIS AUTOMATICALLY):**
- **Snake Game:** `import dudraw, import random` (for food placement)
- **Pong Game:** `import dudraw, import random` (for ball direction/speed variation)
- **Breakout Game:** `import dudraw, import random` (for brick layouts, ball behavior)
- **Maze Game:** `import dudraw, import random` (for maze generation)
- **Particle Systems:** `import dudraw, import random, import math` (for particle behavior)
- **Physics Simulations:** `import dudraw, import math` (for trigonometry)
- **Simple Drawings:** `import dudraw` (minimal requirements)

**Your Programming Knowledge (Use This for Structure):**
- **Game Architecture:** Initialization → Game Loop (Update → Draw → Repeat)
- **State Management:** Global variables for game state, position tracking, scoring
- **Input Handling:** Event-driven input processing, key mapping, continuous input
- **Collision Detection:** Boundary checking, object intersection, distance calculations
- **Animation Timing:** Frame rate control, smooth movement, physics simulation
- **Randomization Logic:** Food spawning, initial conditions, procedural generation

**Mandatory DuDraw Function Queries (ALWAYS DO THESE):**
For ANY project, you MUST query these function categories:
1. **Canvas & Setup:** Query "canvas" - Get canvas initialization functions
2. **Drawing Operations:** Query "drawing" - Get shape/line drawing functions  
3. **Colors:** Query "colors" - Get color setting functions
4. **Display & Timing:** Query "display" - Get screen update and timing functions

For INTERACTIVE projects, ALSO query:
5. **Input Systems:** Query "keyboard" or "mouse" - Get input handling functions

For GAMES specifically, ALSO query:
6. **Text Display:** Query "text" - Get score/message display functions

**Code Generation Process:**
1. **Analyze Request:** What type of project? What imports will I need based on common sense?
2. **Query ALL Relevant Functions:** Make comprehensive retrieval queries for every DuDraw function category needed
3. **Structure Code:** Apply your programming knowledge to organize the code properly
4. **Implement Logic:** Use retrieved DuDraw functions with your programming logic and common sense imports
5. **Validate:** Does this make sense? Are all necessary imports included?

**Quality Standards:**
- **Functional First:** Code must actually work and be runnable
- **Complete Imports:** Include ALL necessary imports (dudraw + random/math/time as needed)
- **Proper Structure:** Use initialize/update/draw/loop pattern for interactive programs
- **Accurate Syntax:** Only use DuDraw functions that you've retrieved and verified
- **Common Sense:** Apply logical thinking about what a project type needs

**IMPORTANT TOOL CALL FORMAT:**
When calling retrieve_dudraw_functions, use ONLY a simple string query:
- retrieve_dudraw_functions(query="canvas") ✓
- retrieve_dudraw_functions(query="drawing") ✓
- retrieve_dudraw_functions(query="keyboard") ✓
- DO NOT use complex JSON objects or multiple parameters!

**Output Format for Final Answer:**
```python
# Your complete, functional DuDraw code
# Include ALL necessary imports (dudraw + random/math/time as appropriate)
# Include all setup, functions, and main execution
```
---
**Explanation:**
- Detailed explanation of the code structure and logic
- Description of how programming concepts combine with DuDraw functions
- Explanation of imports chosen and why they're necessary
- Explanation of game/animation mechanics if applicable

**Remember:** 
- Apply common sense about imports and project requirements
- ALWAYS query DuDraw functions comprehensively before coding
- Query ALL relevant function categories, not just one
- Use programming fundamentals + retrieved functions + logical imports
- Validate that your approach makes sense for the project type"""

    # Initialize conversation history
    conversation_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Create this DuDraw project: {user_request}"}
    ]
    
    # Available tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "retrieve_dudraw_functions",
                "description": "Get information about DuDraw functions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query to find relevant DuDraw functions"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_expression",
                "description": "Calculate mathematical expressions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ]
    
    available_tools = {
        "retrieve_dudraw_functions": retriever.retrieve_functions,
        "calculate_expression": calculate_expression
    }
    
    st.subheader("Agent's Step-by-Step Reasoning:")
    st.markdown(f"**User Goal:** *{user_request}*")
    st.divider()
    
    final_output_generated = False
    steps = 0
    
    try:
        while not final_output_generated and steps < MAX_AGENT_STEPS:
            steps += 1
            st.markdown(f"**--- Agent Step {steps} ---**")
            
            # Call LLM with spinner
            with st.spinner(f"Agent is thinking (Step {steps})..."):
                response = groq_client.chat.completions.create(
                    model=GROQ_MODEL_NAME,
                    messages=conversation_history,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=1500
                )
            
            response_message = response.choices[0].message
            conversation_history.append(response_message)
            
            # Display agent's thought if available
            if response_message.content and response_message.content.strip().startswith("Thought:"):
                st.info(f"**Agent Thought:** {response_message.content.replace('Thought:', '').strip()}")
            elif response_message.content and not response_message.tool_calls:
                # If it's not a tool call and contains content, it's likely the final answer
                generated_output = response_message.content
                st.write("\n---")
                st.subheader("Generated DuDraw Code & Explanation:")
                st.code(generated_output, language='python')
                final_output_generated = True
                break
            
            # Handle tool calls
            if response_message.tool_calls:
                tool_call_successful = False
                tool_messages = []
                
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}
                    
                    st.markdown(f"**Agent Action: Calling Tool** - `{function_name}` with arguments: `{function_args}`")
                    
                    if function_name in available_tools:
                        try:
                            tool_to_call = available_tools[function_name]
                            
                            # Validate function arguments
                            if function_name == "retrieve_dudraw_functions":
                                if "query" not in function_args:
                                    # Try to extract a query from the arguments
                                    if function_args:
                                        # If arguments exist but no 'query', use the first value
                                        query_value = next(iter(function_args.values()), "drawing functions")
                                        function_args = {"query": str(query_value)}
                                    else:
                                        function_args = {"query": "drawing functions"}
                                    st.warning(f"Fixed malformed tool call: using query='{function_args['query']}'")
                            
                            tool_response = tool_to_call(**function_args)
                            tool_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_response,
                                "name": function_name
                            })
                            tool_call_successful = True
                        except Exception as tool_error:
                            error_message = f"Tool execution failed: {tool_error}"
                            st.error(error_message)
                            tool_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": error_message,
                                "name": function_name
                            })
                    else:
                        error_message = f"Error: Tool '{function_name}' not found."
                        st.error(error_message)
                        tool_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_message,
                            "name": function_name
                        })
                
                # Add all tool messages to history
                if tool_messages:
                    conversation_history.extend(tool_messages)
                
                if not tool_call_successful:
                    st.warning("Tool calls failed. Agent will continue with available knowledge.")
                    
            elif not response_message.content.strip().startswith("Thought:"):
                st.warning("Agent's response didn't clearly indicate a thought or tool call. This might be an intermediate step.")
                st.info(f"**Agent Thought (Implicit):** {response_message.content}")
        
        if not final_output_generated:
            st.error(f"Agent failed to generate a final output after {MAX_AGENT_STEPS} steps.")
            
            # Fallback: Generate code directly without tools
            st.info("Attempting fallback code generation...")
            fallback_messages = [
                {"role": "system", "content": "Generate functional DuDraw code directly. Use your knowledge of DuDraw functions. Focus on creating working code."},
                {"role": "user", "content": f"Create this DuDraw project: {user_request}"}
            ]
            
            try:
                fallback_response = groq_client.completions.create(
                    model=GROQ_MODEL_NAME,
                    messages=fallback_messages,
                    temperature=0.3,
                    max_tokens=1500
                )
                
                fallback_content = fallback_response.choices[0].message.content or ""
                if fallback_content:
                    st.success("Fallback generation successful!")
                    return fallback_content
                else:
                    return ""
                    
            except Exception as fallback_error:
                st.error(f"Fallback generation also failed: {fallback_error}")
                return ""
        
        st.divider()
        if final_output_generated:
            st.success("**Agent Final Report:** Task completed. The DuDraw code and its detailed explanation are provided above.")
        else:
            st.error("**Agent Final Report:** Task failed to complete.")
        
        return response_message.content or ""
        
    except Exception as e:
        st.error(f"An error occurred during agent's reasoning loop: {e}")
        return ""

def extract_code(text: str) -> str:
    """Extract Python code from response"""
    import re
    
    # Look for code blocks
    blocks = re.findall(r"```python\s+(.*?)```", text, flags=re.DOTALL|re.IGNORECASE)
    if blocks:
        return blocks[0].strip()
    
    # Look for code without markdown
    blocks = re.findall(r"```\s*(.*?)```", text, flags=re.DOTALL)
    if blocks:
        return blocks[0].strip()
    
    # If no blocks, look for code starting with import
    if text.strip().startswith("import"):
        return text.strip()
    
    return text.strip()

def extract_explanation(text: str) -> str:
    """Extract explanation from response"""
    import re
    
    # Look for explanation after the code block
    explanation_match = re.search(r"---\s*\*\*Explanation:\*\*(.*?)(?=\n\n|$)", text, flags=re.DOTALL|re.IGNORECASE)
    if explanation_match:
        return explanation_match.group(1).strip()
    
    # Look for explanation without markdown
    explanation_match = re.search(r"---\s*Explanation:(.*?)(?=\n\n|$)", text, flags=re.DOTALL|re.IGNORECASE)
    if explanation_match:
        return explanation_match.group(1).strip()
    
    return ""

def validate_code(code: str, retriever: DuDrawFunctionRetriever = None) -> List[str]:
    """Enhanced code validation with DuDraw function checking against actual function database"""
    errors = []

    # Check imports
    if 'import dudraw' not in code:
        errors.append("Missing 'import dudraw'")

    # Common sense import checking based on project type
    project_lower = code.lower()
    
    # Games that typically need random
    game_indicators = ['snake', 'pong', 'breakout', 'maze', 'food', 'brick', 'ball', 'enemy', 'spawn']
    if any(indicator in project_lower for indicator in game_indicators):
        if 'random' in code and 'import random' not in code:
            errors.append("Missing 'import random' - games typically need randomization for food/ball/brick placement")
    
    # General random usage check
    if 'random.' in code and 'import random' not in code:
        errors.append("Missing 'import random' (code uses random functions)")
    
    # Math operations check - more comprehensive
    math_indicators = ['sin', 'cos', 'tan', 'pi', 'sqrt', 'math.', 'atan2', 'asin', 'acos', 'degrees', 'radians']
    math_functions_used = any(indicator in code for indicator in math_indicators)
    
    # Also check for mathematical operations that typically need math
    math_operations = ['pow(', 'abs(', 'floor(', 'ceil(', 'round(']
    math_ops_used = any(op in code for op in math_operations)
    
    if (math_functions_used or math_ops_used) and 'import math' not in code:
        errors.append("Missing 'import math' (code uses mathematical functions)")
    
    # Time operations check
    if 'time.' in code and 'import time' not in code:
        errors.append("Missing 'import time' (code uses time functions)")
    
    # Check syntax
    try:
        compile(code, "<generated>", "exec")
    except SyntaxError as e:
        errors.append(f"Syntax error: {e}")
    
    # Check for common mistakes
    if 'key == "left"' in code or 'key == "right"' in code:
        errors.append("Keyboard error: dudraw.next_key_typed() returns 'a', 'd', etc. not 'left', 'right'")

    if 'for _ in range(100): pass' in code:
        errors.append("Timing error: use dudraw.delay(ms) instead of busy-wait loops")
    
    # Check for incorrect DuDraw functions
    incorrect_functions = {
        'dudraw.set_scale': 'Use dudraw.set_x_scale() and dudraw.set_y_scale() instead',
        'dudraw.clear_canvas': 'Use dudraw.clear() instead',
        'dudraw.draw_point': 'Use dudraw.filled_circle() or dudraw.filled_square() instead',
        'dudraw.get_key_press': 'Use dudraw.next_key_typed() with dudraw.has_next_key_typed() instead',
        'dudraw.set_pen_color': 'Use dudraw.set_pen_color_rgb() for RGB values',
        'dudraw.draw_text': 'Use dudraw.text() instead',
        'dudraw.draw_line': 'Use dudraw.line() instead',
        'dudraw.draw_rectangle': 'Use dudraw.filled_rectangle() or dudraw.rectangle() instead',
        'dudraw.draw_circle': 'Use dudraw.filled_circle() or dudraw.circle() instead'
    }
    
    for incorrect_func, correct_usage in incorrect_functions.items():
        if incorrect_func in code:
            errors.append(f"Invalid DuDraw function: {incorrect_func} - {correct_usage}")
    
    # ENHANCED: Check against actual DuDraw function database
    if retriever and retriever.collection:
        errors.extend(validate_against_dudraw_database(code, retriever))
    else:
        # Fallback to basic validation if database is not available
        errors.extend(validate_basic_dudraw_functions(code))
    
    # Enhanced game structure validation with common sense - more flexible
    game_terms = ['game', 'move', 'control', 'score', 'collision', 'snake', 'pong', 'breakout', 'player']
    if any(word in code.lower() for word in game_terms):
        # Check for initialization - more flexible
        init_patterns = ['initialize_game', 'init_game', 'setup_game', 'def main', 'def setup']
        has_init = any(pattern in code.lower() for pattern in init_patterns)
        if not has_init:
            errors.append("Game structure: Missing initialization function (should have initialize_game() or main())")
        
        # Check for update logic - more flexible
        update_patterns = ['update_game', 'update', 'move', 'step', 'tick']
        has_update = any(pattern in code.lower() for pattern in update_patterns)
        if not has_update:
            errors.append("Game structure: Missing game update logic (should have update_game() or update logic)")
        
        # Check for drawing - more flexible
        draw_patterns = ['draw_game', 'draw', 'render', 'display', 'show']
        has_draw = any(pattern in code.lower() for pattern in draw_patterns)
        if not has_draw:
            errors.append("Game structure: Missing drawing/rendering function (should have draw_game() or drawing logic)")
        
        # Check for game loop - more flexible
        loop_patterns = ['game_loop', 'while true', 'while True', 'for', 'loop']
        has_loop = any(pattern in code.lower() for pattern in loop_patterns)
        if not has_loop:
            errors.append("Game structure: Missing main game loop (should have game_loop() or while True)")
        
        # Check for keyboard input - only if keyboard interaction is mentioned
        keyboard_terms = ['key', 'arrow', 'wasd', 'input', 'control', 'move']
        has_keyboard_terms = any(term in code_lower for term in keyboard_terms)
        if has_keyboard_terms and 'enable_keyboard_input' not in code:
            errors.append("Game structure: Missing dudraw.enable_keyboard_input() - required for keyboard games")
    
    # Check for proper main execution
    if 'if __name__' not in code and 'while True' in code:
        errors.append("Missing main execution block: Use if __name__ == '__main__':")
    
    # Check for proper DuDraw setup
    if 'set_canvas_size' not in code:
        errors.append("Missing dudraw.set_canvas_size() - required for proper setup")
    
    if 'show' not in code and 'while True' in code:
        errors.append("Missing dudraw.show() - required to display drawings")
    
    # Project-specific validation
    if 'snake' in project_lower:
        if 'random' not in code:
            errors.append("Snake game: Missing random food placement logic")
        if 'list' not in code and 'array' not in code:
            errors.append("Snake game: Missing snake body data structure (list/array)")
    
    if 'pong' in project_lower:
        if 'ball' not in code.lower():
            errors.append("Pong game: Missing ball object/variables")
        if 'paddle' not in code.lower():
            errors.append("Pong game: Missing paddle object/variables")
    
    if 'breakout' in project_lower:
        if 'brick' not in code.lower():
            errors.append("Breakout game: Missing brick/block system")
        if 'random' not in code:
            errors.append("Breakout game: Should use random for brick layouts or ball behavior")
    
    # Button-specific validation
    button_terms = ['button', 'click', 'menu', 'interface', 'gui', 'ui']
    if any(term in project_lower for term in button_terms):
        if 'mouse_pressed' not in code and 'mouse_x' not in code and 'mouse_y' not in code:
            errors.append("Button interface: Missing mouse input functions (dudraw.mouse_pressed, dudraw.mouse_x, dudraw.mouse_y)")
        if 'class' not in code and 'def' not in code:
            errors.append("Button interface: Consider using a Button class for better organization")
    
    return errors

def validate_against_dudraw_database(code: str, retriever: DuDrawFunctionRetriever) -> List[str]:
    """Validate generated code against the actual DuDraw function database"""
    errors = []
    if not retriever or not retriever.collection:
        return errors

    import re
    dudraw_functions_used = re.findall(r'dudraw\.(\w+)\s*\(', code)
    d_functions_used = re.findall(r'd\.(\w+)\s*\(', code)

    try:
        results = retriever.collection.query(
            query_texts=["all functions"],
            n_results=100,
            include=['metadatas']
        )

        available_functions = set()
        if results and results['metadatas'] and results['metadatas'][0]:
            for meta in results['metadatas'][0]:
                func_id = meta.get('id', '')
                if func_id:
                    if func_id.startswith('dudraw.'):
                        available_functions.add(func_id.replace('dudraw.', ''))
                    elif func_id.startswith('d.'):
                        available_functions.add(f"d.{func_id.replace('d.', '')}")

        # Check dudraw.* calls
        for func_name in dudraw_functions_used:
            if func_name not in available_functions:
                similar = [f"dudraw.{af}" for af in available_functions if func_name.lower() in af.lower()]
                if similar:
                    errors.append(f"Invalid DuDraw function: dudraw.{func_name} - Similar available functions: {', '.join(similar)}")
                else:
                    errors.append(f"Invalid DuDraw function: dudraw.{func_name} - Function not found in DuDraw database")

        # Check d.* calls
        for func_name in d_functions_used:
            if f"d.{func_name}" not in available_functions:
                errors.append(f"Invalid DuDraw function: d.{func_name} - Function not found in DuDraw database")

        # Heuristics for missing function groups...
        code_lower = code.lower()
        if any(term in code_lower for term in ['key', 'input', 'control', 'move']):
            keyboard_functions = ['enable_keyboard_input', 'next_key_typed', 'has_next_key_typed']
            missing_keyboard = [f for f in keyboard_functions if f not in dudraw_functions_used]
            if missing_keyboard:
                errors.append(f"Missing keyboard input functions: {', '.join(missing_keyboard)} - required for interactive programs")

        if any(term in code_lower for term in ['draw', 'circle', 'square', 'rectangle', 'line']):
            drawing_functions = ['filled_circle', 'filled_square', 'filled_rectangle', 'line', 'text']
            missing_drawing = [f for f in drawing_functions if f not in dudraw_functions_used]
            if missing_drawing:
                errors.append(f"Missing drawing functions: {', '.join(missing_drawing)} - required for visual programs")

        if 'while true' in code_lower or 'game_loop' in code_lower:
            display_functions = ['show', 'clear']
            missing_display = [f for f in display_functions if f not in dudraw_functions_used]
            if missing_display:
                errors.append(f"Missing display functions: {', '.join(missing_display)} - required for game loops")

    except Exception as e:
        st.warning(f"Database validation skipped: {e}")

    return errors

def validate_basic_dudraw_functions(code: str) -> List[str]:
    """Basic DuDraw function validation without database dependency"""
    errors = []
    
    # Common DuDraw functions that should be valid
    valid_functions = {
        'dudraw.set_canvas_size': 'Canvas setup',
        'dudraw.set_x_scale': 'X-axis scale',
        'dudraw.set_y_scale': 'Y-axis scale',
        'dudraw.set_pen_color': 'Pen color',
        'dudraw.set_pen_color_rgb': 'RGB pen color',
        'dudraw.clear': 'Clear canvas',
        'dudraw.show': 'Display canvas',
        'dudraw.filled_circle': 'Draw filled circle',
        'dudraw.filled_square': 'Draw filled square',
        'dudraw.filled_rectangle': 'Draw filled rectangle',
        'dudraw.circle': 'Draw circle outline',
        'dudraw.square': 'Draw square outline',
        'dudraw.rectangle': 'Draw rectangle outline',
        'dudraw.line': 'Draw line',
        'dudraw.text': 'Draw text',
        'dudraw.enable_keyboard_input': 'Enable keyboard input',
        'dudraw.next_key_typed': 'Get next key typed',
        'dudraw.has_next_key_typed': 'Check if key available',
        'dudraw.delay': 'Delay execution',
        # Button-related functions
        'dudraw.mouse_x': 'Get mouse X position',
        'dudraw.mouse_y': 'Get mouse Y position',
        'dudraw.mouse_pressed': 'Check if mouse is pressed'
    }
    
    # Check for obviously invalid functions
    import re
    dudraw_pattern = r'dudraw\.(\w+)\s*\('
    dudraw_functions_used = re.findall(dudraw_pattern, code)
    
    for func_name in dudraw_functions_used:
        full_func = f"dudraw.{func_name}"
        if full_func not in valid_functions:
            # Try to find similar functions
            similar = []
            for valid_func in valid_functions:
                if func_name.lower() in valid_func.lower() or valid_func.lower() in func_name.lower():
                    similar.append(valid_func)
            
            if similar:
                errors.append(f"Invalid DuDraw function: {full_func} - Similar available: {', '.join(similar)}")
            else:
                errors.append(f"Invalid DuDraw function: {full_func} - Function not recognized")
    
    return errors

def get_button_code_template() -> str:
    """Get hardcoded button code templates for common button implementations"""
    return """
# ===== BUTTON CODE TEMPLATES =====

# 1. Simple Button Class
class Button:
    def __init__(self, x, y, width, height, text, color=dudraw.BLUE):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.is_hovered = False
    
    def draw(self):
        # Draw button background
        dudraw.set_pen_color(self.color)
        dudraw.filled_rectangle(self.x, self.y, self.width, self.height)
        
        # Draw button border
        dudraw.set_pen_color(dudraw.BLACK)
        dudraw.rectangle(self.x, self.y, self.width, self.height)
        
        # Draw button text
        dudraw.set_pen_color(dudraw.WHITE)
        dudraw.text(self.x, self.y, self.text)
    
    def is_clicked(self, mouse_x, mouse_y):
        return (self.x - self.width/2 <= mouse_x <= self.x + self.width/2 and
                self.y - self.height/2 <= mouse_y <= self.y + self.height/2)

# 2. Button Manager for Multiple Buttons
class ButtonManager:
    def __init__(self):
        self.buttons = []
    
    def add_button(self, button):
        self.buttons.append(button)
    
    def draw_all(self):
        for button in self.buttons:
            button.draw()
    
    def check_clicks(self, mouse_x, mouse_y):
        for button in self.buttons:
            if button.is_clicked(mouse_x, mouse_y):
                return button
        return None

# 3. Simple Button Implementation Example
def create_simple_button():
    # Create a button
    button = Button(400, 300, 100, 50, "Click Me!")
    
    # Main loop
    while True:
        # Clear screen
        dudraw.clear(dudraw.WHITE)
        
        # Draw button
        button.draw()
        
        # Check for mouse clicks
        if dudraw.mouse_pressed():
            mouse_x = dudraw.mouse_x()
            mouse_y = dudraw.mouse_y()
            
            if button.is_clicked(mouse_x, mouse_y):
                print("Button clicked!")
                # Add your button action here
        
        dudraw.show(10)

# 4. Multiple Buttons Example
def create_multiple_buttons():
    # Create button manager
    manager = ButtonManager()
    
    # Add buttons
    manager.add_button(Button(200, 200, 80, 40, "Start"))
    manager.add_button(Button(400, 200, 80, 40, "Stop"))
    manager.add_button(Button(300, 300, 80, 40, "Reset"))
    
    # Main loop
    while True:
        dudraw.clear(dudraw.WHITE)
        
        # Draw all buttons
        manager.draw_all()
        
        # Check for clicks
        if dudraw.mouse_pressed():
            mouse_x = dudraw.mouse_x()
            mouse_y = dudraw.mouse_y()
            
            clicked_button = manager.check_clicks(mouse_x, mouse_y)
            if clicked_button:
                if clicked_button.text == "Start":
                    print("Start button clicked!")
                elif clicked_button.text == "Stop":
                    print("Stop button clicked!")
                elif clicked_button.text == "Reset":
                    print("Reset button clicked!")
        
        dudraw.show(10)

# 5. Toggle Button Example
class ToggleButton(Button):
    def __init__(self, x, y, width, height, text, color=dudraw.GREEN):
        super().__init__(x, y, width, height, text, color)
        self.is_on = False
    
    def draw(self):
        # Change color based on state
        if self.is_on:
            dudraw.set_pen_color(dudraw.GREEN)
        else:
            dudraw.set_pen_color(dudraw.RED)
        
        dudraw.filled_rectangle(self.x, self.y, self.width, self.height)
        
        # Draw border and text
        dudraw.set_pen_color(dudraw.BLACK)
        dudraw.rectangle(self.x, self.y, self.width, self.height)
        dudraw.set_pen_color(dudraw.WHITE)
        dudraw.text(self.x, self.y, self.text)
    
    def toggle(self):
        self.is_on = not self.is_on

# 6. Color Picker Button Example
def create_color_picker():
    colors = [dudraw.RED, dudraw.GREEN, dudraw.BLUE, dudraw.YELLOW, dudraw.PURPLE]
    color_buttons = []
    
    for i, color in enumerate(colors):
        x = 100 + i * 80
        y = 100
        button = Button(x, y, 60, 60, "", color)
        color_buttons.append(button)
    
    current_color = dudraw.BLACK
    
    while True:
        dudraw.clear(dudraw.WHITE)
        
        # Draw color buttons
        for button in color_buttons:
            button.draw()
        
        # Draw current color indicator
        dudraw.set_pen_color(current_color)
        dudraw.filled_circle(400, 300, 50)
        dudraw.set_pen_color(dudraw.BLACK)
        dudraw.circle(400, 300, 50)
        
        # Check for color selection
        if dudraw.mouse_pressed():
            mouse_x = dudraw.mouse_x()
            mouse_y = dudraw.mouse_y()
            
            for i, button in enumerate(color_buttons):
                if button.is_clicked(mouse_x, mouse_y):
                    current_color = colors[i]
                    print(f"Selected color: {colors[i]}")
        
        dudraw.show(10)

# ===== USAGE EXAMPLES =====
# Uncomment the function you want to test:
# create_simple_button()
# create_multiple_buttons()
# create_color_picker()
"""

def self_repair_code(code: str, errors: List[str], retriever: DuDrawFunctionRetriever = None) -> str:
    """Automatically repair common DuDraw function errors and add missing imports using DuDraw database"""
    repaired_code = code
    
    # Smart import additions based on project type and missing imports
    project_lower = repaired_code.lower()
    
    # Add missing random import for games
    game_indicators = ['snake', 'pong', 'breakout', 'maze', 'food', 'brick', 'ball', 'enemy', 'spawn']
    if any(indicator in project_lower for indicator in game_indicators):
        if 'import random' not in repaired_code and 'random.' in repaired_code:
            repaired_code = repaired_code.replace('import dudraw', 'import dudraw\nimport random')
        elif 'import random' not in repaired_code:
            # Add random import proactively for games that should use it
            repaired_code = repaired_code.replace('import dudraw', 'import dudraw\nimport random')
    
    # Add missing math import - more comprehensive
    math_indicators = ['sin', 'cos', 'tan', 'pi', 'sqrt', 'atan2', 'asin', 'acos', 'degrees', 'radians']
    math_operations = ['pow(', 'abs(', 'floor(', 'ceil(', 'round(']
    
    has_math_functions = any(indicator in repaired_code for indicator in math_indicators)
    has_math_ops = any(op in repaired_code for op in math_operations)
    
    if (has_math_functions or has_math_ops) and 'import math' not in repaired_code:
        repaired_code = repaired_code.replace('import dudraw', 'import dudraw\nimport math')
    
    # Add missing time import
    if 'import time' not in repaired_code and 'time.' in repaired_code:
        repaired_code = repaired_code.replace('import dudraw', 'import dudraw\nimport time')
    
    # Common DuDraw function corrections
    corrections = {
        'dudraw.set_scale(': 'dudraw.set_x_scale(0, 20)\n    dudraw.set_y_scale(0, 20)',
        'dudraw.clear_canvas(': 'dudraw.clear(',
        'dudraw.draw_point(': 'dudraw.filled_circle(',
        'dudraw.get_key_press()': 'dudraw.next_key_typed()',
        'dudraw.set_pen_color(': 'dudraw.set_pen_color_rgb(',
        'dudraw.draw_text(': 'dudraw.text(',
        'dudraw.draw_line(': 'dudraw.line(',
        'dudraw.draw_rectangle(': 'dudraw.filled_rectangle(',
        'dudraw.draw_circle(': 'dudraw.filled_circle(',
    }
    
    # Apply corrections
    for incorrect, correct in corrections.items():
        if incorrect in repaired_code:
            repaired_code = repaired_code.replace(incorrect, correct)
    
    # Fix keyboard input patterns
    if 'dudraw.get_key_press()' in repaired_code:
        # Replace the problematic input loop pattern
        repaired_code = repaired_code.replace(
            'for _ in range(LIMIT):\n            key = dudraw.get_key_press()',
            'if dudraw.has_next_key_typed():\n            key = dudraw.next_key_typed()'
        )
    
    # Add missing enable_keyboard_input if needed
    if 'enable_keyboard_input' not in repaired_code and 'next_key_typed' in repaired_code:
        if 'initialize_game' in repaired_code:
            repaired_code = repaired_code.replace(
                'def initialize_game():',
                'def initialize_game():\n    dudraw.enable_keyboard_input()'
            )
    
    # Add missing show() calls
    if 'while True' in repaired_code and 'dudraw.show(' not in repaired_code:
        if 'draw_game' in repaired_code:
            repaired_code = repaired_code.replace(
                'def draw_game():',
                'def draw_game():\n    dudraw.show()\n    dudraw.delay(100)'
            )
    
    # Add missing canvas setup for games
    if any(word in project_lower for word in ['game', 'snake', 'pong', 'breakout']):
        if 'set_canvas_size' not in repaired_code:
            repaired_code = repaired_code.replace(
                'import dudraw',
                'import dudraw\n\n# Canvas setup\ndudraw.set_canvas_size(800, 600)'
            )
    
    # Add button code if button-related project
    button_terms = ['button', 'click', 'menu', 'interface', 'gui', 'ui']
    if any(term in project_lower for term in button_terms):
        if 'class Button' not in repaired_code and 'mouse_pressed' not in repaired_code:
            # Add button template code
            button_template = '''
# Button class for interactive interface
class Button:
    def __init__(self, x, y, width, height, text, color=dudraw.BLUE):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
    
    def draw(self):
        dudraw.set_pen_color(self.color)
        dudraw.filled_rectangle(self.x, self.y, self.width, self.height)
        dudraw.set_pen_color(dudraw.BLACK)
        dudraw.rectangle(self.x, self.y, self.width, self.height)
        dudraw.set_pen_color(dudraw.WHITE)
        dudraw.text(self.x, self.y, self.text)
    
    def is_clicked(self, mouse_x, mouse_y):
        return (self.x - self.width/2 <= mouse_x <= self.x + self.width/2 and
                self.y - self.height/2 <= mouse_y <= self.y + self.height/2)

'''
            repaired_code = repaired_code.replace('import dudraw', f'import dudraw{button_template}')
    
    # ENHANCED: Database-aware repairs
    if retriever:
        repaired_code = repair_using_dudraw_database(repaired_code, errors, retriever)
    
    return repaired_code

def repair_using_dudraw_database(code: str, errors: List[str], retriever: DuDrawFunctionRetriever) -> str:
    """Use DuDraw database to intelligently repair function errors"""
    repaired_code = code
    
    try:
        # Get all available functions from database
        try:
            results = retriever.collection.query(
                query_texts=["all functions"],
                n_results=100,
                include=['metadatas']
            )
        except Exception as e:
            st.warning(f"Database query failed: {e} - using fallback validation")
            return repaired_code
        
        available_functions = {}
        if results and results['metadatas'] and results['metadatas'][0]:
            for meta in results['metadatas'][0]:
                func_id = meta.get('id', '')
                syntax = meta.get('syntax', '')
                if func_id and syntax:
                    available_functions[func_id] = syntax
        
        # Repair invalid function calls
        import re
        
        # Find invalid dudraw function calls
        dudraw_pattern = r'dudraw\.(\w+)\s*\('
        matches = re.finditer(dudraw_pattern, code)
        
        for match in matches:
            func_name = match.group(1)
            func_id = f"dudraw.{func_name}"
            
            if func_id not in available_functions:
                # Try to find similar functions
                similar_functions = []
                for available_id, syntax in available_functions.items():
                    if func_name.lower() in available_id.lower() or available_id.lower() in func_name.lower():
                        similar_functions.append((available_id, syntax))
                
                if similar_functions:
                    # Replace with the most similar function
                    best_match = similar_functions[0]
                    old_call = f"dudraw.{func_name}("
                    new_call = best_match[1].split('(')[0] + "("
                    repaired_code = repaired_code.replace(old_call, new_call)
        
        # Add missing essential functions based on code analysis
        code_lower = code.lower()
        
        # Add keyboard input setup if needed - more comprehensive
        keyboard_terms = ['key', 'arrow', 'wasd', 'input', 'control', 'move']
        has_keyboard_terms = any(term in code_lower for term in keyboard_terms)
        
        if has_keyboard_terms and 'enable_keyboard_input' not in code:
            # Try to add to initialization functions
            init_functions = ['initialize_game', 'init_game', 'setup_game', 'main', 'setup']
            added = False
            
            for func_name in init_functions:
                if func_name in code:
                    pattern = f'def {func_name}():'
                    replacement = f'def {func_name}():\n    dudraw.enable_keyboard_input()'
                    if pattern in repaired_code:
                        repaired_code = repaired_code.replace(pattern, replacement)
                        added = True
                    break

            # If no initialization function found, add it to the top level
            if not added:
                repaired_code = repaired_code.replace(
                    'import dudraw',
                    'import dudraw\n\ndudraw.enable_keyboard_input()'
                )
        
        # Add missing show() calls in game loops
        if 'while True' in code and 'dudraw.show(' not in code:
            if 'draw_game' in code:
                repaired_code = repaired_code.replace(
                    'def draw_game():',
                    'def draw_game():\n    dudraw.show(10)'
                )
            elif 'game_loop' in code:
                repaired_code = repaired_code.replace(
                    'def game_loop():',
                    'def game_loop():\n    dudraw.show(10)'
                )
        
    except Exception as e:
        # If database repair fails, continue with basic repairs
        pass
    
    return repaired_code

def show_relevant_dudraw_functions(project_description: str, retriever: DuDrawFunctionRetriever):
    """Show relevant DuDraw functions for the project type"""
    try:
        # Check if retriever and collection are available
        if not retriever or not retriever.collection:
            st.markdown("**Note:** DuDraw function database not available for analysis.")
            return
        
        # Determine project type from description
        desc_lower = project_description.lower()
        
        # Define queries based on project type
        queries = []
        
        if any(word in desc_lower for word in ['game', 'snake', 'pong', 'breakout', 'maze']):
            queries.extend(['canvas setup', 'drawing shapes', 'keyboard input', 'display timing', 'colors'])
        elif any(word in desc_lower for word in ['animation', 'bouncing', 'moving', 'particle']):
            queries.extend(['canvas setup', 'drawing shapes', 'display timing', 'colors', 'math functions'])
        elif any(word in desc_lower for word in ['paint', 'draw', 'interactive', 'mouse']):
            queries.extend(['canvas setup', 'drawing shapes', 'mouse input', 'colors', 'display timing'])
        elif any(word in desc_lower for word in ['button', 'click', 'menu', 'interface', 'gui', 'ui']):
            queries.extend(['canvas setup', 'drawing shapes', 'mouse input', 'colors', 'text display'])
        else:
            # Default queries for any project
            queries.extend(['canvas setup', 'drawing shapes', 'display timing', 'colors'])
        
        # Get relevant functions
        relevant_functions = []
        for query in queries[:3]:  # Limit to 3 most relevant categories
            try:
                results = retriever.collection.query(
                    query_texts=[query],
                    n_results=3,
                    include=['metadatas']
                )
                if results and results['metadatas'] and results['metadatas'][0]:
                    for meta in results['metadatas'][0]:
                        relevant_functions.append({
                            'id': meta.get('id', ''),
                            'syntax': meta.get('syntax', ''),
                            'description': meta.get('description', '')
                        })
            except Exception as e:
                continue
        
        # Display relevant functions
        if relevant_functions:
            st.markdown("**Available DuDraw functions for this project:**")
            for func in relevant_functions[:6]:  # Show top 6 functions
                st.code(f"{func['syntax']} - {func['description']}")
        else:
            st.markdown("**Note:** Could not retrieve specific DuDraw functions for this project type.")
            
    except Exception as e:
        st.markdown("**Note:** Function analysis unavailable.")

# ================== UI ==================
st.title("DuDraw Code Generator")
st.markdown("Generate functional DuDraw programs from descriptions with detailed explanations")
st.divider()

if not groq_client:
    st.error("Cannot generate code without Groq API key.")
    st.stop()

# Initialize retriever
retriever = None
try:
    retriever = DuDrawFunctionRetriever()
    st.sidebar.success("DuDraw Function Retriever Ready")
except Exception as e:
    st.error(f"Failed to initialize function retriever: {e}")
    st.stop()

# Add database reset option in sidebar
if st.sidebar.button("Reset Database"):
    import os
    import shutil
    if os.path.exists("./chroma_db"):
        try:
            shutil.rmtree("./chroma_db")
            st.sidebar.success("Database reset successfully!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Failed to reset database: {e}")
    else:
        st.sidebar.info("No database to reset")

# Main input section
st.subheader("Project Description")
user_input = st.text_area(
    "Describe your DuDraw project:",
    placeholder="e.g., 'Create a snake game with arrow key controls'\n'Draw a bouncing ball animation'\n'Make a simple paint program'",
    height=100
)

# Action buttons
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    generate_btn = st.button("Generate Code", type="primary", use_container_width=True)

with col2:
    if st.button("Show Examples", use_container_width=True):
        with st.expander("Example Project Ideas", expanded=True):
            st.markdown("""
            **Games:**
            - Snake game with arrow key controls
            - Pong game with paddle movement
            - Simple maze game
            - Breakout/brick breaker game
            
            **Animations:**
            - Bouncing ball simulation
            - Rotating geometric patterns
            - Particle system effects
            - Solar system animation
            
            **Interactive:**
            - Paint program with mouse drawing
            - Calculator with button interface
            - Digital clock display
            - Color picker tool
            """)

with col3:
    if st.button("Button Templates", use_container_width=True):
        with st.expander("DuDraw Button Code Templates", expanded=True):
            st.code(get_button_code_template(), language='python')
            st.markdown("""
            **Quick Button Examples:**
            - **Simple Button**: Basic clickable button
            - **Multiple Buttons**: Button manager for multiple buttons
            - **Toggle Button**: On/off state button
            - **Color Picker**: Interactive color selection
            """)

st.divider()

# Generate code when button is pressed
if generate_btn and user_input.strip():
    with st.spinner("Generating your DuDraw code..."):
        try:
            # Generate code
            response = generate_dudraw_code(user_input.strip(), retriever)
            code = extract_code(response)
            explanation = extract_explanation(response)
            
            if code:
                # Create tabs for better organization
                tab1, tab2, tab3 = st.tabs(["Generated Code", "Validation Results", "Function Analysis"])
                
                with tab1:
                    st.subheader("Generated DuDraw Code")
                    st.code(code, language="python")
                    
                    if explanation:
                        st.subheader("Code Explanation")
                        st.markdown(explanation)
                
                with tab2:
                    st.subheader("Validation Results")
                    
                    # Validate code against DuDraw database
                    errors = validate_code(code, retriever)
                    
                    # Auto-repair common errors
                    if errors:
                        st.warning("Detected some issues in the generated code. Attempting to auto-repair...")
                        original_code = code
                        code = self_repair_code(code, errors, retriever)
                        
                        # Re-validate after repair against DuDraw database
                        new_errors = validate_code(code, retriever)
                        
                        if len(new_errors) < len(errors):
                            st.success(f"Auto-repair successful! Reduced errors from {len(errors)} to {len(new_errors)}")
                            errors = new_errors
                        else:
                            st.warning("Auto-repair did not improve the code significantly")
                            code = original_code
                    
                    # Display validation results
                    if errors:
                        st.error(f"**Validation Results:** {len(errors)} issues found")
                        for error in errors:
                            st.error(f"• {error}")
                    else:
                        st.success("**Validation Results:** No issues found!")
                
                with tab3:
                    st.subheader("DuDraw Function Analysis")
                    show_relevant_dudraw_functions(user_input.strip(), retriever)
                    
                    if any(term in user_input.lower() for term in ['button', 'click', 'menu', 'interface', 'gui', 'ui']):
                        st.info("**Button Code Suggestions:**")
                        st.markdown("""
**For button interfaces, consider using:**
- `dudraw.mouse_pressed()` - Check if mouse is pressed
- `dudraw.mouse_x()` - Get mouse X position
- `dudraw.mouse_y()` - Get mouse Y position
- `dudraw.filled_rectangle()` - Draw button background
- `dudraw.text()` - Draw button text
""")
                        st.markdown("**Click 'Button Templates' for complete examples!**")
            else:
                st.error("Failed to generate code. Please try again.")
                
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.error("Please try again with a simpler request.")

elif generate_btn and not user_input.strip():
    st.warning("Please describe what you want to create!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>DuDraw Code Generator - Powered by AI</p>
    <p>Built with Streamlit, ChromaDB, and Groq API</p>
</div>
""", unsafe_allow_html=True) 