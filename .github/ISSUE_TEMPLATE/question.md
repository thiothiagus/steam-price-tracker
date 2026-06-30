name: Question
description: Ask a question about the project
title: "[QUESTION] "
labels: ["question"]
body:
  - type: markdown
    attributes:
      value: |
        Have a question? Please provide as much detail as possible.

  - type: textarea
    id: question
    attributes:
      label: Question
      description: What would you like to know?
    validations:
      required: true

  - type: textarea
    id: context
    attributes:
      label: Additional Context
      description: Add any relevant context or background information.