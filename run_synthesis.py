import os
import sys
import argparse
import getpass
import yaml
from agent import SynthesisAgent
from schemas import RefinementPlan # Importamos el modelo Pydantic

def load_config():
    """Loads configuration from config.yaml."""
    try:
        with open("config.yaml", 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config.yaml not found. Please ensure it exists in the project directory.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}")
        sys.exit(1)

def get_api_key_from_env():
    """Retrieves the Google API key, falling back to interactive prompt."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("API key found in environment variable GOOGLE_API_KEY.")
        return api_key
    else:
        print("Environment variable GOOGLE_API_KEY not found.")
        print("Please enter your Google Gemini API key.")
        try:
            api_key = getpass.getpass("API Key: ")
            if not api_key:
                print("Error: API Key cannot be empty.")
                sys.exit(1)
            return api_key
        except Exception as e:
            print(f"Error: Could not read API key from prompt: {e}")
            sys.exit(1)

def read_file_content(filepath):
    """Reads and returns the content of a file, exiting on error."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found at '{filepath}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")
        sys.exit(1)

def get_user_language_preference():
    """Prompts the user for their preferred language with confirmation."""
    while True:
        language = input("In which language do you want the response and the document? (e.g., English, Spanish): ")
        if not language.strip():
            print("Language cannot be empty. Please try again.")
            continue
        
        while True:
            confirm = input(f"You have selected '{language}'. Are you sure? [y/n]: ").lower()
            if confirm in ['y', 'yes']:
                return language
            elif confirm in ['n', 'no']:
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

def main():
    parser = argparse.ArgumentParser(
        description='Academic Document Synthesizer with robust JSON parsing and intelligent termination.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('problem_file', default='problem_statement.txt', nargs='?')
    parser.add_argument('--output', '-o', default='output/final_document.md', help='Path for the final output markdown file (default: output/final_document.md)')
    # max_refinements is now controlled by config.yaml, but can be overridden by command line.
    parser.add_argument('--max-refinements', '-r', type=int, default=None, help='Maximum number of refinement cycles to perform (safeguard). Overrides config.')
    args = parser.parse_args()

    # --- Setup ---
    config = load_config()
    api_key = get_api_key_from_env()
    problem_statement = read_file_content(args.problem_file)
    language = get_user_language_preference()
    
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.splitext(os.path.basename(args.output))[0]
    checkpoint_path = os.path.join(output_dir, f".{output_filename}_checkpoint.md")

    print("\n--- Starting Synthesis Process ---")
    
    max_refinements = args.max_refinements if args.max_refinements is not None else config['synthesis_config']['max_refinements']
    
    # --- Agent Execution ---
    agent = SynthesisAgent(problem_statement, language, api_key, checkpoint_path, config)
    final_document = agent.synthesize(max_refinements=max_refinements)
    
    # --- Output and Cleanup ---
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(final_document)
        print(f"\n✅ Success! The final document has been saved to: {args.output}")

        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            print("Checkpoint file removed.")
            
    except IOError as e:
        print(f"\n❌ Error: Could not write the final document. Progress is saved in {checkpoint_path}")
        print(f"Error details: {e}")

if __name__ == "__main__":
    # Ensure main is protected by if __name__ == "__main__":
    # for proper multiprocessing initialization
    main()