#!/usr/bin/env python3
"""
Quran Data Ingestion Module

This script processes Quran verse data from CSV files and converts it into a structured JSON format.
Each verse includes Arabic text, translations, transliterations, and audio URLs.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# Placeholder for actual data ingestion logic
# This file would typically handle reading raw Quran data (e.g., CSV, JSON)
# and processing it into a format suitable for the knowledge base.

# Example: If using a custom JSON parser
# import json


class QuranDataIngestor:
    def __init__(self, data_source_path: Path, knowledge_base_path: Path):
        self.data_source_path = data_source_path
        self.knowledge_base_path = knowledge_base_path

    def ingest_data(self):
        """Reads raw Quran data and processes it into the knowledge base."""
        print(
            f"Ingesting data from {self.data_source_path} to {self.knowledge_base_path}"
        )

        # Placeholder for actual data ingestion logic
        # Example: Reading a CSV file and converting to a simple JSON format
        try:
            # Assuming data_source_path points to a directory with CSVs like dataset/archive/
            # and each CSV is a chapter or part of the Quran.
            all_data = []
            for csv_file in self.data_source_path.glob("*.csv"):
                print(f"Processing {csv_file.name}...")
                df = pd.read_csv(csv_file)
                # Assuming the CSV has columns like 'verse_number', 'text', 'translation'
                # Convert DataFrame to list of dictionaries
                all_data.extend(df.to_dict(orient="records"))

            # Save to a single JSON knowledge base file
            with open(self.knowledge_base_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print(
                f"Successfully ingested {len(all_data)} records into {self.knowledge_base_path}"
            )

        except Exception as e:
            print(f"Error during data ingestion: {e}")


# Example usage (can be run directly for testing or called from main.py)
if __name__ == "__main__":
    # Adjust these paths as per your project structure
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent  # Adjust based on actual project root

    quran_data_source = project_root / "dataset" / "archive"
    quran_knowledge_base_file = project_root / "knowledge_base.json"

    ingestor = QuranDataIngestor(quran_data_source, quran_knowledge_base_file)
    ingestor.ingest_data()

    # Example of how to load and use the knowledge base
    with open(quran_knowledge_base_file, "r", encoding="utf-8") as f:
        knowledge_base_data = json.load(f)
    print(f"Loaded {len(knowledge_base_data)} records from knowledge base.")
    # You can now query or process knowledge_base_data
    # For example, find a specific verse:
    # verse_1_1 = [record for record in knowledge_base_data if record.get('chapter') == 1 and record.get('verse_number') == 1]
    # print(verse_1_1)


# Constants
RECITER_BASE_URL = "https://everyayah.com/data/AbdulSamad_64kbps_QuranExplorer.Com/"
MIN_CHAPTER = 1
MAX_CHAPTER = 114
CSV_FILE_PATTERN = "{chapter_num}.csv"


class QuranDataIngester:
    """Handles the ingestion and transformation of Quran data from CSV to JSON format."""

    def __init__(self, csv_dir: str, output_json_path: str):
        """
        Initialize the ingester with paths.

        Args:
            csv_dir: Directory containing chapter CSV files
            output_json_path: Path for the output JSON file
        """
        self.csv_dir = Path(csv_dir)
        self.output_json_path = Path(output_json_path)
        self.quran_data: List[Dict] = []

    def _process_verse(self, row: pd.Series, chapter_num: int) -> Optional[Dict]:
        """
        Process a single verse row from the CSV.

        Args:
            row: Pandas Series representing a verse
            chapter_num: Current chapter number

        Returns:
            Dictionary with processed verse data or None if invalid
        """
        try:
            verses_str = row["verses"]
            verse_dict = json.loads(verses_str.replace("'", '"'))

            full_verse_id = str(verse_dict["id"])
            verse_num = int(full_verse_id.split(".", maxsplit=1)[0])

            # Format audio URL components
            formatted_chapter = f"{chapter_num:03d}"
            formatted_verse = f"{verse_num:03d}"
            audio_url = f"{RECITER_BASE_URL}{formatted_chapter}{formatted_verse}.mp3"

            return {
                "chapter_id": chapter_num,
                "surah_name": row["surah_name"],
                "surah_name_ar": row["surah_name_ar"],
                "translation_name": row["translation"],
                "type": row["type"],
                "total_verses": row["total_verses"],
                "description": row["description"],
                "full_verse_id": full_verse_id,
                "verse_number_in_chapter": verse_num,
                "content_ar": verse_dict["content"],
                "translation_eng": verse_dict["translation_eng"],
                "transliteration": verse_dict["transliteration"],
                "audio_url": audio_url,
            }

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error processing verse: {e}")
            return None

    def _process_chapter(self, chapter_num: int) -> None:
        """Process all verses in a single chapter."""
        csv_path = self.csv_dir / CSV_FILE_PATTERN.format(chapter_num=chapter_num)

        if not csv_path.exists():
            print(f"Warning: {csv_path} not found. Skipping.")
            return

        try:
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                verse_data = self._process_verse(row, chapter_num)
                if verse_data:
                    self.quran_data.append(verse_data)

        except pd.errors.EmptyDataError:
            print(f"Error: {csv_path} is empty or corrupt.")
        except Exception as e:
            print(f"Unexpected error processing {csv_path}: {e}")

    def ingest(self) -> None:
        """Main method to process all chapters and save output."""
        print(f"Starting Quran data ingestion from {self.csv_dir}")

        for chapter_num in range(MIN_CHAPTER, MAX_CHAPTER + 1):
            self._process_chapter(chapter_num)

        self._save_output()
        print(f"Successfully saved Quran data to {self.output_json_path}")

    def _save_output(self) -> None:
        """Save the processed data to JSON file."""
        with open(self.output_json_path, "w", encoding="utf-8") as f:
            json.dump(self.quran_data, f, ensure_ascii=False, indent=4)


def main() -> None:
    """Main entry point for the script."""
    csv_directory = "/home/desktop/Desktop/box/curtain/dataset/archive"
    output_json_file = "/home/desktop/Desktop/box/curtain/quran_data.json"

    ingester = QuranDataIngester(csv_directory, output_json_file)
    ingester.ingest()


if __name__ == "__main__":
    main()
