# Euphrosyne Project Ecosystem

Euphrosyne is a comprehensive scientific data management platform designed for heritage science analyses. The platform consists of multiple interconnected projects that work together to provide a complete solution for managing and exploring scientific data from heritage science analyses.

## Project Components

### 1. Main Django Application (euphrosyne)

The core platform built with Django and modern JavaScript/TypeScript.

#### Core Architecture

- Django (Python) backend
- Modern JavaScript/TypeScript frontend with Web Components
- Webpack for frontend module bundling
- OpenSearch (Elasticsearch) for catalog and search functionality
- Azure Storage for file storage
- ORCID integration for researcher authentication

#### Key Features

- Project Management for scientific investigations
- Object Management with materials, dating, and provenance
- Experimental Methods with configurable parameters
- Digital Laboratory Notebook
- Secure Data Management
- Collaboration Tools
- Integration with external services (ORCID, OpenSearch)

#### Main Modules

##### Lab Module (`/lab/`)

- Core scientific data management
- Features:
  - Project management
  - Experimental runs
  - Object documentation
  - Integration with EROS database
  - Catalog and search functionality:
    - Project and object group indexing
    - Advanced search capabilities
    - Material and location-based filtering
    - Date-based aggregations

##### Tools Module (`/euphro_tools/`)

- Utility functions and hooks to integrate with tools-api

##### Authentication (`/euphro_auth/`)

- User management
- ORCID integration

##### Lab Notebook (`/lab_notebook/`)

- Digital documentation of experiments
- Description of measurement points

##### Data Request (`/data_request/`)

- Data access management

### 2. Catalog Frontend (euphrosyne-digilab)

A Next.js application that provides a digital lab interface.

#### Features

- Data catalog for project & object items
- Data request for run data

### 3. API Service (euphrosyne-tools-api)

A Python-based API service built with FastAPI that serves as a middleware between the main application and various external services (Azure & Guacamole).

#### Core Features

- Azure cloud service integrations
- Authentication system with JWT token validation

#### Key Components

- Azure Cloud Services:
  - Virtual Machine management
  - Image processing and management
  - Data storage and streaming
  - Infrastructure management
  - Storage operations
  - VM size definitions (`common.py`)
  - Version management (`version.py`)
- Apache Guacamole:
  - Remote desktop access management
  - Connection and user management

### 4. Infrastructure (euphrosyne-tools-infra)

Infrastructure as Code project managing deployment and infrastructure using Terraform and Azure Bicep.

#### Core Components

##### Network Infrastructure

- Virtual Network (VNet) with multiple subnets:
  - VM subnet for virtual machines
  - Guacamole subnet for remote desktop access
  - SQL subnet for database services
  - Private subnet for container instances
- Service endpoints for Azure Storage
- Network security groups and rules

##### Compute Resources

- Virtual Machines:
  - Windows-based VMs for scientific computing
  - Custom VM images stored in Shared Image Gallery
  - Support for multiple VM sizes (B8ms, B20ms, E16s_v5)
  - Availability zones for high availability
- App Service:
  - Linux-based service plan for Guacamole
  - Container instances for specific workloads

##### Storage Solutions

- Azure Storage Accounts:
  - File shares for data storage
  - Blob storage for object storage
  - Integration with VNet service endpoints
- Key Vault:
  - Secret management
  - Access policies
  - Soft delete protection

##### Database Services

- MySQL Flexible Server:
  - Private subnet deployment
  - Network isolation
  - Flexible scaling options

#### Infrastructure Management

##### Terraform Configuration

- Resource group management
- Network infrastructure
- Storage solutions
- Database services
- App Service configuration
- VM image gallery
- Key Vault setup

##### Bicep Templates

- VM deployment templates
- Network interface configuration
- Storage integration
- Custom script extensions
- Drive mounting automation

#### Deployment Environments

- Staging environment
- Production environment
- Environment-specific variables
- Resource naming conventions

## Project Interactions and Infrastructure Design

### System Architecture

#### Component Interactions

1. **Euphrosyne (Main Django Application)**

   - Communicates with tools-api for:
     - VM management
     - Storage operations
     - Remote desktop access
   - Direct interaction with OpenSearch for:
     - Catalog indexing
     - Search queries
     - Data aggregation
   - Provides API endpoints for Digilab

2. **Digilab (Next.js Frontend)**

   - Interacts with Euphrosyne as an API interface for OpenSearch
   - Accesses search and catalog functionality

3. **tools-api (API Service)**

   - Acts as a middleware between Euphrosyne and Azure services
   - Manages Azure resources:
     - VM operations
     - Storage management
     - Network configuration
   - Handles Guacamole integration for remote desktop access

4. **OpenSearch (Elasticsearch)**
   - Directly integrated with Euphrosyne
   - Handles:
     - Catalog indexing
     - Search functionality
     - Data aggregation
     - Material and location filtering

## Getting Started

For detailed setup instructions, please refer to each project specifically:

- [Euphrosyne - Main Application](https://github.com/betagouv/euphrosyne)
- [Data Catalog](https://github.com/betagouv/euphrosyne-digilab)
- [tools-api](https://github.com/betagouv/euphrosyne-tools-api)
- [Infrastructure management](https://github.com/betagouv/euphrosyne-tools-infra)
