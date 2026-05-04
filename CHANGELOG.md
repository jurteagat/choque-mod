# Changelog

## [0.2.0] - 2026-04-16

### Changed

- **Pivote de producto**: el proyecto pasa de ser un extractor de diapositivas a un simulador de impacto de una camioneta rodando por una pendiente (Shiny for Python).

### Added

- Módulo `physics` con aceleración neta, velocidad de impacto, energía cinética, probabilidad de fatalidad (Rosén & Sander 2009) y clasificación AIS.
- Módulo `plotting` con esquema 2D de la escena y perfil de velocidad/energía (Plotly).
- App Shiny con sliders para pendiente, distancia y masa, y selector de superficie.
- Tests unitarios para el modelo físico (`tests/test_physics.py`).

### Removed

- Funcionalidad de extracción de diapositivas desde video (OpenCV, OCR con ocrmypdf, generación de PDF).
- Dependencias: `opencv-python`, `scikit-image`, `Pillow`, `img2pdf`, `ocrmypdf`.

## [0.1.0] - 2026-04-05

### Added

- Initial release of the slide extractor Shiny app.
- Video upload support (mp4, avi, mov, mkv, webm).
- Auto-detection of slide region using OpenCV contour analysis.
- Manual region selection via image clicks or numeric inputs.
- Slide transition detection using SSIM comparison.
- Lossless PDF generation with img2pdf.
- OCR text layer (Spanish + English) with ocrmypdf.
- Interactive preview with region overlay.
- Slide gallery view with thumbnails.
- Processing log panel.
- Unit tests for slide detector, transition detector, and PDF generator.
