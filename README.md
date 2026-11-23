# AI Structured JSON Output Validator

## Project Description
This project uses Google Gemini API and Python
to generate structured JSON output.

Pydantic validates the generated data against
a predefined schema.

## Features
- JSON schema definition
- Pydantic validation
- Automatic retry and repair
- Typed Python output
- Error handling

## Technologies
- Python
- Google Gemini API
- Pydantic
- JSON

## Installation

Install the required libraries:

pip install -r requirements.txt

Create a .env file and add your Gemini API key.

## Run the project

python main.py

## Expected Result

The program accepts text and generates
validated JSON containing:

- Topic
- Category
- Difficulty
- Summary

If validation fails, the program retries
up to three times.