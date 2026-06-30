name: Feature Request
description: Suggest an idea for this project
title: "[FEATURE] "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for suggesting a feature! Please provide as much detail as possible.

  - type: textarea
    id: problem
    attributes:
      label: Problem Statement
      description: Is your feature request related to a problem? Please describe.
      placeholder: I'm always frustrated when [...]
    validations:
      required: false

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: A clear and concise description of what you want to happen.
    validations:
      required: true

  - type: textarea
    id: use_case
    attributes:
      label: Use Case
      description: Describe the use case or user story this feature would address.
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: Describe any alternative solutions or features you've considered.
    validations:
      required: false

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Add any other context, mockups, or examples about the feature request.