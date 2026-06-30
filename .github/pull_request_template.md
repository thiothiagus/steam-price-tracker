name: Pull Request
description: Create a pull request to contribute to the project
title: ""
labels: []
body:
  - type: markdown
    attributes:
      value: |
        Thanks for contributing! Please fill out the checklist below.

  - type: textarea
    id: description
    attributes:
      label: Description
      description: Describe your changes and why they are needed.
    validations:
      required: true

  - type: textarea
    id: related
    attributes:
      label: Related Issue
      description: Link to any related issues (e.g., "Fixes #123").
    validations:
      required: false

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: My code follows the project's style guidelines (PEP 8)
          required: true
        - label: I have added type hints to my functions
          required: true
        - label: I have added docstrings to public functions
          required: true
        - label: I have written tests for my changes (when applicable)
          required: false
        - label: I have updated the documentation (when applicable)
          required: false
        - label: I have tested my changes locally
          required: true

  - type: textarea
    id: testing
    attributes:
      label: Testing Done
      description: Describe the testing you performed to verify your changes.
    validations:
      required: true

  - type: textarea
    id: screenshots
    attributes:
      label: Screenshots
      description: If applicable, add screenshots to help explain your changes.
    validations:
      required: false