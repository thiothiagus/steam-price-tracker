name: Bug Report
description: Report a bug or unexpected behavior
title: "[BUG] "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report!

  - type: textarea
    id: description
    attributes:
      label: Description
      description: A clear and concise description of what the bug is.
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: Steps to reproduce the behavior.
      placeholder: |
        1. Go to '...'
        2. Click on '...'
        3. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: A clear and concise description of what you expected to happen.
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: A clear and concise description of what actually happened.
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: Please provide your system information.
      placeholder: |
        - OS: [e.g. Windows 11, macOS 14, Ubuntu 22.04]
        - Python version: [e.g. 3.12]
        - App version: [e.g. 1.0.0]
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Logs
      description: If applicable, add error logs to help explain the problem.
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Add any other context about the problem here.