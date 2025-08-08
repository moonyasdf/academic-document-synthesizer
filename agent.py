import os
import sys
import json
import requests
import re
import time
import difflib
from pydantic import ValidationError
from schemas import RefinementPlan

class SynthesisAgent:
    """
    An AI agent for synthesizing and refining academic documents,
    featuring config-driven behavior, debugging logs, and robust parsing with Pydantic.
    """
    def __init__(self, problem_statement, language, api_key, checkpoint_path, config):
        """
        Initializes the agent.
        """
        self.problem_statement = problem_statement
        self.language = language
        self.api_key = api_key
        self.checkpoint_path = checkpoint_path
        self.config = config
        self.prompts = self._load_prompts()
        
        model_name = self.config['model_config']['model_name']
        self.api_url = self.config['model_config']['api_endpoint'].format(model_name=model_name)
        self.headers = {"Content-Type": "application/json", "X-goog-api-key": self.api_key}
        
        if self.config['debugging']['debug_mode']:
            self.debug_log_dir = self.config['debugging']['log_directory']
            os.makedirs(self.debug_log_dir, exist_ok=True)
            print(f"DEBUG MODE ENABLED: Raw LLM responses will be saved to '{self.debug_log_dir}'")
        
        self.synthesis_step = 0

    def _load_prompts(self):
        """Loads all necessary prompts from the 'prompts' directory."""
        prompt_files = ["system_expert_prompt.txt", "initial_synthesis_prompt.txt", "iterative_refinement_prompt.txt"]
        prompts = {}
        for filename in prompt_files:
            try:
                with open(os.path.join("prompts", filename), 'r', encoding='utf-8') as f:
                    key = os.path.splitext(filename)[0].replace('_prompt', '')
                    prompts[key] = f.read()
            except FileNotFoundError:
                print(f"Error: Prompt file not found at 'prompts/{filename}'")
                sys.exit(1)
        return prompts

    def _save_debug_log(self, step_name, response_text):
        """Saves the raw LLM response to a file if debug mode is active."""
        if not self.config['debugging']['debug_mode']:
            return
        
        self.synthesis_step += 1
        filename = f"step_{self.synthesis_step}_{step_name}.txt"
        filepath = os.path.join(self.debug_log_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"  -> Debug log saved: {filepath}")
        except IOError as e:
            print(f"  -> Warning: Could not save debug log. Error: {e}")

    def _call_api(self, system_prompt, user_prompt, temperature=None, retries=3):
        """Sends a request to the Gemini API, using settings from config."""
        temp = temperature if temperature is not None else self.config['model_config']['temperature']
        
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temp,
                "topP": 0.95,
                "thinkingConfig": {"thinkingBudget": 32768}
            },
        }
        for attempt in range(retries):
            try:
                response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))
                response.raise_for_status()
                candidates = response.json().get('candidates')
                if candidates and candidates[0].get('content', {}).get('parts'):
                    return candidates[0]['content']['parts'][0]['text']
                else:
                    print(f"API Warning: Unexpected response format or empty content. Full response: {response.json()}")
                    finish_reason = candidates[0].get('finishReason', 'UNKNOWN')
                    print(f"Finish Reason: {finish_reason}")
                    return ""
            except requests.exceptions.RequestException as e:
                print(f"API Error (Attempt {attempt + 1}/{retries}): {e}")
                time.sleep(2 ** attempt)
        return None
    
    def _save_checkpoint(self, document_content):
        """Saves the current state of the document to the checkpoint file."""
        try:
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                f.write(document_content)
            print(f"  -> Checkpoint saved successfully to {self.checkpoint_path}")
        except IOError as e:
            print(f"  -> Warning: Could not save checkpoint. Error: {e}")

    def _load_from_checkpoint(self):
        """Loads the document from a checkpoint file if it exists."""
        if os.path.exists(self.checkpoint_path):
            print(f"Checkpoint file found at '{self.checkpoint_path}'. Resuming progress.")
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def _generate_initial_draft(self):
        """Generates the first complete draft of the document."""
        print("Generating initial draft...")
        user_prompt = self.prompts['initial_synthesis'].format(
            language=self.language,
            problem_statement=self.problem_statement
        )
        draft = self._call_api(self.prompts['system_expert'], user_prompt)
        if draft:
            self._save_debug_log("initial_draft", draft)
            print("Initial draft generated successfully.")
        else:
            print("Failed to generate initial draft.")
            sys.exit(1)
        return draft

    def _request_refinement_plan(self, document_content):
        """Asks the LLM to act as a peer reviewer, providing the original task context."""
        print("Requesting context-aware peer review and refinement plan from LLM...")
        user_prompt = self.prompts['iterative_refinement'].format(
            problem_statement=self.problem_statement,
            document_content=document_content
        )
        plan_raw = self._call_api(self.prompts['system_expert'], user_prompt, temperature=0.2)
        if plan_raw:
            self._save_debug_log("refinement_plan", plan_raw)
            print("Refinement plan (raw) received.")
        return plan_raw

    # --- NUEVO: Función para extraer JSON del Markdown ---
    def _extract_json_from_markdown(self, text):
        """Extracts JSON content enclosed in markdown code blocks."""
        # Regex to find blocks of code, optionally prefixed by 'json' or '```'
        json_pattern = re.compile(r'```(?:json)?\s*\n([\s\S]*?)\n```', re.DOTALL)
        match = json_pattern.search(text)
        if match:
            return match.group(1).strip()
        
        # Fallback: if no markdown blocks found, try to parse the entire text as JSON
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            return text
        
        return None
    # --- FIN DE _extract_json_from_markdown ---

    def _apply_refinements(self, document, refinement_plan: RefinementPlan):
        """Aplica las secciones refinadas del plan Pydantic al documento."""
        if not refinement_plan.refined_sections:
            print("No sections were rewritten in this cycle.")
            return document, False

        # Usamos el parser de reconstrucción que ya era robusto
        original_sections = {}
        section_pattern = re.compile(r'(##\s+([^\n]+))\n([\s\S]*?)(?=\n##\s+|\Z)')
        for match in section_pattern.finditer(document):
            title = match.group(2).strip()
            content = match.group(3).strip()
            original_sections[title] = content
        
        updates = {section.section_title: section.content for section in refinement_plan.refined_sections if section.content is not None}

        new_document_parts = []
        for title, original_content in original_sections.items():
            new_content = updates.get(title, original_content)
            new_document_parts.append(f"## {title}\n{new_content}\n")
            if title in updates:
                print(f"  - Applying update to section '{title}'.")
        
        new_document = "\n".join(new_document_parts)
        changes_made = new_document.strip() != document.strip()
        
        return new_document, changes_made

    def synthesize(self, max_refinements):
        """Main synthesis loop with Pydantic-based validation and intelligent termination."""
        document = self._load_from_checkpoint()
        if document is None:
            document = self._generate_initial_draft()
            if document: self._save_checkpoint(document)
        else:
            print("Successfully loaded document from checkpoint.")

        confidence_threshold = self.config['synthesis_config']['confidence_threshold']
        consecutive_final_versions = 0
        i = 0 # Initialize i for the final log message

        for i in range(max_refinements):
            print(f"\n--- Starting Refinement Cycle {i + 1}/{max_refinements} ---")
            
            plan_raw = self._request_refinement_plan(document)
            
            if not plan_raw:
                print("Skipping refinement cycle due to API failure.")
                consecutive_final_versions = 0
                continue
            
            # --- MODIFICACIÓN CLAVE: Extraer el JSON antes de la validación ---
            plan_json_str = self._extract_json_from_markdown(plan_raw)

            if not plan_json_str:
                print("❌ ERROR: LLM response did not contain a parseable JSON structure. Retrying in next cycle.")
                consecutive_final_versions = 0
                continue
            
            try:
                refinement_plan = RefinementPlan.model_validate_json(plan_json_str)
                
                verdict = refinement_plan.final_verdict
                print(f"Reviewer Verdict: {verdict}")
                print("\n--- LLM's Summary of Findings ---")
                for finding in refinement_plan.summary_of_findings:
                    # Imprimimos los hallazgos de forma limpia
                    print(f"* Location: {finding.location}, Classification: {finding.classification}")
                    print(f"  Issue: {finding.issue}")
                print("---------------------------------\n")

                if verdict == "NO_FURTHER_IMPROVEMENTS_NEEDED":
                    consecutive_final_versions += 1
                    print(f"Confidence counter for completion is now {consecutive_final_versions}/{confidence_threshold}.")
                    if consecutive_final_versions >= confidence_threshold:
                        print("\n✅ Agent has confirmed document quality and task fulfillment. Terminating refinement process early.")
                        break
                else:
                    consecutive_final_versions = 0
                
                # Aplicamos los refinamientos
                document, changes_made = self._apply_refinements(document, refinement_plan)
                
                if changes_made:
                    self._save_checkpoint(document)
                else:
                    print("No substantial changes were applied in this cycle.")

            except ValidationError as e:
                print(f"\n❌ CRITICAL PARSING ERROR: LLM response did not match Pydantic schema.")
                print(f"Pydantic Validation Errors: {e}")
                consecutive_final_versions = 0
                continue
        
        if i == max_refinements - 1 and consecutive_final_versions < confidence_threshold:
             print(f"\n⚠️  Reached maximum refinement limit.")

        print("\nSynthesis process completed.")
        return document