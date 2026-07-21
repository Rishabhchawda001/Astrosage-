# AstroSage Art Studio

Visual Generation Pipeline for AstroSage AI hero artwork.

## Structure

```
art_studio/
├── providers/        # Image generation provider abstraction
├── prompts/          # Versioned prompt library
├── evaluation/       # Quality scoring system
├── history/          # Version management
├── integration/      # Pipeline orchestration
├── research/         # Art direction research
├── generated/        # Generated artwork
├── exports/          # Exported artwork
└── cli.py            # CLI interface
```

## Usage

```bash
python -m art_studio status
python -m art_studio providers
python -m art_studio prompts
python -m art_studio generate --count 2
python -m art_studio evaluate image.jpg --prompt-id v3_painterly_tradition
python -m art_studio accept image.jpg --prompt-id v3_painterly_tradition
python -m art_studio versions
```

## Adding Providers

Implement `ImageProvider` base class, register in `providers/__init__.py`.

## Quality Dimensions

12 weighted dimensions including composition, lighting, readability,
historical plausibility, anatomy, color harmony, and premium appearance.
