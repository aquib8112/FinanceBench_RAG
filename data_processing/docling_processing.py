# Originally used on Kaggle with an NVIDIA GPU and four CPU threads.
# This version defaults to CPU; change DEVICE to AcceleratorDevice.CUDA for GPU.
# Edit the PDF paths and output directory for your own environment.
# CPU processing can take considerably longer.

import json
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


DEVICE = AcceleratorDevice.CPU

PDF_PATHS = [
    # insert pdf paths
]

OUTPUT_DIR = Path("")  # insert output path


options = PdfPipelineOptions(do_table_structure=True)
options.accelerator_options = AcceleratorOptions(
    num_threads=4,
    device=DEVICE,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=options)
    }
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for pdf_path in PDF_PATHS:
    result = converter.convert(pdf_path)
    output_path = OUTPUT_DIR / f"{Path(pdf_path).stem}.json"

    output_path.write_text(
        json.dumps(result.document.export_to_dict(), ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved: {output_path.name}")
