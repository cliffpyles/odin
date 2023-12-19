#!/usr/bin/env python

import click
import sys
import os
import requests
import boto3
from urllib.parse import urlparse


# Function to determine if a string is a valid URL
def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


# Function to check if a string is an S3 path
def is_s3_path(string):
    return string.startswith("s3://")


# Function to read content from a file, URL, or S3 path
def read_content_from_source(source):
    # Check if source is a URL
    if is_url(source):
        response = requests.get(source)
        return response.text

    # Check if source is an S3 path
    if is_s3_path(source):
        s3 = boto3.client("s3")
        bucket, key = source[5:].split("/", 1)
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read().decode("utf-8")

    # Otherwise, treat it as a file path
    if os.path.isfile(source):
        with open(source, "r") as file:
            return file.read()

    return source


# Function to read from stdin if prompt is empty
def read_stdin_if_empty(prompt):
    if not prompt:
        return sys.stdin.read().strip()
    return prompt


# Function to process template arguments
def process_template_arguments(prompt, template_args):
    for arg in template_args:
        key, value = arg.split("=")
        prompt = prompt.replace(f"{{{key}}}", value)
    return prompt


# Define the main CLI group with examples
@click.group(
    epilog="""\b
Examples:
  ask bedrock "Tell me a joke"
  ask openai "Tell me a fact" --model="gpt-4"
  ask openai "How's the weather in {city}?" city=London
  ask openai /path/to/prompt.txt
  ask bedrock https://example.com/prompt.txt
  ask openai s3://mybucket/prompt.txt
"""
)
def ask():
    """This tool allows interaction with AI services such as OpenAI and Amazon Bedrock."""
    pass


# Modify the bedrock and openai functions to use read_content_from_source
@ask.command(
    help="""\b
Interact with Amazon Bedrock.

Examples:
  ask openai "Tell me a fact" --model="gpt-4"
  ask openai "Translate '{text}' to French" text="Hello, world" --model="gpt-4"
  ask openai "How many {unit} in a mile?" unit=kilometers
  ask openai /path/to/fact_request.txt
  ask openai s3://mybucket/fact_request.txt
  ask openai https://example.com/fact_request.txt
"""
)
@click.argument("prompt", required=False)
@click.argument("template_args", nargs=-1)
def bedrock(prompt, template_args):
    prompt = read_content_from_source(read_stdin_if_empty(prompt))
    prompt = process_template_arguments(prompt, template_args)
    # LangChain code here for Amazon Bedrock
    response = f"Bedrock response to: {prompt}"
    print(response)


@ask.command(
    help="""\b
Interact with OpenAI.

Examples:
  ask openai "Tell me a fact" --model="gpt-4"
  ask openai "Translate '{text}' to French" text="Hello, world" --model="gpt-4"
  ask openai "How many {unit} in a mile?" unit=kilometers
"""
)
@click.argument("prompt", required=False)
@click.argument("template_args", nargs=-1)
@click.option("--model", default="gpt-4", help="Specify the model")
@click.option("--chat", help="Name of the chat session")
def openai(prompt, model, chat, template_args):
    prompt = read_content_from_source(read_stdin_if_empty(prompt))
    prompt = process_template_arguments(prompt, template_args)
    # LangChain code here for OpenAI
    response = f"OpenAI ({model}) response to: {prompt}"
    print(response)


if __name__ == "__main__":
    ask()
