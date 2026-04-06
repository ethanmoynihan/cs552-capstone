# Voice-Driven Mathematical Equation Editor Using a Large Language Model

## Introduction and Objective

### Introduction

Writing complex mathematical equations in traditional editors such as LaTeX or GUI equation builders can be slow, unintuitive, and mentally taxing. Users must dedicate time to understand LaTeX syntax or GUI which can act as a barrier to entry to describing equations in writing equations and interrupts mathematical reasoning and problem solving.

This project proposes a web platform that allows users to speak mathematical expressions aloud, which are then processed in real time into functional LaTeX code and is rendered visually as mathematical equations. The system aims to reduce friction in equation writing and improve accessibility.

### Objective

The objective of this project is to develop a web based platform driven by an open source large language model (LLM) that will be capable of: Conversion of spoken mathematical equations and symbols into valid LaTeX code, real time rendering of equations, voice based editing commands, and exporting of the equations to LaTeX. This system aims to lower the barrier to writing mathematical notation on a computer and improve accessibility for users unfamiliar with LaTeX or those with motor impairments.

## LLM Selection and Justification

This project will be built using LLaMA 3 (8B parameters). The selection of LLaMA 8B parameters is motivated by performance, deployment feasibility, and instruction following capabilities.

**Justification:**

- Strong instruction-following capability good for structured text generation
- 8k token context window large enough for long mathematical expressions
- Lightweight enough to run on a single GPU with 16-24GB of VRAM
- Up to date world knowledge not necessary
- Actively supported and available via Hugging Face

The model will be prompted to behave as a structured LaTeX generator to constrain it to only output valid LaTeX code.

## Project Definition

This project is under the umbrella of content generation using LLMs. The system generates formal mathematical markup using natural language input.

**Input:**

- Spoken mathematical expression
- Speech converted to text using a separate Automatic Speech Recognition (ASR) model

**Outputs:**

- Syntactically valid LaTeX code
- Real-time rendered mathematical equation
- Editable LaTeX source
- Exportable LaTeX compatible string

The LLM acts as a semantic interpreter that converts natural language into structured mathematical markup. Separating itself from traditional equation editors, this approach leverages language understanding to reduce interface complexity.

## Implementation Plan

### Architecture Overview

The system will be comprised of three major components:

**Speech Recognition Module:**

- Model: Open source ASR
- Role: Translates speech to text transcript

**LLM Inference Module:**

- Model: LLaMA 3 8B
- Framework: PyTorch
- Role: Convert Natural Language to function LaTeX mathematical equations

**Web Application:**

*Frontend:*

- React
- Vite
- Live LaTeX rendering using MathJax
- Voice command interface and transcript display
- Role: Output display for equations and user interaction

*Backend:*

- Python with FastAPI
- Model inference endpoint
- Model response output

The GPU will be hosted using Hugging Face Inference Endpoints and the frontend will be hosted using Netlify.

## Model Evaluation Criteria

Evaluation will focus on measurable system performance of the following:

### Latency

The end to end latency from speech spoken to the rendered equation. Setting a target of less than 3 seconds of total latency. Token generation speed will be directly measured from the model inference in tokens per second.

### Resource Usage

Computation resources will be measured as the model performs the LaTeX generation task. These will include:

- GPU memory consumption
- GPU utilization percent
- CPU utilization percent

### Accuracy

Exact LaTeX strings match the reference expressions which will be defined in LaTeX in advance. This will be measured by an edit distance from the ground truth LaTeX. Mathematical equivalence will be checked for against the ground truth as well. A rendering success rate will be tracked during these tests, either tracked by the tester or through automated error reading depending on time.

### Scalability and Robustness

The model will be tested against larger equations and complex edit requests from the user. Ambiguous phrasing will be tested against the model to describe some ground truth equations. The model will be tested for concurrent requests.

## Expected Outcomes and Challenges

### Expected Outcomes

This project should:

- Lead to a reduced amount of time required to create mathematical equations.
- Provide a simple and understandable user interface that is more practical than GUI-based editors
- Help mathematicians with motor impairments write their equations

### Expected Challenges

Some potential challenges that this project will face are:

- **Speech recognition mistakes:** issues with the speech recognition model could propagate into errors that impact the model. To mitigate this the user should be able to correct their messages after transcription and make edits to the final equation.
- **LaTeX rendering issues during token streaming:** As the model streams its output to the frontend there may be issues in rendering the partially completed LaTeX. This can be mitigated by batching the output or having an error tolerant display pane.
- **Ambiguity in Spoken Math:** this challenge can arise from phrases like "x cubed over two plus 10" which can be grouped in several different ways. Mitigation for this will be iterative prompting by the user.

### Resources Required

- LLaMA 3 8B
- Whisper (open source ASR model)
- PyTorch
- React
- Vite
- MathJax
- Hosted GPU (likely from Hugging Face Inference Endpoints)
- Netlify (frontend hosting)

## Conclusion

This project aims to transform spoken language into mathematical notation in real time using a LLM. Integration of speech recognition, LLM LaTeX generation, and live rendering of equations will help to bridge natural spoken language and mathematical expression. The proposed application demonstrates a real world application of open source LLM used to generate structured content within a specific use case.
