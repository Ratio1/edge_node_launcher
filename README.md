# Edge Node Launcher

Edge Node Launcher is a desktop application designed to manage the containerized edge node of Naeural Edge Protocol. It allows you to edit environment files, check Docker availability, launch and stop Docker containers, plot data from JSON files, and perform other management tasks.

## Table of Contents
- [Features](#features)
- [Binary Installation](#binary-installation)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [macOS (Apple Silicon)](#macos-apple-silicon)
  - [Windows](#windows)
  - [Ubuntu](#ubuntu)
- [Source Code Install](#source-code-install)
- [Building the Application](#building-the-application)
- [Usage](#usage)
  - [Editing Environment Files](#editing-environment-files)
  - [Checking Docker Availability](#checking-docker-availability)
  - [Launching and Stopping Docker Containers](#launching-and-stopping-docker-containers)
  - [Viewing Plots](#viewing-plots)
  - [Updating the Application](#updating-the-application)
- [Development](#development)
- [Citation](#citation)
- [License](#license)

## Features

- Edit `.env` files for Docker container configuration
- Check if Docker is available and prompt for installation if not
- Launch and stop Docker containers
- Display plots for CPU load, memory load, GPU load, and GPU memory load
- Refresh plots every 10 seconds
- Copy local node address
- Delete specific files and restart containers
- Toggle between dark and light themes

## Platform-Specific Instructions

### macOS (Apple Silicon)
1. Download the latest `EdgeNodeLauncher-OSX-arm64-[version].zip` from the [Releases page](https://github.com/Ratio1/edge_node_launcher/releases)
2. Extract the zip file
3. If you encounter security restrictions when trying to open the app:
   - Open Terminal
   - Run the following command (replace with your actual path):
     ```sh
     xattr -cr /path/to/EdgeNodeLauncher
     ```
   - Try running the app again
4. Install Docker Desktop for Apple Silicon if not already installed
5. Ensure Docker Desktop is running before launching the Edge Node Launcher

### Windows
1. Download the latest `EdgeNodeLauncher-WIN32-[version].zip` from the Releases page
2. Extract the zip file
3. Run the EdgeNodeLauncher executable
4. Install Docker Desktop for Windows if prompted
5. Ensure Docker Desktop is running before using the launcher

### Ubuntu
1. Download the appropriate Ubuntu version zip file from the Releases page:
   - For Ubuntu 24.04: `EdgeNodeLauncher-LINUX_Ubuntu-24.04-[version].zip`
   - For Ubuntu 22.04: `EdgeNodeLauncher-LINUX_Ubuntu-22.04-[version].zip`
   - For Ubuntu 20.04: `EdgeNodeLauncher-LINUX_Ubuntu-20.04-[version].zip`
2. Extract the zip file
3. Make the launcher executable:
   ```sh
   chmod +x EdgeNodeLauncher
   ```
4. Run the launcher:
   ```sh
   ./EdgeNodeLauncher
   ```
5. Install Docker if prompted or manually install using:
   ```sh
   sudo apt-get update
   sudo apt-get install docker.io
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

## Binary installation

Download from [Releases page](https://github.com/Ratio1/edge_node_launcher/releases) and run the app for your platform.

## Source code install

To install and run Edge Node Launcher, follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/Ratio1/edge_node_launcher.git
   cd edge_node_launcher
   ```

2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Run the application:
   ```sh
   python main.py
   ```

## Building the Application

The repository uses GitHub Actions to build and release binaries for different platforms (Windows, Ubuntu 22.04, and Ubuntu 20.04). The build process includes:

- Checking the version in `ver.py` and comparing it with the latest release version
- Building the application using PyInstaller
- Zipping the built artifacts and uploading them as release assets

## Usage

### Editing Environment Files

To edit the `.env` file used by the Docker container, click the "Edit .env File" button. The file will open in a text editor within the application. After making changes, save the file and close the editor.

### Checking Docker Availability

The application checks for Docker availability at startup. If Docker is not installed, you will be prompted to install it.

### Launching and Stopping Docker Containers

Use the "Launch Container" button to start the Docker container. If the container is already running, the button will show "Stop Container" to allow stopping the container.

### Viewing Plots

The application displays plots for CPU load, memory load, GPU load, and GPU memory load. The plots are updated every 10 seconds with data from a JSON file.

### Updating the Application

The application can check for updates, download the latest release, and replace the current executable. To check for updates, ensure you have an internet connection and the application will handle the rest.

## Development

### Code Structure

- `main.py`: Entry point for the application
- `app_forms/frm_main.py`: Main application form and logic
- `utils/const.py`: Constants used throughout the application
- `utils/docker.py`: Docker utility functions

### Stylesheets

The application uses stylesheets for UI theming. The stylesheets are defined in `utils/const.py` and applied to various widgets.

## Citation

If you use this software in your research, please cite the following paper:

```bibtex
@misc{milik2024naeuralaios,
  title={Naeural AI OS -- Decentralized ubiquitous computing MLOps execution engine}, 
  author={Beatrice Milik and Stefan Saraev and Cristian Bleotiu and Radu Lupaescu and Bogdan Hobeanu and Andrei Ionut Damian},
  year={2024},
  eprint={2306.08708},
  archivePrefix={arXiv},
  primaryClass={cs.AI},
  url={https://arxiv.org/abs/2306.08708},
}
```

Additionally, you can cite this repository as follows:

```bibtex
@misc{naeurallauncher2024,
  author = {Naeural Edge Protocol},
  title = {Edge Node Launcher},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/Ratio1/edge_node_launcher}},
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
