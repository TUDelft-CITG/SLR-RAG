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

import regex as re
import sys
from pathlib import Path

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
    "bridge": ["bridge", "bridges"],
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
    # === 4. NAUTICAL & NAVIGATION ===
    "nautical": ["nautical", "maritime", "navigation", "navigational", "navigate"],
    # === 5. RISK ASSESSMENT ===
    "safety": ["safety", "safe"],
    "risk": ["risk", "risks", "risky"],
    "probability": [
        "probability",
        "probabilities",
        "probable",
        "probably",
        "probabilistic",
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

    # Clean up any existing highlights
    content = cleanup_file(content)

    modified = False
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

        new_content = re.sub(
            pattern,
            rf'<span class="{class_name}">\1</span>',
            content,
            flags=re.IGNORECASE,
        )

        if new_content != content:
            content = new_content
            modified = True

    if modified:
        # Add marker at the top
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
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
