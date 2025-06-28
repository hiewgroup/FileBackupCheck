# Preserve and Cleanup Folder Comparator

This small GUI utility helps you reconcile the contents of two directories:

* **Preserve Folder** – the directory that holds your reference copies.
* **Cleanup Folder** – a folder that may contain duplicates or new files to merge.

The program calculates SHA256 hashes for every file in both folders and suggests
what to do with the files from the cleanup folder. You can then delete duplicates
or move new/mismatched files into the preserve folder.

> **Note**
> The hashing is performed using the Windows `certutil` command, so the tool is
> primarily intended for Windows systems. Ensure `certutil` is available in your
> `PATH`.

## Features

- Detects files in the cleanup folder that have identical content to files in the
  preserve folder and marks them for deletion.
- Detects files with the same relative path but different content. These are
  moved to the preserve folder with a `'` added before the file extension to
  avoid overwriting the original.
- Detects brand new files in the cleanup folder and moves them into the preserve
  folder, recreating any necessary subdirectories.
- Displays a sortable table showing each file, its SHA256 hash and the planned
  action.
- Provides progress feedback during hashing and file operations.

## Getting Started

### Requirements

- Python 3 with `tkinter` installed (included with the standard Windows Python
  installers).
- `certutil` accessible from the command line (bundled with Windows).

### Running the Application

1. Clone or download this repository.
2. Launch the GUI by running:
   ```bash
   python FileChecker.py
   ```

### Workflow

1. **Select Folders** – Click `Select Preserve Folder` to choose your reference
   directory (Folder A). Then click `Select Cleanup Folder` to choose the folder
   you want to merge or clean up (Folder B).
2. **Prepare Comparison** – Click `Prepare Comparison`. The program hashes every
   file in both folders and populates the table with its findings.
3. **Review Actions** – The table lists each file's relative path, its SHA256
   hash, and the proposed action (`Delete`, `MOVE`, or `Reference Copy`). You can
   sort the table by clicking the column headers.
4. **Execute** – Use the buttons to carry out the desired operations:
   - `Delete Identical` removes duplicate files from the cleanup folder.
   - `Move Mismatched` moves files that share a path but differ in content. The
     moved file is renamed with a `'` before the extension.
   - `Move New` moves files that exist only in the cleanup folder.

Each operation updates the table so you can review the results or run additional
passes if needed.

## Notes

- The tool modifies files directly. Consider testing on sample data first to
  ensure it performs as expected.
- Error messages are printed to the console if a file cannot be processed.
- You can add screenshots to this README to illustrate the GUI layout and
  workflow.

