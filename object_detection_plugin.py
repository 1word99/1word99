import logging
import numpy as np
from PIL import Image
from typing import Dict, List, Optional, Union

from osmanli_ai.plugins.base import BasePlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class ObjectDetectionPlugin(BasePlugin):
    """Advanced object detection with multiple model backends"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.model = None
        self.labels = []
        self._initialized = False

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="ObjectDetection",
            version="2.1.0",
            author="Osmanli AI",
            description="Advanced object detection with multiple model support",
            plugin_type=PluginType.VISION,
            capabilities=[
                "object_detection",
                "real_time_processing",
                "batch_processing",
                "gpu_acceleration",
            ],
            dependencies=["numpy", "Pillow", "ultralytics"],
            config_schema={
                "model_type": {
                    "type": "str",
                    "options": ["yolov8", "tensorrt", "onnx"],
                },
                "model_path": {"type": "str"},
                "confidence_threshold": {"type": "float", "min": 0, "max": 1},
                "device": {"type": "str", "options": ["auto", "cuda", "cpu"]},
            },
        )

    def initialize(self) -> None:
        """Initialize the detection model"""
        try:
            model_type = self.config.get("model_type", "yolov8")

            if model_type == "yolov8":
                from ultralytics import YOLO

                self.model = YOLO(self.config.get("model_path", "yolov8n.pt"))
                self.labels = self.model.names
            elif model_type == "tensorrt":
                # TensorRT implementation
                pass
            elif model_type == "onnx":
                # ONNX runtime implementation
                pass

            self._initialized = True
            logger.info(
                f"Initialized {model_type} model with {len(self.labels)} classes"
            )

        except ImportError as e:
            logger.error(f"Required dependencies not installed: {e}")
            raise
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            raise

    def detect(
        self,
        image: Union[np.ndarray, Image.Image, str],
        confidence: Optional[float] = None,
    ) -> List[Dict]:
        """
        Detect objects in an image.

        Args:
            image: Can be numpy array, PIL Image, or file path
            confidence: Optional confidence threshold override

        Returns:
            List of detected objects with:
            - label: str
            - confidence: float
            - box: [x1, y1, x2, y2]
            - class_id: int
        """
        if not self._initialized:
            raise RuntimeError("Plugin not initialized")

        conf_threshold = confidence or self.config.get("confidence_threshold", 0.5)

        try:
            # Convert input to consistent format
            if isinstance(image, str):
                img = Image.open(image)
            elif isinstance(image, Image.Image):
                img = image
            else:
                img = Image.fromarray(image)

            # Run detection
            results = self.model(img, conf=conf_threshold)

            return [
                {
                    "label": self.labels[int(box.cls)],
                    "confidence": float(box.conf),
                    "box": box.xyxy[0].tolist(),
                    "class_id": int(box.cls),
                }
                for box in results[0].boxes
            ]

        except Exception as e:
            logger.error(f"Detection failed: {e}")
            raise

    def batch_detect(
        self,
        images: List[Union[np.ndarray, Image.Image, str]],
        confidence: Optional[float] = None,
    ) -> List[List[Dict]]:
        """Process multiple images efficiently"""
        return [self.detect(img, confidence) for img in images]
