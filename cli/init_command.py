#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive project initialization wizard for ΔP.
"""

import sys
import os
from pathlib import Path
from typing import List, Optional
import shutil


def simple_input(prompt: str, default: str = "") -> str:
    """Simple input with default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def simple_confirm(prompt: str, default: bool = True) -> bool:
    """Simple yes/no confirmation"""
    default_str = "Y/n" if default else "y/N"
    choice = input(f"{prompt} ({default_str}): ").strip().lower()
    
    if not choice:
        return default
    return choice in ['y', 'yes']


def render_template(template_path: Path, context: dict) -> str:
    """Simple template rendering (replace {{var}} with values)"""
    content = template_path.read_text()
    
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, str(value))
    
    return content


def create_project_structure(
    project_name: str,
    init_git: bool,
    author: str,
    description: str,
    starter_module: str,
    template: str,
    include_examples: bool
):
    """Create project directory structure"""
    project_path = Path.cwd() / project_name
    
    if project_path.exists():
        if not simple_confirm(f"Directory '{project_name}' exists. Overwrite?", False):
            print("Aborted.")
            return False
        shutil.rmtree(project_path)
    
    project_path.mkdir()
    
    # Get template directory
    template_dir = Path(__file__).parent / "templates" / "project"
    
    if not template_dir.exists():
        print(f"Error: Template directory not found: {template_dir}")
        return False
    
    # Context for template rendering
    context = {
        "project_name": project_name,
        "author": author,
        "description": description,
    }
    
    # Create deltap.toml
    toml_template = template_dir / "deltap.toml.template"
    if toml_template.exists():
        toml_content = render_template(toml_template, context)
        (project_path / "deltap.toml").write_text(toml_content)
    else:
        # Fallback if template missing
        toml_content = f"""[project]
name = "{project_name}"
version = "0.1.0"
authors = ["{author}"]
description = "{description}"

[dependencies]
# Add dependencies here
"""
        (project_path / "deltap.toml").write_text(toml_content)
    
    # Create directory structure
    (project_path / "src" / "data").mkdir(parents=True, exist_ok=True)
    (project_path / "src" / "results").mkdir(parents=True, exist_ok=True)
    (project_path / "src").mkdir(exist_ok=True)

    # Copy examples if requested                             
    if include_examples:                                     
        examples_source = Path(__file__).parent.parent / "examples"
        
        if examples_source.exists():
            examples_dest = project_path / "src" / "_examples"
            shutil.copytree(examples_source, examples_dest)
            print(f"✓ Copied example modules to src/_examples/")
        else:
            print(f"  Warning: Examples directory not found at {examples_source}")
    
    # Create .gitignore if git enabled
    if init_git:
        gitignore_template = template_dir / "gitignore.template"
        if gitignore_template.exists():
            gitignore_content = gitignore_template.read_text()
            (project_path / ".gitignore").write_text(gitignore_content)
        else:
            # Fallback gitignore
            gitignore_content = """# ΔP
*.h5
delta_db.h5
results/
__pycache__/
*.pyc

# OS
.DS_Store
Thumbs.db
"""
            (project_path / ".gitignore").write_text(gitignore_content)
    
    # Initialize git if requested
    if init_git:
        import subprocess
        try:
            subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
            print(f"✓ Initialized git repository")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  (git init failed - git may not be installed)")
    
    # Create starter module using add_command
    print(f"✓ Creating starter module: {starter_module}")

    # Change to project directory temporarily
    original_dir = os.getcwd()
    os.chdir(project_path)

    try:
        from .add_command import cmd_add
        
        # Create args object
        class ModuleArgs:
            pass
        
        args = ModuleArgs()
        args.module_name = starter_module
        args.template = template
        
        result = cmd_add(args)
        if result != 0:
            print(f"Warning: Failed to create starter module")
    except ImportError:
        print(f"Warning: Could not import add_command, skipping starter module creation")
    finally:
        os.chdir(original_dir)
    
    return True


def cmd_init(args=None):
    """Main init command"""
    print("\nWelcome to ΔP Project Setup!\n")
    
    # 1. Project name
    if args and hasattr(args, 'name') and args.name:
        # Name provided via command line
        project_name = args.name
        print(f"Project name: {project_name}")
        print()
    else:
        # Interactive prompt
        default_name = Path.cwd().name
        project_name = simple_input("Project name", default_name)
    
    # 2. Git
    init_git = simple_confirm("Initialize git repository?", True)
    
    # 3. Metadata
    author = simple_input("Author name (optional)", "")
    description = simple_input("Description (optional)", "")
    
    # 4. Starter module domain selection
    print("\nSelect starter module domain:")
    print("  1. Generic (domain-agnostic template)")
    print("  2. Logistics (lg) - Supply chains, routing, networks")
    print("  3. Finance (fi) - Risk, portfolios, trading")
    print("  4. Healthcare (hc) - Treatment, diagnosis, outcomes")
    print("  5. Manufacturing (mf) - Production, quality, scheduling")
    print("  6. Energy (en) - Grid optimization, forecasting")

    choice = simple_input("Choose (number)", "1").strip()

    domain_map = {
        '1': ('generic', 'default'),
        '2': ('logistics', 'logistics'),
        '3': ('finance', 'finance'),
        '4': ('healthcare', 'healthcare'),
        '5': ('manufacturing', 'manufacturing'),
        '6': ('energy', 'energy'),
    }

    template, starter_module = domain_map.get(choice, ('generic', 'default'))    
    # 5. Include examples
    include_examples = simple_confirm("Include example modules?", False) 
    
    # Create the project
    print(f"\nCreating project '{project_name}'...")
    
    success = create_project_structure(
        project_name=project_name,
        init_git=init_git,
        author=author or "Unknown",
        description=description or "",
        starter_module=starter_module,
        template=template,
        include_examples=include_examples 
    )
    
    if success:
        print(f"\n✓ Created {project_name}/")
        
        # Show next steps
        print(f"\nNext steps:")
        print(f"  cd {project_name}")
        print(f"  dp populate {starter_module}")
        print(f"  dp run {starter_module}")
        print(f"\nAdd more modules:")
        print(f"  dp add <module_name>")
        
        return 0
    else:
        return 1


def main():
    """Entry point for standalone execution"""
    return cmd_init()


if __name__ == "__main__":
    sys.exit(main())