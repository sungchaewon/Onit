# O-nit

O-nit is a generative AI prototype for custom cake order drafting and design guide creation.

## Project Goal

This project converts unstructured custom cake order inputs, including reference images and user text, into a structured order draft and a visual design guide.

## Pipeline

1. Collect and label custom cake reference images.
2. Generate a structured order draft using Gemini.
3. Convert the order draft into a ComfyUI prompt.
4. Generate a cake design guide image with ComfyUI.
5. Display the order draft and generated image in a React prototype UI.

## Tech Stack

- Gemini
- ComfyUI
- Python
- React
