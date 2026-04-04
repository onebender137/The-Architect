import ast
import os
import json
import argparse

class GraphAnalyzer:
    """Analyzes Python codebases to build a dependency and call graph."""

    def __init__(self, root_dir="."):
        self.root_dir = root_dir
        self.graph = {
            "files": {},
            "dependencies": [],
            "calls": []
        }

    def scan(self):
        """Scans the project directory for Python files."""
        ignore_list = {".git", "__pycache__", "venv", "chroma_db", ".venv"}
        for root, dirs, files in os.walk(self.root_dir):
            # Prune directories in place to avoid unnecessary traversal
            dirs[:] = [d for d in dirs if d not in ignore_list]

            for f in files:
                if f.endswith(".py"):
                    filepath = os.path.join(root, f)
                    self._analyze_file(filepath)
        return self.graph

    def _analyze_file(self, filepath):
        """Parses a single file to extract imports and function definitions."""
        rel_path = os.path.relpath(filepath, self.root_dir)
        self.graph["files"][rel_path] = {
            "imports": [],
            "definitions": []
        }

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        self.graph["files"][rel_path]["imports"].append(alias.name)
                        self.graph["dependencies"].append({
                            "from": rel_path,
                            "to": alias.name
                        })
                elif isinstance(node, ast.FunctionDef):
                    self.graph["files"][rel_path]["definitions"].append(node.name)
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")

    def save(self, output_file="dependency_graph.json"):
        """Saves the graph to a JSON file."""
        with open(output_file, "w") as f:
            json.dump(self.graph, f, indent=2)
        print(f"✅ Graph saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Architect Graph Analyzer")
    parser.add_argument("--root", default=".", help="Project root directory")
    parser.add_argument("--out", default="dependency_graph.json", help="Output JSON file")
    args = parser.parse_args()

    analyzer = GraphAnalyzer(args.root)
    analyzer.scan()
    analyzer.save(args.out)
