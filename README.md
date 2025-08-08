# Academic Document Synthesizer

An AI-powered tool for generating and refining structured academic documents using Google's Gemini API. This project is designed in the style of a self-contained, minimal-dependency solver, inspired by the rigorous, logic-driven approach of state-of-the-art AI problem solvers.

## Overview

This system employs a sophisticated AI agent that performs a two-stage process, mimicking an expert academic workflow:
1.  **Initial Drafting**: The agent first generates a complete, structured academic document based on a given problem statement and a set of core principles demanding rigor and clarity.
2.  **Peer-Review Refinement Loop**: It then enters an iterative cycle where the AI agent assumes the role of a meticulous peer reviewer. It first analyzes the entire document to produce a "Summary of Findings," identifying logical flaws and justification gaps. Based on this analysis, it then rewrites only the necessary sections to improve the document's overall quality.

This "Analyze-Then-Rewrite" methodology, inspired by verifier-guided AI systems, ensures that improvements are reasoned and targeted, leading to a higher-quality final product.

## Features

- **Peer-Review Refinement Loop**: A sophisticated process where the agent first critiques the entire document and then acts on its own critique, ensuring targeted and logical improvements.
- **Rigor-Driven Prompts**: The prompt architecture is heavily inspired by the logical constraints used in advanced mathematical problem-solvers, conditioning the model for high-quality, structured output.
- **Minimal Dependencies**: Requires only the `requests` library for maximum portability and ease of use.
- **Interactive Language Selection**: Prompts the user for the desired output language with a confirmation step.
- **Modular Prompt System**: All prompts are stored in a `prompts/` directory, allowing for easy customization of the agent's persona and tasks without altering code.
- **Robust API Interaction**: Includes exponential backoff for API calls to handle transient network issues gracefully.

## Prerequisites

1.  **Python 3.7+**
2.  **Google Gemini API Key**: Obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).
3.  **Required Python package**:
    ```bash
    pip install requests
    ```

## Setup

1.  **Clone or download the project files.**
2.  **Set up your API key**: The script reads the API key from an environment variable.
    ```bash
    export GOOGLE_API_KEY="your_api_key_here"
    ```
3.  **Prepare your problem statement**: Modify `problem_statement.txt` with the details of the academic task you want the agent to perform.

## Usage

Run the main synthesis script from your terminal:

```bash
python run_synthesis.py [problem_file] [options]