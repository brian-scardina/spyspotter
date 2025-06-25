#!/usr/bin/env python3
"""
SBOM (Software Bill of Materials) Generator for PixelTracker

Generates CycloneDX format SBOM during build process.
"""

import json
import sys
import subprocess
import pkg_resources
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
import uuid


def get_installed_packages() -> List[Dict[str, Any]]:
    """Get list of installed packages with versions"""
    packages = []
    
    try:
        # Get installed packages
        installed = [d for d in pkg_resources.working_set]
        
        for package in installed:
            packages.append({
                'name': package.project_name,
                'version': package.version,
                'location': package.location
            })
    except Exception as e:
        print(f"Warning: Could not get installed packages: {e}")
    
    return packages


def get_git_info() -> Dict[str, Any]:
    """Get git repository information"""
    git_info = {}
    
    try:
        # Get current commit hash
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        git_info['commit'] = result.stdout.strip()
        
        # Get branch name
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        git_info['branch'] = result.stdout.strip()
        
        # Get remote URL
        result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], 
                              capture_output=True, text=True, check=True)
        git_info['url'] = result.stdout.strip()
        
    except subprocess.CalledProcessError:
        print("Warning: Could not get git information")
    except FileNotFoundError:
        print("Warning: Git not found")
    
    return git_info


def calculate_file_hash(file_path: Path) -> Optional[str]:
    """Calculate SHA-256 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def get_project_files() -> List[Dict[str, Any]]:
    """Get project source files"""
    files = []
    project_root = Path(__file__).parent
    
    # Common source file extensions
    source_extensions = {'.py', '.yaml', '.yml', '.json', '.txt', '.md', '.cfg', '.ini'}
    
    for file_path in project_root.rglob('*'):
        if (file_path.is_file() and 
            file_path.suffix in source_extensions and
            not any(part.startswith('.') for part in file_path.parts) and
            '__pycache__' not in str(file_path)):
            
            relative_path = file_path.relative_to(project_root)
            file_hash = calculate_file_hash(file_path)
            
            files.append({
                'path': str(relative_path),
                'size': file_path.stat().st_size,
                'hash': file_hash
            })
    
    return files


def generate_cyclone_dx_sbom() -> Dict[str, Any]:
    """Generate CycloneDX format SBOM"""
    
    # Get project information
    packages = get_installed_packages()
    git_info = get_git_info()
    project_files = get_project_files()
    
    # Generate unique BOM serial number
    bom_serial = f"urn:uuid:{uuid.uuid4()}"
    
    # Create CycloneDX SBOM structure
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "serialNumber": bom_serial,
        "version": 1,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "tools": [
                {
                    "vendor": "PixelTracker",
                    "name": "SBOM Generator",
                    "version": "1.0.0"
                }
            ],
            "component": {
                "type": "application",
                "bom-ref": "pixeltracker",
                "name": "PixelTracker",
                "version": git_info.get('commit', 'unknown')[:8],
                "description": "Advanced tracking pixel detection and privacy analysis tool",
                "licenses": [
                    {
                        "license": {
                            "name": "MIT"
                        }
                    }
                ],
                "properties": [
                    {
                        "name": "git:commit",
                        "value": git_info.get('commit', 'unknown')
                    },
                    {
                        "name": "git:branch", 
                        "value": git_info.get('branch', 'unknown')
                    },
                    {
                        "name": "git:url",
                        "value": git_info.get('url', 'unknown')
                    }
                ]
            }
        },
        "components": []
    }
    
    # Add Python dependencies as components
    for package in packages:
        component = {
            "type": "library",
            "bom-ref": f"pkg:pypi/{package['name']}@{package['version']}",
            "name": package['name'],
            "version": package['version'],
            "purl": f"pkg:pypi/{package['name']}@{package['version']}",
            "scope": "required"
        }
        sbom["components"].append(component)
    
    # Add source files information
    if project_files:
        sbom["metadata"]["component"]["hashes"] = []
        for file_info in project_files[:10]:  # Limit to first 10 files
            if file_info['hash']:
                sbom["metadata"]["component"]["hashes"].append({
                    "alg": "SHA-256",
                    "content": file_info['hash']
                })
    
    return sbom


def save_sbom(sbom: Dict[str, Any], output_file: str = "sbom.json") -> None:
    """Save SBOM to file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(sbom, f, indent=2)
        print(f"✅ SBOM saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving SBOM: {e}")
        sys.exit(1)


def validate_sbom(sbom: Dict[str, Any]) -> bool:
    """Basic validation of SBOM structure"""
    required_fields = ['bomFormat', 'specVersion', 'serialNumber', 'metadata']
    
    for field in required_fields:
        if field not in sbom:
            print(f"❌ Missing required field: {field}")
            return False
    
    if sbom['bomFormat'] != 'CycloneDX':
        print("❌ Invalid bomFormat")
        return False
    
    if 'component' not in sbom['metadata']:
        print("❌ Missing metadata component")
        return False
    
    print("✅ SBOM structure is valid")
    return True


def main():
    """Main function to generate SBOM"""
    print("🔨 Generating SBOM (Software Bill of Materials)...")
    
    # Generate SBOM
    sbom = generate_cyclone_dx_sbom()
    
    # Validate SBOM
    if not validate_sbom(sbom):
        sys.exit(1)
    
    # Print summary
    component_count = len(sbom.get('components', []))
    print(f"📦 Found {component_count} components")
    
    if 'metadata' in sbom and 'component' in sbom['metadata']:
        main_component = sbom['metadata']['component']
        print(f"🎯 Main component: {main_component.get('name', 'Unknown')}")
        print(f"📝 Version: {main_component.get('version', 'Unknown')}")
    
    # Save SBOM
    output_file = sys.argv[1] if len(sys.argv) > 1 else "sbom.json"
    save_sbom(sbom, output_file)
    
    # Print SBOM info
    print(f"🆔 BOM Serial: {sbom['serialNumber']}")
    print(f"📅 Generated: {sbom['metadata']['timestamp']}")


if __name__ == '__main__':
    main()
