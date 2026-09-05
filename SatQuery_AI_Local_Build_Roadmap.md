# SatQuery AI — Complete Local Build Roadmap (RTX 5050, 8GB VRAM)

Goal: a fully working, fully local prototype for the internal round, built around Moondream2 instead of training anything. No cloud, no fine-tuning yet — this proves the architecture.

---

## 1. Final Architecture

```
                    ┌───────────────────────┐
                    │   Streamlit Frontend    │
                    │  (upload + query box)   │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   FastAPI Backend       │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Input Validator         │  checks: 1 image? optical+SAR pair?
                    │                          │  bi-temporal pair? format ok?
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  LangGraph Controller    │  classifies query intent,
                    │  (rule/keyword routing)  │  picks which tool(s) to call
                    └───────────┬─────────────┘
                                │
        ┌───────────┬──────────┼──────────────┬──────────────┐
        ▼           ▼          ▼               ▼              │
   VQA/Caption   Grounding   Change-Detect   Optical-SAR       │
   (Moondream2   (Moondream2 (OpenCV diff    Fusion (Moondream2│
   .query/       .detect)    + Moondream2    called twice,     │
   .caption)                 .query)         combined prompt)  │
        │           │          │               │                │
        └───────────┴──────────┴───────────────┴────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Output Combiner         │  text answer + bbox overlay
                    │                          │  + confidence + execution log
                    └───────────┬─────────────┘
                                │
                                ▼
                        Response to Frontend
```

**Key point**: Moondream2 is loaded **once** and reused across the VQA, grounding, and fusion tools — you're not juggling multiple large models in 8GB VRAM.

---

## 2. Datasets Used for Internal-Round Demo Samples

Not for training — just pulling a small number of sample images/pairs from each, since these are the datasets named directly by the problem statement:

| Dataset | Used for | Demo samples needed |
|---|---|---|
| **VRSBench** | Single-image VQA, captioning, grounding (has referring-expression/bbox annotations) | 3-4 sample images |
| **RSVQA** | Single-image VQA | 2-3 sample image+question pairs |
| **CDVQA** | Bi-temporal change detection | 1-2 before/after pairs |
| **BigEarthNet** (Sentinel-1 SAR + Sentinel-2 optical) | Optical–SAR fusion (co-registered pairs) | 1-2 optical+SAR pairs |

Total: roughly 6-10 sample images/pairs, pulled from each dataset's HuggingFace page — not the full dataset. This keeps every demo example traceable back to a dataset the problem statement actually names.

---

## 3. Tech Stack (Local-Only)

| Layer | Tech |
|---|---|
| VLM | **Moondream2 (4-bit)** — `moondream/moondream-2b-2025-04-14-4bit` via `transformers` |
| Change detection | **OpenCV** (`cv2.absdiff`, thresholding) — no GPU needed |
| Image I/O | `rasterio` (GeoTIFF/TIFF) + `Pillow` (PNG/JPEG for benchmark datasets) |
| Orchestration | **LangGraph** — rule-based routing to start |
| Backend | **FastAPI** |
| Frontend | **Streamlit** |
| Environment | Python venv, CUDA-enabled PyTorch matching your driver version |

Install:
```bash
pip install transformers pillow torchao einops opencv-python rasterio fastapi uvicorn streamlit langgraph
```

---

## 4. Build Phases

### Phase 1 — Environment + Model Sanity Check (Day 1)
- Set up venv, install CUDA-matched PyTorch
- Load Moondream2 4-bit, confirm it runs on your RTX 5050 without OOM
- Test `.query()`, `.caption()`, `.detect()` on 2-3 sample satellite images (download a few from BigEarthNet.txt, VRSBench, or even Google Earth screenshots for a quick smoke test)
- **Exit criteria**: model loads, responds to a basic query in under ~5 seconds

### Phase 2 — Core Single-Image Tools (Day 2)
- Wrap Moondream2 calls into clean functions: `answer_vqa(image, question)`, `caption_image(image)`, `detect_object(image, label)`
- Add domain-context system prompting (e.g. prefix queries with "This is a satellite/remote-sensing image.") to nudge outputs toward relevant terminology
- Test against representative queries from the problem statement ("Describe the land-cover...", "Highlight the water body...")

### Phase 3 — Change Detection Tool (Day 2-3)
- Build `detect_change(image_t1, image_t2)`:
  1. Align/resize both images to same dimensions
  2. `cv2.absdiff()` between them, threshold to get a change mask
  3. Pass the change mask + both original images to Moondream2 with a prompt like "These two images show the same location at different times. A change was detected in the highlighted region — describe what changed."
- Test on a before/after pair (can simulate with two crops of the same area, or download an actual CDVQA sample pair)

### Phase 4 — Optical–SAR "Fusion" Tool (Day 3)
- Build `fuse_optical_sar(optical_img, sar_img, query)`:
  - Call Moondream2 with a prompt explicitly framing both images: "Image A is optical imagery, Image B is SAR (radar) imagery of the same location. Using both together, answer: {query}"
  - Since Moondream2 handles one image at a time in some versions, you may need to run it twice (once per image) and combine both text outputs into a final synthesis prompt — test which approach gives more coherent output
- Test with a query like "Use both images to identify built-up and water regions"

### Phase 5 — Input Validator (Day 3-4)
- Build a function that inspects the upload(s) and classifies input type: single image / optical+SAR pair / bi-temporal pair
- Basic checks: file format (GeoTIFF/TIFF/PNG/JPEG), image dimensions match (for pairs), band count sanity check

### Phase 6 — LangGraph Controller (Day 4-5)
- Build the routing graph:
  - Parse query text for intent keywords: "changed"/"compare"/"over time" → change-detection tool; "highlight"/"where"/"locate" → grounding tool; "describe"/"what is" → captioning/VQA tool
  - Cross-reference with input type from the validator: if 2 images of different sensor types → fusion tool regardless of query keywords, if bi-temporal pair → change tool
  - Route to the matching tool function from Phases 2-4
- Log every decision: `{"task": "change_detection", "tool_called": "detect_change", "input_type": "bi_temporal_pair"}`

### Phase 7 — Output Combiner + Confidence (Day 5)
- Merge tool output into a consistent response schema:
  ```json
  {
    "answer": "text response",
    "evidence": {"bbox": [...], "overlay_image": "base64..."},
    "confidence": 0.0-1.0,
    "execution_log": {...}
  }
  ```
- Confidence can start simple — e.g. a heuristic based on Moondream2's response length/specificity, or just a fixed placeholder with a note that this becomes a learned calibration in the full version

### Phase 8 — FastAPI Backend (Day 5-6)
- Single endpoint: `POST /query` accepting image(s) + text query, returning the combined response
- Wire the LangGraph controller as the core logic behind this endpoint

### Phase 9 — Streamlit Frontend (Day 6)
- Upload widget (supports 1 or 2 images)
- Text query box
- Display: answer text, image with bbox overlay (if grounding), confidence, and a readable execution log panel
- Keep it simple — functional over polished for this round

### Phase 10 — End-to-End Testing (Day 6-7)
- Run through all 5 representative queries from the problem statement
- Fix routing misclassifications, prompt issues, or crashes
- Prepare 2-3 clean demo examples you know work well for the actual presentation

---

## 5. Timeline Summary

**~7 days total**, roughly:
- Days 1-2: environment + core VQA/caption/grounding
- Days 2-4: change detection + fusion + input validation
- Days 4-6: controller + backend + frontend
- Days 6-7: testing + polish + demo prep

---

## 6. What to Say in Your Pitch

Be explicit that this is a **working proof-of-concept demonstrating the full agentic architecture**, using a lightweight general-purpose VLM (Moondream2) as a stand-in for the domain-adapted model. Show your Phase 2 roadmap (the BigEarthNet.txt fine-tuning plan from before) as the clear next step — judges respond well to seeing the distinction between "this proves the concept works end-to-end" and "this is our final accuracy number," rather than either overselling the local demo's accuracy or underselling the architecture's completeness.

---

## 7. Known Limitations to Flag Yourself (before a judge finds them)

- Moondream2 has no remote-sensing domain knowledge — expect generic/imprecise land-cover terminology
- Change detection is unsupervised pixel-diff, not learned — will produce false positives from lighting/seasonal differences, not just real change
- "Fusion" is prompt-level, not learned cross-attention — genuinely joint SAR-optical reasoning is limited
- Confidence score is heuristic, not calibrated
- These are exactly the gaps the full training roadmap (BigEarthNet.txt fine-tuning) closes in the next phase
