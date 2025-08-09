from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# Definimos un alias para los tipos de veredicto permitidos
VerdictType = Literal[
    "SIGNIFICANT_IMPROVEMENTS_REQUIRED",
    "MINOR_IMPROVEMENTS_SUGGESTED",
    "NO_FURTHER_IMPROVEMENTS_NEEDED"
]

# Definimos un alias para los tipos de fallo permitidos
IssueType = Literal["Critical Flaw", "Justification Gap"]

class Finding(BaseModel):
    """
    Modelo para un único hallazgo en la revisión.
    Usa alias para ser más flexible con lo que el LLM genera.
    """
    location: str = Field(
        description="The standardized English section title where the issue occurs (e.g., 'Introduction')."
    )
    issue: str = Field(
        description="A brief description of the problem."
    )
    classification: IssueType = Field(
        alias="Issue Classification",
        description="The classification of the issue."
    )

class RefinedSection(BaseModel):
    """
    Modelo para una única sección reescrita.
    Inspirado en OpenEvolve para localizar y reemplazar contenido.
    """

    section_title: str = Field(
        description="The standardized English title of the section to be replaced (e.g., 'Discussion')."
    )
    content: str = Field(
        description="The full, rewritten content for this section."
    )

class RefinementPlan(BaseModel):
    """
    Este es el modelo Pydantic principal para la respuesta del agente refinador.
    El LLM debe generar un JSON que valide contra este modelo.
    """
    final_verdict: VerdictType = Field(
        alias="Final Verdict",
        description="The overall verdict on the document's quality."
    )
    summary_of_findings: List[Finding] = Field(
        alias="Summary of Findings",
        description="A list of all issues discovered in the document."
    )
    # Hacemos que las secciones refinadas sean opcionales. Si el LLM no quiere cambiar nada, puede omitirlo.
    refined_sections: Optional[List[RefinedSection]] = Field(
        default=None,
        alias="Refined Document Sections",
        description="A list of sections to be updated with new content."
    )