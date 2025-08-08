# Academic Document Synthesizer

An AI-powered tool for generating and refining structured academic documents, optimized to use Google's Gemini 2.5 Pro. This project is designed as a self-contained, minimal-dependency solver, inspired by the rigorous, logic-driven approach of state-of-the-art AI problem solvers.

 <!-- Opcional: Puedes crear un diagrama de flujo simple y subirlo a un host de imágenes como Imgur -->

## Overview

This system employs a sophisticated AI agent that performs a two-stage process, mimicking an expert academic workflow:

1.  **Initial Drafting**: Guided by a highly structured prompt, the agent first generates a complete, high-quality draft of an academic document based on a given problem statement.
2.  **Peer-Review Refinement Loop**: The agent then enters an iterative cycle where it assumes the role of a meticulous "Academic Consultant." It analyzes the entire document against the original requirements, identifies flaws and gaps, and then generates a superior, rewritten version. This process repeats until a high standard of quality is met or a maximum number of cycles is reached.

The system features intelligent termination, stopping automatically when it determines the document is of sufficient quality, making it efficient and autonomous.

## Key Features

- **Optimized for Gemini 2.5 Pro**: Pre-configured to leverage the advanced reasoning capabilities of Gemini 2.5 Pro, using a low temperature (`0.1`) and a large `thinkingBudget` for focused, coherent, and high-quality output.
- **Intelligent Termination**: The agent autonomously decides when to stop the refinement process based on its own quality assessment, requiring multiple consecutive "no improvements needed" verdicts to gain confidence.
- **Robust Checkpointing**: Automatically saves progress after each successful refinement cycle to a temporary file. If the process is interrupted (e.g., API credit exhaustion, network error), it can be resumed seamlessly by running the same command again.
- **Pydantic-based Validation**: Uses Pydantic schemas to validate the structure of the LLM's refinement plans, eliminating parsing errors and ensuring reliable operation.
- **Config-Driven Behavior**: The entire process is controlled by a central `config.yaml` file, allowing easy customization of the model, synthesis parameters, and debugging options without touching the code.
- **Debug Mode**: Includes an optional debug mode which saves all raw LLM responses to a `debug_logs/` directory for easy analysis and troubleshooting.
- **User-Friendly Interaction**: Handles API key management gracefully (prioritizing environment variables but falling back to a secure prompt) and asks for the desired output language.

## Prerequisites

1.  **Python 3.7+**
2.  **Google Gemini API Key**: Obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey). Ensure your key has access to the `gemini-1.5-pro-latest` model.
3.  **Required Python packages**: Install them using the provided file.
    ```bash
    pip install -r requirements.txt
    ```

## Project Structure

```
.
├── README.md
├── config.yaml
├── run_synthesis.py
├── agent.py
├── schemas.py
├── requirements.txt
├── problem_statement.txt
└── prompts/
    ├── system_expert_prompt.txt
    ├── initial_synthesis_prompt.txt
    └── iterative_refinement_prompt.txt
```

## Setup & Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/academic-document-synthesizer.git
    cd academic-document-synthesizer
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the API Key:** You have two options:
    *   **(Recommended) Set an environment variable:**
        ```bash
        # On Linux/macOS
        export GOOGLE_API_KEY="your_api_key_here"
        
        # On Windows PowerShell
        $env:GOOGLE_API_KEY="your_api_key_here"
        ```
    *   **Or, run the script:** If the environment variable is not found, the script will prompt you to enter the key securely.

4.  **Edit `problem_statement.txt`:** Replace the content of this file with the specific academic task you want the agent to perform.

5.  **(Optional) Edit `config.yaml`:**
    *   To disable debug logging, set `debug_mode: false`.
    *   To change the number of refinement cycles, adjust `max_refinements`.
    *   To modify the model, update `model_name`.

## Usage

The main entry point for the synthesizer is `run_synthesis.py`.

1.  Navigate to the project directory in your terminal.
2.  Run the script.

    ```bash
    python run_synthesis.py [problem_file] [options]
    ```

The script will first ask for your API key (if not set as an environment variable) and then for your preferred language.

**Arguments & Options:**

-   `problem_file` (optional): Path to the problem statement file. Defaults to `problem_statement.txt`.
-   `--output <path>`, `-o <path>`: Specify the path for the final Markdown document. Defaults to `output/final_document.md`.
-   `--max-refinements <N>`, `-r <N>`: Override the `max_refinements` setting from `config.yaml`. Acts as a safeguard limit for the refinement loop.

**Example Workflows:**

-   **Standard Run:**
    ```bash
    python run_synthesis.py
    ```

-   **Run with a different task and higher refinement limit:**
    ```bash
    python run_synthesis.py my_other_task.txt -r 10
    ```

-   **Resume an interrupted run:** Simply execute the exact same command you used before. The agent will automatically find the checkpoint file and resume the process.
    ```bash
    # If this command was interrupted...
    python run_synthesis.py --output results/my_paper.md
    
    # ...just run it again to resume.
    python run_synthesis.py --output results/my_paper.md
    ```

## How It Works

1.  **Configuration Loading:** `run_synthesis.py` loads all settings from `config.yaml`.
2.  **Initialization:** It prompts the user for necessary inputs (API key, language) and initializes the `SynthesisAgent`.
3.  **Drafting/Resuming:** The agent first checks for a checkpoint file. If found, it loads the existing document. If not, it uses the powerful `initial_synthesis_prompt.txt` to generate a high-quality first draft. A checkpoint is saved.
4.  **Refinement Loop:**
    a. The agent sends the current document and the original problem statement to the LLM using the `iterative_refinement_prompt.txt`. This prompt instructs the model to act as a consultant and return a **JSON object** defined by the Pydantic `RefinementPlan` schema.
    b. The agent receives the raw text response and, if in debug mode, saves it to `debug_logs/`.
    c. It extracts the JSON block from the response.
    d. It uses `RefinementPlan.model_validate_json()` to parse and validate the JSON. If this fails, it reports the error and skips the cycle.
    e. It checks the `final_verdict` from the validated plan. If the verdict is `NO_FURTHER_IMPROVEMENTS_NEEDED` for a configured number of consecutive times, the loop terminates early.
    f. It applies the changes from the `refined_sections` to the document by reconstructing it, which prevents duplication errors.
    g. If changes were made, a new checkpoint is saved.
5.  **Final Output:** The final refined document is saved to the specified output file, and the temporary checkpoint file is deleted.
