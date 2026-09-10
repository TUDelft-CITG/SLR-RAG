#!/usr/bin/env python3
"""
Batch apply keyword highlighting with stemming support.
Safety: checks if word is already in a kw- span before wrapping.

Dictionary format:
{
    "root_word": ["variant1", "variant2", ...]
}

All variants get the same class: kw-root_word

Usage: python highlight_keywords.py /path/to/your/notes/folder
"""

import sys
from pathlib import Path

import regex as re

# Stemming dictionary: {root_word: [all_variants]}
# Organized by topics:
# 1. Offshore Infrastructure
# 2. Maritime Vessels & Structures
# 3. Safety & Incidents
# 4. Nautical & Navigation
# 5. Risk Assessment
# 6. Analysis & Prediction
STEMMING_DICT = {
    # === 1. OFFSHORE INFRASTRUCTURE ===
    "offshore": ["offshore"],
    "infrastructure": ["infrastructure", "construction", "installation"],
    "wind-farm": [
        "windfarm",
        "windfarms",
        "wind farm",
        "wind farms",
        "windmill",
        "wind turbine",
        "wind park",
        "wind parks",
        "wind energy",
    ],
    "other-offshore-infrastructures": [
        "platform",
        "platforms",
        "quay",
        "quays",
        "wharf",
        "wharfs",
        "lidar",
        "lidars",
        "flotel",
        "flotels",
        "aquaculture farm",
        "aquaculture farms",
        "artificial island",
        "artificial islands",
        "synthetic island",
        "synthetic islands",
    ],
    "bridge": ["bridge", "bridges", "bridging"],
    "aquaculture": ["aquaculture"],
    # === 2. MARITIME VESSELS & STRUCTURES ===
    "ship": ["ship", "ships", "shipping", "shipped"],
    "vessel": ["vessel", "vessels"],
    # === 3. SAFETY & INCIDENTS ===
    "collision": [
        "collision",
        "collisions",
        "collide",
        "collided",
        "allision",
        "allisions",
        "allide",
        "allides",
    ],
    "accident": ["accident", "accidents"],
    "impact": ["impact", "impacts"],
    # === 4. NAUTICAL & NAVIGATION ===
    "nautical": ["nautical", "maritime", "navigation", "navigational", "navigate"],
    # === 5. RISK ASSESSMENT ===
    "safety": ["safety", "safe", "safer"],
    "risk": ["risk", "risks", "risky"],
    "probability": [
        "probability",
        "probabilities",
        "probable",
        "probably",
        "probabilistic",
    ],
    "frequency": [
        "frequency",
        "frequencies",
    ],
    "chance": ["chance", "chances", "likelihood", "likely", "unlikely"],
    "assess": ["assess", "assessment", "assessments", "assessing", "assessed"],
    "navigation-risk-assessment": [
        "navigation risk assessment",
        "navigational risk assessment",
        "navigation risk assessments",
        "navigational risk assessments",
    ],
    # === 6. ANALYSIS & PREDICTION ===
    "model": ["model", "models", "modelling", "modeling"],
    "predict": [
        "predict",
        "predicts",
        "predicted",
        "predicting",
        "prediction",
        "predictions",
        "predictive",
    ],
    "analyse": [
        "analyse",
        "analyses",
        "analysed",
        "analysing",
        "analysis",
        "analyze",
        "analyzed",
        "analyzing",
    ],
    "simulator": ["simulator", "simulate", "simulation"],
    # === 7. IRRELEVANT (for exclusion/filtering) ===
    "irrelevant": ["therapy", "therapies", "blood", "medicine", "medicines", "medical"],
}


def root_to_class(root):
    """Convert root word to CSS class name: 'wind-farm' -> 'kw-wind-farm'"""
    return f"kw-{root}"


def get_all_keyword_variants():
    """Get all keyword variants with their root class"""
    result = []
    for root, variants in STEMMING_DICT.items():
        class_name = root_to_class(root)
        for variant in variants:
            result.append({"variant": variant, "class_name": class_name, "root": root})
    return result


def highlight_keywords_in_text(text: str) -> str:
    """
    Apply keyword highlighting to a text string using the STEMMING_DICT.
    Only highlights whole words that are not already inside kw- spans.

    Args:
        text: The text to highlight

    Returns:
        The text with keywords wrapped in appropriate kw- class spans
    """
    if not text or not isinstance(text, str):
        return text

    all_variants = get_all_keyword_variants()

    # Sort by length (longest first) to avoid partial matches
    all_variants.sort(key=lambda x: len(x["variant"]), reverse=True)

    for item in all_variants:
        variant = item["variant"]
        class_name = item["class_name"]

        # Regex pattern: match whole word NOT already inside a kw- span
        # (?<!class="kw-[^"]*">[^<]*\b) = not preceded by kw- class
        # (?![^<]*</span>) = not followed by </span> (safety)
        pattern = (
            r'(?<!class="kw-[^"]*">[^<]*\b)(\b'
            + re.escape(variant)
            + r"\b)(?![^<]*</span>)"
        )

        new_text = re.sub(
            pattern, rf'<span class="{class_name}">\1</span>', text, flags=re.IGNORECASE
        )

        if new_text != text:
            text = new_text

    return text


def cleanup_file(content):
    """Remove all existing KW highlights and markers"""
    # Remove all kw- spans
    content = re.sub(
        r'<span class="kw-[^"]+">(.*?)</span>', r"\1", content, flags=re.DOTALL
    )

    # Clean up extra spaces
    content = re.sub(r" +", " ", content)
    content = re.sub(r"\n\n+", "\n\n", content)
    return content.strip()


def process_file(filepath):
    """Apply keyword highlighting to a single markdown file"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split content into header (between ---) and body
    # Check if there's a frontmatter header
    header = None
    body = content

    if content.strip().startswith("---"):
        # Find the closing ---
        second_dash_pos = content.find("---", 3)  # Start after first ---
        if second_dash_pos != -1:
            # Extract header (including the --- delimiters)
            header_end = second_dash_pos + 3
            header = content[:header_end]
            body = content[header_end:]

    # Clean up any existing highlights from body only (preserve leading/trailing whitespace)
    # We need to be careful not to strip the body if there's a header
    if header is not None:
        # Don't strip leading whitespace from body if there's a header
        # Remove only kw- spans from body
        body = re.sub(
            r'<span class="kw-[^"]+">(.*?)</span>', r"\1", body, flags=re.DOTALL
        )
        # Clean up extra spaces but preserve structure
        body = re.sub(r" +", " ", body)
        body = re.sub(r"\n\n+", "\n\n", body)
    else:
        body = cleanup_file(body)

    # Apply keyword highlighting to body only
    highlighted_body = highlight_keywords_in_text(body)

    # Recombine content
    if header is not None:
        highlighted_content = header + highlighted_body
    else:
        highlighted_content = highlighted_body

    if highlighted_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(highlighted_content)
        print(f"✓ Processed: {filepath}")
        return True

    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python highlight_keywords.py /path/to/folder")
        print("Example: python highlight_keywords.py ~/Documents/Obsidian/MyVault")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    if not folder_path.exists():
        print(f"Error: Folder not found: {folder_path}")
        sys.exit(1)

    # Find all markdown files
    md_files = list(folder_path.rglob("*.md"))

    if not md_files:
        print(f"No markdown files found in: {folder_path}")
        sys.exit(1)

    print(f"Found {len(md_files)} markdown files in {folder_path}")
    print(f"Stemming roots: {', '.join(STEMMING_DICT.keys())}")
    print(f"Total variants: {sum(len(v) for v in STEMMING_DICT.values())}")
    print("Processing...\n")

    processed_count = 0
    for md_file in md_files:
        if process_file(md_file):
            processed_count += 1

    print(f"\n✅ Done! Processed {processed_count} out of {len(md_files)} files")


if __name__ == "__main__":
    main()
