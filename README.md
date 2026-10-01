# SINOVA

SINOVA is a local-first desktop application for micro-computed tomography (microCT) projection preprocessing. It provides interactive projection and sinogram previews, configurable preprocessing pipelines, background full-stack processing, and export to common scientific imaging formats.

The application is designed for large local datasets. Raw MRAW and DAT inputs are accessed through read-only memory mapping where possible, and full-stack processing uses a file-backed workspace to avoid requiring the entire dataset in RAM.

## Features

- Load local DICOM, TIFF, MRAW, and DAT datasets.
- Inspect projection frames and sinograms before processing.
- Configure independent preprocessing operations in an enforced dependency order.
- Apply intensity, spatial, geometry, and destriping operations.
- Preview the current slice without modifying the source dataset.
- Run the configured pipeline across the complete stack as a background job.
- Monitor progress and cancel active processing jobs.
- Export processed data as TIFF, MRAW, DAT, or a DICOM series.
- Use CUDA acceleration for the neural destriping operation when a compatible PyTorch installation and GPU are available.
- Keep all dataset processing local. SINOVA does not require a hosted inference service.

## Supported Formats

### Input

- **DICOM**: A DICOM file, multi-frame DICOM file, or directory containing a DICOM series.
- **TIFF**: A multi-page TIFF, a single TIFF image, or a directory of single-image TIFF files.
- **MRAW**: A raw MRAW file with its corresponding `.cih` or `.cihx` header.
- **DAT**: Headerless C-order binary data shaped as `projections x height x width`. A matching JSON sidecar is recommended and may define `width`, `height`, `projection_count`, `dtype`, and `offset`.

Headerless DAT files cannot describe their dimensions by themselves. Provide the sidecar when the dimensions and data type are not otherwise known. SINOVA validates the file size against the declared layout before loading it.

### Output

Processed data is written to the backend output directory, normally `./data/exports`:

- BigTIFF multi-page `.tiff`
- Float32 `.mraw` with a `.cih` header
- Float32 `.dat` with a matching `.json` sidecar
- A directory of DICOM files

## Preprocessing Operations

Available operations include:

- Normalization using flat and dark references
- Negative logarithm conversion
- Attenuation clipping
- FOV and beam masking
- Beam cropping and padding
- Median or Gaussian denoising
- Projection mutation and resampling
- Center of rotation estimation and adjustment
- Fourier-wavelet destriping through TomoPy
- Vo sorting-based destriping through TomoPy
- Neural destriping using an implicit neural representation of sinogram data

Operation dependencies and context restrictions are validated by the backend. For example, negative logarithm requires normalization, while destriping operations operate on sinograms.

## Neural Destriping

SINOVA includes a local, zero-shot PyTorch implementation of the implicit neural representation approach described in:

> Shi, L., Jiang, X., & Liu, Y. (2024). Ring Artifacts Removal Based on Implicit Neural Representation of Sinogram Data. *arXiv preprint arXiv:2409.15731*. https://arxiv.org/abs/2409.15731

The implementation is based on the paper and is maintained as part of this project. It trains a fresh representation for each sinogram and does not require a pretrained checkpoint or an external model service. CUDA is selected automatically when available; otherwise processing runs on the CPU.

The practical model choice is the local zero-shot INR implementation when avoiding hosted inference fees, model storage, and external data transfer is more important than minimum runtime. It is computationally expensive, especially on large sinograms. For lower compute cost and higher throughput, use the TomoPy Fourier-wavelet or Vo sorting methods instead.

## Release Downloads

The GitHub Releases page provides two platform-specific ZIP archives:

- **Windows**: the Windows desktop application package
- **Linux**: the Linux desktop application package

Each archive includes its own release README with platform-specific launch instructions. Download the archive for the target operating system, extract it to a local directory, and launch the included SINOVA application. The packaged application starts the FastAPI backend sidecar automatically.

Use a writable location for the extracted application and for dataset output. Do not place active datasets inside the application directory unless that is intentional.

## Source Development

### Backend

The backend is a FastAPI application in `sinova-backend`. It provides dataset ingestion, preview, preprocessing job management, health reporting, and export services.

```text
cd sinova-backend
python -m venv .venv
source .venv/bin/activate        # Linux
# .venv\Scripts\activate         # Windows PowerShell
pip install -r requirements.txt
python -m app.main
```

The API listens on `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

The backend also depends on a working PyTorch installation for health reporting and neural destriping. Install the PyTorch build appropriate for the target CPU or CUDA environment before using that operation.

### Frontend

The frontend is a React and TypeScript application using Vite. The desktop shell is provided by Tauri.

```text
cd sinova-frontend
npm install
npm run dev
```

For a production frontend build:

```text
npm run build
```

For local Tauri development, install the Rust toolchain and Tauri prerequisites for the target operating system. The Tauri application expects the packaged backend sidecar configured in `sinova-frontend/src-tauri`.

## Architecture

```text
React + TypeScript + Plotly
            |
     Tauri desktop shell
            |
     FastAPI backend sidecar
            |
  Business services and jobs
            |
 Readers, TomoPy, SciPy, PyTorch
```

The backend separates business services from infrastructure readers and processing algorithms. Dataset readers expose a shared interface, allowing the ingestion and preprocessing workflows to remain independent of the input format.

## Data and Privacy

SINOVA is intended for local processing. Dataset paths are supplied to the local backend, and processing results are written to the local output workspace. Review the access permissions and output location of the operating system account used to run the application.

## License

This project is licensed under the MIT License.