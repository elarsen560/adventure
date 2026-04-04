# Image Asset Plan

This folder is reserved for desktop-wrapper visuals:

- startup/title artwork
- later room/location visuals for the right-side visual panel

## Style Direction

- late 1980s / early 1990s adventure-game feel
- DOS VGA-inspired background art
- hand-painted pixel-art look rather than chunky 8-bit sprites
- visible but controlled pixel structure
- restrained palette with storm blues, slate greys, lamp amber, oxidized brass-green
- atmospheric and readable at moderate size

## Recommended Asset Sizes

Working composition target:

- think in `320x200` scene-composition terms

Saved runtime asset target:

- `640x400` PNG for startup and room visuals

This preserves a retro aspect while still looking acceptable in the desktop wrapper.

## Initial Usage

The first visual to create is the startup/title image:

- `assets/images/startup/cover_v1.png`

Later room visuals should follow:

- `assets/images/rooms/<room_id>.png`

Examples:

- `assets/images/rooms/cliff_path.png`
- `assets/images/rooms/front_gate.png`
- `assets/images/rooms/courtyard.png`

## Prompt Sources

Prompt candidates for the startup image live in:

- `assets/images/prompts/startup_cover_candidates.md`

## Notes

- Do not bake UI text into the images.
- Treat these as background plates, not posters with lettering.
- Prefer one approved visual house style before generating room batches.
