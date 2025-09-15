# Overlay Images

This directory contains overlay images for the multi-view capture system.

## Required Files

Place the following PNG files in this directory:

- `front_overlay.png` - Overlay for front view capture
- `side_overlay.png` - Overlay for side view capture  
- `rear_overlay.png` - Overlay for rear view capture

## Overlay Specifications

Each overlay should be:
- PNG format with transparency
- 1080x1920 resolution (portrait orientation)
- Semi-transparent guide showing where to position the animal
- Include a rectangular guide box for the animal
- Include a small square in the bottom-left corner for ArUco marker placement

## Placeholder Images

For development, you can use simple colored rectangles as placeholders:
- Front: Blue rectangle in center
- Side: Green rectangle in center  
- Rear: Red rectangle in center

Each should have a small white square in the bottom-left corner for the ArUco marker guide.
