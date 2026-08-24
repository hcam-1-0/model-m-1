# Primary Research References

Accessed 2026-08-24. These sources inform candidate evaluation. The role-based
portfolio is selected for planning, but listing or selecting a candidate does
not approve an artifact or prove H-CAM compatibility.

## Detection, Tracking, And OCR

- [YOLOX official repository](https://github.com/Megvii-BaseDetection/YOLOX)
  documents the Apache-2.0 source repository, Tiny/Nano variants, and ONNX,
  TensorRT, ncnn, and OpenVINO deployment material. Implication: use
  YOLOX-Tiny as the stable portable reference, subject to exact weight review.
- [D-FINE official repository](https://github.com/Peterande/D-FINE) documents
  Nano through X model tiers and ONNX Runtime/TensorRT export and inference.
  Implication: use D-FINE-N as the compact modern challenger, not as an assumed
  edge winner.
- [RF-DETR official repository](https://github.com/roboflow/rf-detr) documents
  Apache-designated Nano through Large detection tiers, separate PML-licensed
  Plus tiers, fine-tuning, and upstream COCO/RF100-VL benchmarks. Implication:
  evaluate Small as the balanced candidate and Large as the accuracy candidate;
  exclude XL/2XL from this portfolio.
- [RT-DETRv4 official repository](https://github.com/RT-DETRs/RT-DETRv4)
  documents an Apache-2.0 source repository, 2026 release, ONNX/TensorRT tools,
  and a DINOv3 teacher in the training path. Implication: retain it as a future
  challenger until maturity and the complete teacher/weight lineage are
  reviewed.
- [Ultralytics licensing](https://www.ultralytics.com/license) states that its
  YOLO code/models use AGPL-3.0 by default and that private/proprietary use
  requires an Enterprise license under its terms. Implication: YOLO26 is not a
  default H-CAM candidate without a separate license decision.
- [ByteTrack official repository](https://github.com/FoundationVision/ByteTrack)
  documents the MIT-licensed detector-association tracker and established MOT
  results. Implication: use it only for anonymous, stream-local tracks.
- [PP-OCRv6 official documentation](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html)
  documents tiny/small/medium tiers, current supported-language scope, and
  ONNX Runtime/OpenVINO measurements. Implication: evaluate small/medium for
  supported Latin text; do not infer Gujarati or Devanagari coverage.
- [PaddleOCR text-recognition catalog](https://www.paddleocr.ai/main/en/version3.x/module_usage/text_recognition.html)
  explicitly lists `devanagari_PP-OCRv5_mobile_rec` for Devanagari letters and
  numbers. Implication: keep it as the script-specific Devanagari candidate.
- [Tesseract language reference](https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc),
  [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast), and
  [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) document
  official `guj` data and the speed/accuracy tiers. Implication: compare fast
  and best as separate Gujarati candidates.

Repository licensing, checkpoint licensing, backbone/teacher licensing,
training-data terms, and redistribution rights remain separate evidence. All
published accuracy and latency values are upstream results, not H-CAM results.

## Video And Inference Runtimes

- [NVIDIA DeepStream SDK Developer Guide](https://docs.nvidia.com/metropolis/deepstream/dev-guide/index.html)
  identifies DeepStream 9.0 as the current documented release and describes the
  NVIDIA intelligent-video analytics platform. Implication: evaluate it for an
  NVIDIA-specific accelerated pipeline, not as the H-CAM domain contract.
- [NVIDIA Triton Inference Server](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html)
  documents multiple backends, model repositories, concurrent execution,
  scheduling, health, and metrics. [Triton batching](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/batcher.html)
  explains the latency/throughput tradeoff of dynamic batching. Implication:
  benchmark stateless detector batching while keeping stream-local state and
  maximum queue age explicit.
- [ONNX Runtime Execution Providers](https://onnxruntime.ai/docs/execution-providers/)
  documents hardware abstraction across CPU, CUDA/TensorRT, OpenVINO, and other
  providers. [ONNX Runtime quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)
  warns that gains depend on model and hardware and can regress performance.
  Implication: use a portable reference candidate and validate each provider and
  precision separately.
- [OpenVINO 2026 supported devices](https://docs.openvino.ai/2026/documentation/compatibility-and-support/supported-devices.html)
  documents CPU, GPU, NPU, AUTO, HETERO, batching, and multi-stream support.
  [OpenVINO AUTO](https://docs.openvino.ai/2026/openvino-workflow/running-inference/inference-devices-and-modes/auto-device-selection.html)
  describes device selection and throughput hints. Implication: evaluate Intel
  edge hardware using a declared device list rather than relying on an opaque
  automatic choice in benchmark evidence.

## Model And Dataset Operations

- [MLflow Model Registry workflows](https://mlflow.org/docs/latest/ml/model-registry/workflow/)
  document immutable versions, aliases, and tags and note the move away from
  deprecated fixed stages. Implication: if selected, use environment-separated
  records and aliases while events retain immutable version IDs.
- [CVAT video format and interpolation](https://docs.cvat.ai/docs/manual/advanced/formats/format-cvat/)
  documents video tracks and interpolation; [CVAT MOT format](https://docs.cvat.ai/docs/manual/advanced/formats/format-mot/)
  documents track-oriented exports. Implication: CVAT is a viable annotation
  UI candidate, but H-CAM still owns the normalized schema and QA rules.

## Risk Governance

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
  is a voluntary framework for incorporating trustworthiness into AI design,
  development, use, and evaluation.
- [NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
  organizes work through Govern, Map, Measure, and Manage. Implication: use the
  functions to structure risk records and lifecycle evidence without claiming
  certification or treating the framework as a substitute for Indian legal and
  Gujarat Police policy review.

## Research Update Rule

Before implementation, recheck versions, licenses, supported operating systems,
hardware matrices, security advisories, model licenses, and formal Government
requirements. Documentation and product behavior can change after this access
date.
