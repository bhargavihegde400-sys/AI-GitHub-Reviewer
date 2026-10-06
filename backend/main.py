from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class RepoRequest(BaseModel):
    url: str


def review_code_with_ai(source_contents):
    code_text = "\n\n".join(
        f"FILE: {item["path"]}\n{item["content"]}"
        for item in source_contents
    )

    prompt = f"""You are a professional software code reviewer.

Review the following source files.

Return ONLY valid JSON. Do not write any explanation, markdown, or text before or after the JSON.

Use EXACTLY these keys:

{{
  "code_quality_score": 0,
  "code_quality": "",
  "issues": [],
  "suggestions": [],
  "design_patterns": "",
  "developer_skill": ""
}}


Rules:
- code_quality_score must be an integer from 0 to 100.
- code_quality must be one short paragraph.
- issues must contain 1 to 3 specific issues found in the code.
- suggestions must contain 1 to 3 specific improvements.
- design_patterns must identify patterns actually visible in the code, or "None identified".
- developer_skill must be "Junior", "Intermediate", or "Advanced", followed by one short reason.
- Return valid JSON only.
- Do not use markdown code fences.
- Do not add extra keys.
- Do not explain your reasoning.

SOURCE CODE:
{code_text[:4000]}
"""

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "qwen3:4b",
            "prompt": prompt,
            "stream": False,
"think": False,
"format": "json",
            "options": {
                "temperature": 0.2,
		"num_predict": 300
            }
        }
    )

    if response.status_code != 200:
        return "AI review failed"

    return clean_ai_response(response.json()["response"])

def generate_readme_with_ai(repo_name, description, language, 
technologies):
    prompt = f"""Create a professional GitHub README for this project.

Project name: {repo_name}
Description: {description}
Main language: {language}
Technologies: {", ".join(technologies)}

Include:
- Project title
- Short description
- Features
- Technologies used
- Installation steps
- Usage
- Future improvements

Return only the README content in Markdown.
Do not explain your answer.
"""

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "qwen3:4b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        }
    )

    if response.status_code != 200:
        return "README generation failed"

    return clean_ai_response(response.json()["response"])
def clean_ai_response(response):
    if "</think>" in response:
        response = response.split("</think>", 1)[1]
    return response.strip()


def fetch_source_files(owner, name, branch, source_files):
    source_contents = []

    for file_path in source_files:
        api_url = f"https://api.github.com/repos/{owner}/{name}/contents/{file_path}?ref={branch}"
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            encoded_content = data.get("content", "")

            if encoded_content:
                import base64
                content = base64.b64decode(encoded_content).decode("utf-8", errors="ignore")

                source_contents.append({
                    "path": file_path,
                    "content": content[:6000]
                })

    return source_contents


def select_source_files(files):
    source_extensions = (
        ".py", ".java", ".js", ".jsx", ".ts", ".tsx",
        ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
        ".rs", ".go", ".php", ".rb"
    )

    preferred = []
    other_source = []

    excluded_parts = (
        "documentation/",
        "docs/",
        "doc/",
        "test/",
        "tests/",
        "__tests__/",
        "node_modules/",
        "vendor/",
        "build/",
        "dist/"
    )

    preferred_parts = (
        "src/",
        "app/",
        "lib/",
        "backend/",
        "frontend/",
        "server/"
    )

    for file in files:
        lower_file = file.lower()

        if not lower_file.endswith(source_extensions):
            continue

        if any(part in lower_file for part in excluded_parts):
            continue

        if any(part in lower_file for part in preferred_parts):
            preferred.append(file)
        else:
            other_source.append(file)

    selected = preferred[:5]

    if len(selected) < 5:
        selected.extend(other_source[:5 - len(selected)])

    return selected


def home():
    return {"message": "AI GitHub Reviewer Backend is Running"}


@app.post("/analyze")
def analyze_repo(repo: RepoRequest):

    parts = repo.url.rstrip("/").split("/")

    if len(parts) < 2:
        return {"error": "Invalid GitHub URL"}

    owner = parts[-2]
    name = parts[-1]

    # Get repository information
    repo_url = f"https://api.github.com/repos/{owner}/{name}"
    response = requests.get(repo_url)

    if response.status_code != 200:
        return {"error": "GitHub repository not found"}

    data = response.json()

    # Get default branch
    branch = data["default_branch"]

    # Get repository file tree
    tree_url = (
        f"https://api.github.com/repos/{owner}/{name}"
        f"/git/trees/{branch}?recursive=1"
    )

    tree_response = requests.get(tree_url)

    files = []

    if tree_response.status_code == 200:
        tree_data = tree_response.json()

        files = [
            item["path"]
            for item in tree_data.get("tree", [])
            if item["type"] == "blob"
        ]

    # Technology Stack Detection
    technologies = []

    file_names = [file.lower() for file in files]

    # Configuration files
    if "package.json" in file_names:
        technologies.append("Node.js / JavaScript")

    if "requirements.txt" in file_names or "pyproject.toml" in file_names:
        technologies.append("Python")

    if "pom.xml" in file_names:
        technologies.append("Java / Maven")

    if "build.gradle" in file_names or "build.gradle.kts" in file_names:
        technologies.append("Java / Gradle")

    if "cargo.toml" in file_names:
        technologies.append("Rust")

    if "go.mod" in file_names:
        technologies.append("Go")

    if "composer.json" in file_names:
        technologies.append("PHP")

    if "gemfile" in file_names:
        technologies.append("Ruby")

    if "dockerfile" in file_names:
        technologies.append("Docker")

    if "androidmanifest.xml" in file_names:
        technologies.append("Android")

    # Source-code extensions
    if any(file.endswith(".py") for file in file_names):
        technologies.append("Python")

    if any(file.endswith(".java") for file in file_names):
        technologies.append("Java")

    if any(file.endswith((".js", ".jsx")) for file in file_names):
        technologies.append("JavaScript")

    if any(file.endswith((".ts", ".tsx")) for file in file_names):
        technologies.append("TypeScript")

    if any(file.endswith((".cpp", ".cc", ".cxx", ".hpp")) for file in file_names):
        technologies.append("C++")

    if any(file.endswith(".c") for file in file_names):
        technologies.append("C")

    if any(file.endswith(".rs") for file in file_names):
        technologies.append("Rust")

    if any(file.endswith(".go") for file in file_names):
        technologies.append("Go")

    if any(file.endswith(".php") for file in file_names):
        technologies.append("PHP")

    if any(file.endswith(".rb") for file in file_names):
        technologies.append("Ruby")

    # Remove duplicate technologies
    technologies = list(dict.fromkeys(technologies))

    # Add GitHub's detected language
    if data["language"] and data["language"] not in technologies:
        technologies.append(data["language"])

    # Select source files for later AI analysis
    source_files = select_source_files(files)
    source_contents = fetch_source_files(owner, name, branch, source_files)
    ai_review = review_code_with_ai(source_contents)

    # Get README
    readme_url = (
        f"https://api.github.com/repos/{owner}/{name}/readme"
    )

    readme_response = requests.get(
        readme_url,
        headers={"Accept": "application/vnd.github.raw+json"}
    )

    readme_preview = ""

    if readme_response.status_code == 200:
        readme_preview = readme_response.text[:2000]
    if readme_preview:
        readme_status = "README found"
    else:
        readme_status = "README missing"
    generated_readme = ""

    if not readme_preview:
        generated_readme = generate_readme_with_ai(
            data["name"],
            data["description"],
            data["language"],
            technologies
        )
    # Return analysis
    return {
        "name": data["name"],
        "description": data["description"],
        "language": data["language"],
        "technologies": technologies,
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "total_files": len(files),
        "important_files": files[:20],
        "source_files": source_files,
        "source_contents": source_contents,
        "readme_preview": readme_preview,
        "readme_status": readme_status,
        "generated_readme": generated_readme,
        "ai_review": ai_review,
        "url": data["html_url"]
    }
