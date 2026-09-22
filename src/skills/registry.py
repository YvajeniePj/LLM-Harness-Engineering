"""Registry and dynamic injector for external Skills."""

from pathlib import Path
from typing import Dict, List, Optional
import yaml

from src.schema import Skill


class SkillRegistry:
    """Manages loading, validating, and injecting modular Skills into Subagents."""

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or (Path(__file__).resolve().parent.parent.parent / "skills")
        self._skills: Dict[str, Skill] = {}
        self.load_all()

    def load_all(self) -> None:
        """Scan skills directory and parse all skill definition markdown files."""
        self._skills.clear()
        if not self.skills_dir.exists():
            return

        for file_path in self.skills_dir.glob("*.md"):
            try:
                skill = self._parse_skill_file(file_path)
                if skill:
                    self._skills[skill.name] = skill
            except Exception as exc:
                print(f"[SkillRegistry] Warning: failed to parse {file_path.name}: {exc}")

    def _parse_skill_file(self, file_path: Path) -> Optional[Skill]:
        """Parse frontmatter and markdown body from a skill file."""
        text = file_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None

        parts = text.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter_str = parts[1]
        content = parts[2].strip()

        meta = yaml.safe_load(frontmatter_str) or {}
        name = meta.get("name", file_path.stem)
        title = meta.get("title", name.replace("_", " ").title())
        version = str(meta.get("version", "1.0.0"))
        target_agents = meta.get("target_agents", [])
        description = meta.get("description", "")
        tags = meta.get("tags", [])

        return Skill(
            name=name,
            title=title,
            version=version,
            target_agents=target_agents,
            description=description,
            tags=tags,
            content=content,
        )

    def get(self, name: str) -> Optional[Skill]:
        """Retrieve a skill by its unique identifier."""
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        """Return list of all registered skills."""
        return list(self._skills.values())

    def format_skills_injection(self, skill_names: List[str]) -> str:
        """Format requested skills into an authoritative injected prompt block.
        
        This is the runtime injection mechanism that equips the subagent
        with specific domain methodologies without bloating the global prompt.
        """
        if not skill_names:
            return ""

        blocks = []
        blocks.append("================================================================================")
        blocks.append("RUNTIME INJECTED SKILLS & DOMAIN STANDARDS:")
        blocks.append("The following specialized methodologies and rules are active for this execution.")
        blocks.append("You MUST adhere strictly to all guidelines specified below.")
        blocks.append("================================================================================\n")

        found_any = False
        for name in skill_names:
            skill = self.get(name)
            if not skill:
                continue
            found_any = True
            blocks.append(f"### SKILL: {skill.title} (v{skill.version})")
            blocks.append(f"Description: {skill.description}")
            blocks.append(f"Target Roles: {', '.join(skill.target_agents)}")
            blocks.append(f"\n{skill.content}\n")
            blocks.append("--------------------------------------------------------------------------------")

        if not found_any:
            return ""

        return "\n".join(blocks)
