from setuptools import setup, find_packages

setup(
    name="arxiv-harvester",
    version="0.1.0",
    description="Tool for extracting and processing academic papers from arXiv.org",
    author="AI Team",
    author_email="ai@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.28.2",
        "pypdf2>=3.0.1",
        "pandas>=2.0.1",
        "tqdm>=4.65.0",
        "python-dotenv>=1.0.0"
    ],
    python_requires=">=3.8",
)
