import json
import subprocess

# You may need to import these if not already present at the top of your file
import chromadb
from loguru import logger
from sentence_transformers import SentenceTransformer

from osmanli_ai.core.exceptions import QuranKnowledgeBaseError


class QuranKnowledgeBase:
    """Manages the loading, organization, and retrieval of Quranic data."""

    def __init__(
        self,
        config: dict,
    ):
        """Initializes the QuranKnowledgeBase.

        Args:
            config (dict): The configuration dictionary.
        """
        quran_config = config.get("modules", {}).get("quran", {})
        json_path = quran_config.get("quran_data_path", "data/quran_data.json")
        self.audio_base_url = quran_config.get(
            "audio_base_url", "http://www.everyayah.com/data/Alafasy_128kbps/"
        )  # Default base URL
        self.audio_url_format = quran_config.get(
            "audio_url_format", "{base_url}{chapter:03d}{verse:03d}.mp3"
        )  # New config parameter
        self.data = self._load_data(json_path)
        self.chapters = self._organize_chapters()
        self.mpv_process = None  # To store the mpv subprocess

        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(
            name="quran_verses"
        )
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        # self._ingest_data_to_chroma()

    def _load_data(self, json_path: str) -> list:
        """Loads Quranic data from a JSON file."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise QuranKnowledgeBaseError(
                f"Quran data file not found at {json_path}: {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise QuranKnowledgeBaseError(
                f"Error decoding Quran data JSON from {json_path}: {e}"
            ) from e
        except Exception as e:
            raise QuranKnowledgeBaseError(
                f"Error loading Quran data from {json_path}: {e}"
            ) from e

    def _organize_chapters(self) -> dict:
        """Organizes the loaded data into a chapter-based structure."""
        chapters = {}
        if self.data:
            for verse in self.data:
                chapter_id = verse["chapter_id"]
                if chapter_id not in chapters:
                    chapters[chapter_id] = {
                        "surah_name": verse["surah_name"],
                        "surah_name_ar": verse["surah_name_ar"],
                        "translation_name": verse["translation_name"],
                        "type": verse["type"],
                        "total_verses": verse["total_verses"],
                        "description": verse["description"],
                        "verses": [],
                    }
                chapters[chapter_id]["verses"].append(verse)
        return chapters

    def ingest_data(self):
        """Public method to trigger data ingestion with a progress bar."""
        from rich.progress import Progress

        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Ingesting Quranic Data...[/]", total=len(self.data)
            )
            self._ingest_data_to_chroma(progress, task)

    def _ingest_data_to_chroma(self, progress, task):
        """Ingests Quranic data into ChromaDB for semantic search."""
        try:
            if self.collection.count() == 0:  # Only ingest if collection is empty
                documents = []
                metadatas = []
                ids = []
                for verse in self.data:
                    document = f"Chapter {verse['chapter_id']}, Verse {verse['verse_number_in_chapter']}: {verse['translation_eng']}"
                    documents.append(document)
                    metadatas.append(
                        {
                            "chapter_id": verse["chapter_id"],
                            "verse_number_in_chapter": verse["verse_number_in_chapter"],
                            "surah_name": verse["surah_name"],
                            "translation_eng": verse["translation_eng"],
                        }
                    )
                    ids.append(
                        f"verse_{verse['chapter_id']}_{verse['verse_number_in_chapter']}"
                    )
                    progress.update(task, advance=1)

                # Generate embeddings and ingest in batches
                BATCH_SIZE = 5000  # Define a suitable batch size
                for i in range(0, len(documents), BATCH_SIZE):
                    batch_documents = documents[i : i + BATCH_SIZE]
                    batch_metadatas = metadatas[i : i + BATCH_SIZE]
                    batch_ids = ids[i : i + BATCH_SIZE]

                    batch_embeddings = self.embedding_model.encode(
                        batch_documents
                    ).tolist()

                    self.collection.add(
                        embeddings=batch_embeddings,
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                    )
                    logger.info(f"Ingested batch {i // BATCH_SIZE + 1} into ChromaDB.")
                logger.info("Quranic data ingested into ChromaDB.")
            else:
                logger.info(
                    "ChromaDB collection already populated. Skipping ingestion."
                )
        except Exception as e:
            raise QuranKnowledgeBaseError(
                f"Error ingesting data to ChromaDB: {e}"
            ) from e

    def get_chapter_info(self, chapter_number: int) -> dict | None:
        """Retrieves information about a specific Quran chapter."""
        return self.chapters.get(chapter_number)

    def get_verse(self, chapter_number: int, verse_number: int) -> dict | None:
        """Retrieves a specific verse from a given chapter."""
        chapter = self.chapters.get(chapter_number)
        if chapter:
            for verse in chapter["verses"]:
                if verse["verse_number_in_chapter"] == verse_number:
                    return verse
        return None

    def search_quran(self, keyword: str, n_results: int = 5) -> list[dict]:
        """Searches the Quranic data for a given keyword using semantic search."""
        try:
            query_embedding = self.embedding_model.encode([keyword]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["metadatas", "documents"],
            )

            formatted_results = []
            if results and results["metadatas"]:
                for i in range(len(results["metadatas"][0])):
                    metadata = results["metadatas"][0][i]
                    document = results["documents"][0][i]
                    formatted_results.append(
                        {
                            "chapter_id": metadata["chapter_id"],
                            "verse_id": metadata[
                                "verse_number_in_chapter"
                            ],  # Use verse_id for consistency with existing code
                            "surah_name": metadata["surah_name"],
                            "translation_eng": metadata["translation_eng"],
                            "document": document,  # Include the full document for context
                        }
                    )
            return formatted_results
        except Exception as e:
            raise QuranKnowledgeBaseError(f"Error searching Quran: {e}") from e

    def _play_audio_with_mpv(self, audio_urls: list[str]) -> str:
        """Plays audio using the mpv player via a subprocess.

        Args:
            audio_urls (list[str]): A list of URLs of the audio files to play.

        Returns:
            str: A message indicating the status of the audio playback.
        """
        if self.mpv_process and self.mpv_process.poll() is None:
            self.mpv_process.terminate()
            self.mpv_process.wait()

        try:
            # mpv command-line arguments for background playback and IPC control
            command = [
                "mpv",
                "--no-video",  # Do not open a video window
                "--no-terminal",  # Do not take over the terminal
                "--input-ipc-server=/tmp/mpvsocket",  # Enable IPC for control (e.g., pause/resume)
                "--idle",  # Keep mpv running after playback finishes
            ]
            command.extend(audio_urls)  # Add all audio URLs to the command
            logger.debug(f"Attempting to play audio with mpv. URLs: {audio_urls}")

            self.mpv_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info(f"Started mpv process for {len(audio_urls)} URLs.")
            return "Audio playback started."
        except FileNotFoundError:
            logger.error("mpv not found. Please install mpv to enable audio playback.")
            raise QuranKnowledgeBaseError(
                "mpv not found. Please install mpv to enable audio playback."
            )
        except Exception as e:
            logger.error(f"Error starting mpv process: {e}")
            raise QuranKnowledgeBaseError(f"Error starting audio playback: {e}") from e

    def pause_audio(self) -> str:
        """Pauses the currently playing audio."""
        if self.mpv_process and self.mpv_process.poll() is None:
            try:
                # Send 'cycle pause' command to mpv via IPC
                subprocess.run(
                    [
                        "echo",
                        '{ "command": ["cycle", "pause"] }',
                        "|",
                        "socat",
                        "-",
                        "UNIX-CONNECT:/tmp/mpvsocket",
                    ],
                    shell=True,
                    check=True,
                )
                return "Audio paused."
            except FileNotFoundError:
                raise QuranKnowledgeBaseError(
                    "socat not found. Please install socat to enable audio control (pause/resume/stop)."
                )
            except Exception as e:
                logger.error(f"Error pausing audio: {e}")
                raise QuranKnowledgeBaseError(f"Error pausing audio: {e}") from e
        return "No audio playing to pause."

    def resume_audio(self) -> str:
        """Resumes the paused audio."""
        if self.mpv_process and self.mpv_process.poll() is None:
            try:
                # Send 'set pause no' command to mpv via IPC
                subprocess.run(
                    [
                        "echo",
                        '{ "command": ["set", "pause", "no"] }',
                        "|",
                        "socat",
                        "-",
                        "UNIX-CONNECT:/tmp/mpvsocket",
                    ],
                    shell=True,
                    check=True,
                )
                return "Audio resumed."
            except FileNotFoundError:
                raise QuranKnowledgeBaseError(
                    "socat not found. Please install socat to enable audio control (pause/resume/stop)."
                )
            except Exception as e:
                logger.error(f"Error resuming audio: {e}")
                raise QuranKnowledgeBaseError(f"Error resuming audio: {e}") from e
        return "No audio playing to resume."

    def stop_audio(self) -> str:
        """Stops the currently playing audio."""
        if self.mpv_process and self.mpv_process.poll() is None:
            try:
                self.mpv_process.terminate()
                self.mpv_process.wait()
                self.mpv_process = None
                return "Audio stopped."
            except FileNotFoundError:
                raise QuranKnowledgeBaseError(
                    "socat not found. Please install socat to enable audio control (pause/resume/stop)."
                )
            except Exception as e:
                logger.error(f"Error stopping audio: {e}")
                raise QuranKnowledgeBaseError(f"Error stopping audio: {e}") from e
        return "No audio playing to stop."

    def play_verses_audio(self, verses: list[tuple[int, int]]) -> str:
        """Plays audio for a list of verses."""
        audio_urls = []
        for chapter_number, verse_number in verses:
            audio_url = self.audio_url_format.format(
                base_url=self.audio_base_url, chapter=chapter_number, verse=verse_number
            )
            audio_urls.append(audio_url)
        return self._play_audio_with_mpv(audio_urls)

    def play_verse_audio(self, chapter_number: int, verse_number: int) -> str:
        """Plays audio for a single verse."""
        return self.play_verses_audio([(chapter_number, verse_number)])

    def self_test(self) -> bool:
        """Performs a self-test of the QuranKnowledgeBase component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for QuranKnowledgeBase...")
        try:
            if not self.data:
                logger.error("QuranKnowledgeBase self-test failed: No data loaded.")
                return False
            if not self.chapters:
                logger.error(
                    "QuranKnowledgeBase self-test failed: Chapters not organized."
                )
                return False
            if self.collection.count() == 0:
                logger.warning(
                    "QuranKnowledgeBase self-test: ChromaDB collection is empty. Data ingestion might be needed."
                )

            # Test get_chapter_info
            chapter_info = self.get_chapter_info(1)
            if not chapter_info or chapter_info["surah_name"] != "AL-FATIHA":
                logger.error(
                    "QuranKnowledgeBase self-test failed: get_chapter_info failed."
                )
                return False

            # Test get_verse
            verse = self.get_verse(1, 1)
            if not verse or verse["translation_eng"] == "":
                logger.error("QuranKnowledgeBase self-test failed: get_verse failed.")
                return False

            logger.info("QuranKnowledgeBase self-test passed.")
            return True
        except Exception as e:
            logger.error(f"QuranKnowledgeBase self-test failed: {e}")
            raise QuranKnowledgeBaseError(
                f"QuranKnowledgeBase self-test failed: {e}"
            ) from e
