# Setting Up Euphrosyne for a New Laboratory

This guide covers the process of configuring the Euphrosyne platform for deployment in a new laboratory setting.

## Overview

Euphrosyne is designed to be adaptable to different laboratories with varying analysis methods, equipment, and operational requirements. This documentation will walk you through the essential configuration steps needed when setting up Euphrosyne for a new laboratory.

## Prerequisites

- Python 3.10+
- PostgreSQL database

## Basic Configuration

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/betagouv/euphrosyne.git
cd euphrosyne

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt
npm install
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and edit the values to configure Euphrosyne.

### 3. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Laboratory-Specific Configuration

### 1. Configuring Analysis Methods

Euphrosyne's method system allows for complete customization of the available analysis techniques, detectors, and filters specific to your laboratory.

Please refer to the detailed guide: [Configuring Lab Methods](configuring_lab_methods.md)

This documentation explains how to:

- Modify available methods (e.g., PIXE, PIGE, FTIR, XRF)
- Configure detectors for each method
- Set up filters for different detectors
- Generate migrations for your changes

### 2. Configuring Run Metadata and Run Detail Forms

Run metadata fields (for example: particle type, energy, beamline) and lab-specific
run detail forms are customizable per deployment.

Please refer to the detailed guide: [Configuring Run Metadata](configuring_run_metadata.md)

This documentation explains how to:

- Define lab-specific run metadata fields
- Control the "Experimental conditions" fieldset in admin
- Configure run detail forms for members and admins

## Testing Your Configuration

Run the following commands to ensure your configuration is working correctly:

```bash
# Run tests
pytest

# Build frontend assets
npm run build:dev

# Start the development server
python manage.py runserver
```
