import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import shutil

def calculate_sha256(filepath):
    """Calculate SHA256 hash using Windows certutil."""
    try:
        result = subprocess.run(
            ["certutil", "-hashfile", filepath, "SHA256"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode == 0:
            # certutil output format:
            # Line 1: SHA256 hash of file.txt:
            # Line 2: 5a 5c b5 d6 8c 2e 37 e1 e6 1b 6e 2c 0a 57 dc 3a ...
            # Line 3: CertUtil: -hashfile command completed successfully.
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                # Extract the second line and remove all spaces
                sha256 = lines[1].strip().replace(' ', '')
                return sha256
            else:
                print(f"Unexpected output format when hashing {filepath}")
                return None
        else:
            print(f"Error hashing {filepath}: {result.stderr.strip()}")
            return None
    except Exception as e:
        print(f"Exception hashing {filepath}: {str(e)}")
        return None

def browse_preserve_folder():
    """Select Preserve Folder."""
    global preserve_folder
    preserve_folder = filedialog.askdirectory(title="Select Preserve Folder (Folder A)")
    preserve_label.config(text=f"Preserve Folder: {preserve_folder}")

def browse_cleanup_folder():
    """Select Cleanup Folder."""
    global cleanup_folder
    cleanup_folder = filedialog.askdirectory(title="Select Cleanup Folder (Folder B)")
    cleanup_label.config(text=f"Cleanup Folder: {cleanup_folder}")

def scan_files(base_folder):
    """Recursively scan all files inside a folder."""
    file_dict = {}
    for root, _, files in os.walk(base_folder):
        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, base_folder)
            file_dict[rel_path] = full_path
    return file_dict

def prepare_comparison():
    """Prepare comparison between Preserve and Cleanup folder."""
    if not preserve_folder or not cleanup_folder:
        messagebox.showwarning("Folders Not Selected", "Please select both folders.")
        return

    # Clear previous Treeview
    for item in tree.get_children():
        tree.delete(item)
    delete_plan.clear()
    move_mismatch_plan.clear()
    move_new_plan.clear()
    file_hashes.clear()

    # Step 1: Build complete hash tables for both folders
    preserve_files = scan_files(preserve_folder)
    cleanup_files = scan_files(cleanup_folder)
    
    total_files = len(preserve_files) + len(cleanup_files)
    files_processed = 0
    
    # Set up progress tracking
    progress_var.set(0)
    progress_label.config(text=f"Building hash tables: 0/{total_files}")
    root.update()
    
    # Build hash tables for preserve folder
    preserve_hashes = {}  # sha256 -> list of file paths
    preserve_path_to_hash = {}  # path -> sha256
    
    print(f"Scanning preserve folder ({len(preserve_files)} files)...")
    for index, (rel_path, preserve_fullpath) in enumerate(preserve_files.items(), 1):
        files_processed += 1
        progress_var.set(int(100 * files_processed / total_files))
        progress_label.config(text=f"Hashing preserve: {index}/{len(preserve_files)}")
        
        if index % 5 == 0:
            root.update()
            
        hash_value = calculate_sha256(preserve_fullpath)
        if not hash_value:
            continue
            
        # Store in hash-to-paths mapping
        if hash_value not in preserve_hashes:
            preserve_hashes[hash_value] = []
        preserve_hashes[hash_value].append(rel_path)
        
        # Store in path-to-hash mapping
        preserve_path_to_hash[rel_path] = hash_value
        
        # Also store in global hash dict for display
        file_hashes[rel_path] = hash_value
        
        # Add to tree view as a reference copy
        tree.insert("", "end", values=(
            rel_path,
            hash_value,
            "Reference Copy"
        ))
    
    # Now process cleanup folder files against complete hash tables
    print(f"Scanning cleanup folder ({len(cleanup_files)} files)...")
    for index, (rel_path, cleanup_fullpath) in enumerate(cleanup_files.items(), 1):
        files_processed += 1
        progress_var.set(int(100 * files_processed / total_files))
        progress_label.config(text=f"Processing cleanup: {index}/{len(cleanup_files)}")
        
        if index % 5 == 0:
            root.update()
            
        hash_value = calculate_sha256(cleanup_fullpath)
        if not hash_value:
            continue
            
        # Store hash for display
        file_hashes[rel_path] = hash_value
        
        # Check if this file has a content match anywhere in preserve folder
        if hash_value in preserve_hashes:
            # Content match found - mark for deletion
            delete_plan.append(cleanup_fullpath)
            matching_preserve_paths = preserve_hashes[hash_value]
            
            tree.insert("", "end", values=(
                rel_path,
                hash_value,
                f"Delete (duplicate of {matching_preserve_paths[0]})"
            ))
        else:
            # No content match found - check if path exists in preserve
            if rel_path in preserve_path_to_hash:
                # Path exists but different content - move with rename
                new_rel_path = add_prime_to_filename(rel_path)
                move_mismatch_plan.append((cleanup_fullpath, os.path.join(preserve_folder, new_rel_path)))
                
                tree.insert("", "end", values=(
                    rel_path,
                    hash_value,
                    "MOVE WITH RENAME (path exists but content differs)"
                ))
            else:
                # Completely new file - move directly
                move_new_plan.append((cleanup_fullpath, os.path.join(preserve_folder, rel_path)))
                
                tree.insert("", "end", values=(
                    rel_path,
                    hash_value,
                    "MOVE - New file to preserve folder"
                ))
    
    # Final progress update
    progress_var.set(100)
    progress_label.config(text=f"Completed: {files_processed}/{total_files}")
    
    # Update button states based on what we found
    delete_button.config(state=tk.NORMAL if delete_plan else tk.DISABLED)
    move_mismatch_button.config(state=tk.NORMAL if move_mismatch_plan else tk.DISABLED)
    move_new_button.config(state=tk.NORMAL if move_new_plan else tk.DISABLED)
    
    messagebox.showinfo("Comparison Ready", 
                      f"Ready to process:\n"
                      f"• {len(delete_plan)} files to delete (content exists in preserve)\n"
                      f"• {len(move_mismatch_plan)} files to rename and move\n"
                      f"• {len(move_new_plan)} new files to move\n"
                      f"• {len(preserve_files)} reference files in preserve folder")

                       
def add_prime_to_filename(path):
    """Add prime (') before file extension."""
    dir_name, filename = os.path.split(path)
    if '.' in filename:
        name, ext = os.path.splitext(filename)
        new_filename = name + "'" + ext
    else:
        new_filename = filename + "'"
    return os.path.join(dir_name, new_filename)

def execute_delete():
    """Delete identical files from cleanup folder."""
    if not delete_plan:
        messagebox.showwarning("Nothing to Delete", "No identical files to delete.")
        return

    errors = 0
    for idx, filepath in enumerate(delete_plan):
        try:
            progress_var.set(int(100 * (idx + 1) / len(delete_plan)))
            progress_label.config(text=f"Deleting: {idx+1}/{len(delete_plan)}")
            if idx % 5 == 0:
                root.update()
                
            print(f"Deleting: {filepath}")
            os.remove(filepath)
        except Exception as e:
            errors += 1
            print(f"Error deleting {filepath}: {str(e)}")

    progress_var.set(100)
    result_msg = f"Deleted {len(delete_plan) - errors} identical files."
    if errors:
        result_msg += f"\n{errors} files could not be deleted due to errors."
    
    messagebox.showinfo("Delete Operation Completed", result_msg)
    prepare_comparison()

def execute_move_mismatch():
    """Move files with same name but different hash."""
    if not move_mismatch_plan:
        messagebox.showwarning("Nothing to Move", "No mismatched files to move.")
        return

    errors = 0
    for idx, (src, dst) in enumerate(move_mismatch_plan):
        try:
            progress_var.set(int(100 * (idx + 1) / len(move_mismatch_plan)))
            progress_label.config(text=f"Moving mismatched: {idx+1}/{len(move_mismatch_plan)}")
            if idx % 5 == 0:
                root.update()
                
            dst_folder = os.path.dirname(dst)
            if not os.path.exists(dst_folder):
                os.makedirs(dst_folder, exist_ok=True)
            print(f"Moving (renamed): {src} -> {dst}")
            shutil.move(src, dst)
        except Exception as e:
            errors += 1
            print(f"Error moving {src}: {str(e)}")

    progress_var.set(100)
    result_msg = f"Moved {len(move_mismatch_plan) - errors} mismatched files with rename."
    if errors:
        result_msg += f"\n{errors} files could not be moved due to errors."
    
    messagebox.showinfo("Move Mismatch Operation Completed", result_msg)
    prepare_comparison()

def execute_move_new():
    """Move new files from cleanup to preserve folder."""
    if not move_new_plan:
        messagebox.showwarning("Nothing to Move", "No new files to move.")
        return

    errors = 0
    for idx, (src, dst) in enumerate(move_new_plan):
        try:
            progress_var.set(int(100 * (idx + 1) / len(move_new_plan)))
            progress_label.config(text=f"Moving new: {idx+1}/{len(move_new_plan)}")
            if idx % 5 == 0:
                root.update()
                
            dst_folder = os.path.dirname(dst)
            if not os.path.exists(dst_folder):
                os.makedirs(dst_folder, exist_ok=True)
            print(f"Moving (new): {src} -> {dst}")
            shutil.move(src, dst)
        except Exception as e:
            errors += 1
            print(f"Error moving {src}: {str(e)}")

    progress_var.set(100)
    result_msg = f"Moved {len(move_new_plan) - errors} new files."
    if errors:
        result_msg += f"\n{errors} files could not be moved due to errors."
    
    messagebox.showinfo("Move New Operation Completed", result_msg)
    prepare_comparison()

def sort_by_column(column):
    """Sort treeview content when a column header is clicked."""
    global sort_column, sort_reverse
    
    # If clicking the same column, reverse the sort order
    if sort_column == column:
        sort_reverse = not sort_reverse
    else:
        # If clicking a different column, set as new sort column and reset direction
        sort_column = column
        sort_reverse = False
    
    # Get all items from treeview
    item_list = [(tree.set(item, "Path"), tree.set(item, "SHA256"), tree.set(item, "Action"), item) 
                for item in tree.get_children("")]
    
    # Sort based on the column
    if column == "Path":
        # Extract filename from path and sort by filename only
        item_list.sort(key=lambda x: os.path.basename(x[0].lower()), reverse=sort_reverse)
    elif column == "SHA256":
        # Sort by SHA256 hash
        item_list.sort(key=lambda x: x[1].lower(), reverse=sort_reverse)
    else:  # Action
        item_list.sort(key=lambda x: x[2].lower(), reverse=sort_reverse)
    
    # Rearrange items in the sorted order
    for index, (path, sha256, action, item) in enumerate(item_list):
        tree.move(item, "", index)
    
    # Show sort indicator in the header
    for col in ["Path", "SHA256", "Action"]:
        if col == column:
            # Set header text to indicate sort direction
            direction = "▼" if sort_reverse else "▲"
            tree.heading(col, text=f"{col} {direction}")
        else:
            # Reset other columns' header text
            tree.heading(col, text=col)

# GUI setup
root = tk.Tk()
root.title("Preserve and Cleanup Folder Comparator")

# Create main frame
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# Folder selection frame
folder_frame = ttk.LabelFrame(main_frame, text="Folder Selection", padding=5)
folder_frame.pack(fill=tk.X, pady=5)

# Preserve folder row
preserve_frame = ttk.Frame(folder_frame)
preserve_frame.pack(fill=tk.X, pady=2)
preserve_button = ttk.Button(preserve_frame, text="Select Preserve Folder", command=browse_preserve_folder)
preserve_button.pack(side=tk.LEFT, padx=5)
preserve_label = ttk.Label(preserve_frame, text="Preserve Folder: Not Selected")
preserve_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

# Cleanup folder row
cleanup_frame = ttk.Frame(folder_frame)
cleanup_frame.pack(fill=tk.X, pady=2)
cleanup_button = ttk.Button(cleanup_frame, text="Select Cleanup Folder", command=browse_cleanup_folder)
cleanup_button.pack(side=tk.LEFT, padx=5)
cleanup_label = ttk.Label(cleanup_frame, text="Cleanup Folder: Not Selected")
cleanup_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

# Action buttons frame
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=tk.X, pady=5)

prepare_button = ttk.Button(button_frame, text="Prepare Comparison", command=prepare_comparison)
prepare_button.pack(side=tk.LEFT, padx=5)

# Separate action buttons
delete_button = ttk.Button(button_frame, text="Delete Identical", command=execute_delete, state=tk.DISABLED)
delete_button.pack(side=tk.LEFT, padx=5)

move_mismatch_button = ttk.Button(button_frame, text="Move Mismatched", command=execute_move_mismatch, state=tk.DISABLED)
move_mismatch_button.pack(side=tk.LEFT, padx=5)

move_new_button = ttk.Button(button_frame, text="Move New", command=execute_move_new, state=tk.DISABLED)
move_new_button.pack(side=tk.LEFT, padx=5)

# Progress frame
progress_frame = ttk.Frame(main_frame)
progress_frame.pack(fill=tk.X, pady=5)

progress_label = ttk.Label(progress_frame, text="")
progress_label.pack(side=tk.LEFT, padx=5)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, 
                              length=100, mode='determinate', variable=progress_var)
progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

# Treeview frame with scrollbars
tree_frame = ttk.Frame(main_frame)
tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

# Create scrollbars
vsb = ttk.Scrollbar(tree_frame, orient="vertical")
vsb.pack(side=tk.RIGHT, fill=tk.Y)
hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
hsb.pack(side=tk.BOTTOM, fill=tk.X)

# Create Treeview with three columns
tree = ttk.Treeview(tree_frame, columns=("Path", "SHA256", "Action"), show="headings",
                   yscrollcommand=vsb.set, xscrollcommand=hsb.set)

# Configure scrollbars
vsb.config(command=tree.yview)
hsb.config(command=tree.xview)

# Configure column headings with sort commands
tree.heading("Path", text="Path", command=lambda: sort_by_column("Path"))
tree.heading("SHA256", text="SHA256", command=lambda: sort_by_column("SHA256"))
tree.heading("Action", text="Action", command=lambda: sort_by_column("Action"))

# Configure column widths
tree.column("Path", width=350, anchor="w")
tree.column("SHA256", width=350, anchor="w")
tree.column("Action", width=300, anchor="w")

tree.pack(fill=tk.BOTH, expand=True)

# Globals
preserve_folder = ""
cleanup_folder = ""
delete_plan = []
move_mismatch_plan = []  # For files with same name but different hash
move_new_plan = []       # For files only in cleanup folder
file_hashes = {}         # Store file hashes for reference

# Sorting variables
sort_column = "Path"     # Default sort column
sort_reverse = False     # Default sort direction

# Set window size
root.geometry("1000x600")
root.minsize(800, 500)

root.mainloop()
