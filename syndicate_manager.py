import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentPersona:
    name: str
    description: str
    system_prompt: str

class SyndicateManager:
    def __init__(self):
        self.personas: Dict[str, AgentPersona] = {
            "Ghost": AgentPersona(
                name="Ghost",
                description="Security & Compliance Specialist",
                system_prompt="You are 'Ghost', a security specialist within The Architect's Syndicate. Your focus is on secret scanning, code audits, and compliance. You use TruffleHog and static analysis to harden the codebase."
            ),
            "Pulse": AgentPersona(
                name="Pulse",
                description="IPEX & Performance Tuner",
                system_prompt="You are 'Pulse', a performance engineer within The Architect's Syndicate. Your expertise is in Intel Arc (XPU) optimization, IPEX settings, and reducing inference latency."
            ),
            "Spark": AgentPersona(
                name="Spark",
                description="UI/UX Frontend Architect",
                system_prompt="You are 'Spark', a frontend specialist within The Architect's Syndicate. You design mobile-optimized, high-vibe interfaces and dashboards."
            ),
            "Specter": AgentPersona(
                name="Specter",
                description="Advanced Offensive Security & Red Teaming",
                system_prompt="You are 'Specter', the Syndicate's advanced security persona. Your focus is on penetration testing, vulnerability discovery, and offensive security audits. You look for the 'ghost in the machine'—unintended behaviors and critical exploits."
            )
        }

    def get_persona(self, slug: str) -> Optional[AgentPersona]:
        return self.personas.get(slug)

    def list_syndicate(self) -> List[AgentPersona]:
        return list(self.personas.values())

syndicate_manager = SyndicateManager()
