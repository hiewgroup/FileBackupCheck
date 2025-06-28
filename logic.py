import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

from sha256_tools import calculate_sha256

# GUI components will be assigned by gui_framework
root = None
preserve_label = None
cleanup_label = None
progress_var = None
progress_label = None
tree = None
delete_button = None
move_mismatch_button = None
move_new_button = None

# Data tracking
preserve_folder = ""
cleanup_folder = ""
delete_plan = []
move_mismatch_plan = []
move_new_plan = []
file_hashes = {}

# Sorting
sort_column = "Path"
sort_reverse = False


def browse_preserve_folder():
    """Select Preserve Folder."""
    global preserve_folder
    preserve_folder = filedialog.askdirectory(title="Select Preserve Folder (Folder A)")
    if preserve_label is not None:
        preserve_label.config(text=f"Preserve Folder: {preserve_folder}")


def browse_cleanup_folder():
    """Select Cleanup Folder."""
    global cleanup_folder
    cleanup_folder = filedialog.askdirectory(title="Select Cleanup Folder (Folder B)")
    if cleanup_label is not None:
        cleanup_label.config(text=f"Cleanup Folder: {cleanup_folder}")


def scan_files(base_folder):
    """Recursively scan all files inside a folder."""
    file_dict = {}
    for root_dir, _, files in os.walk(base_folder):
        for filename in files:
            full_path = os.path.join(root_dir, filename)
            rel_path = os.path.relpath(full_path, base_folder)
            file_dict[rel_path] = full_path
    return file_dict


def prepare_comparison():
    """Prepare comparison between Preserve and Cleanup folder."""
    if not preserve_folder or not cleanup_folder:
        messagebox.showwarning("Folders Not Selected", "Please select both folders.")
        return

    for item in tree.get_children():
        tree.delete(item)
    delete_plan.clear()
    move_mismatch_plan.clear()
    move_new_plan.clear()
    file_hashes.clear()

    preserve_files = scan_files(preserve_folder)
    cleanup_files = scan_files(cleanup_folder)

    total_files = len(preserve_files) + len(cleanup_files)
    files_processed = 0

    progress_var.set(0)
    progress_label.config(text=f"Building hash tables: 0/{total_files}")
    root.update()

    preserve_hashes = {}
    preserve_path_to_hash = {}

    for index, (rel_path, preserve_fullpath) in enumerate(preserve_files.items(), 1):
        files_processed += 1
        progress_var.set(int(100 * files_processed / total_files))
        progress_label.config(text=f"Hashing preserve: {index}/{len(preserve_files)}")

        if index % 5 == 0:
            root.update()

        hash_value = calculate_sha256(preserve_fullpath)
        if not hash_value:
            continue
        if hash_value not in preserve_hashes:
            preserve_hashes[hash_value] = []
        preserve_hashes[hash_value].append(rel_path)
        preserve_path_to_hash[rel_path] = hash_value
        file_hashes[rel_path] = hash_value
        tree.insert("", "end", values=(rel_path, hash_value, "Reference Copy"))

    for index, (rel_path, cleanup_fullpath) in enumerate(cleanup_files.items(), 1):
        files_processed += 1
        progress_var.set(int(100 * files_processed / total_files))
        progress_label.config(text=f"Processing cleanup: {index}/{len(cleanup_files)}")

        if index % 5 == 0:
            root.update()

        hash_value = calculate_sha256(cleanup_fullpath)
        if not hash_value:
            continue
        file_hashes[rel_path] = hash_value

        if hash_value in preserve_hashes:
            delete_plan.append(cleanup_fullpath)
            matching_preserve_paths = preserve_hashes[hash_value]
            tree.insert("", "end", values=(rel_path, hash_value, f"Delete (duplicate of {matching_preserve_paths[0]})"))
        else:
            if rel_path in preserve_path_to_hash:
                new_rel_path = add_prime_to_filename(rel_path)
                move_mismatch_plan.append((cleanup_fullpath, os.path.join(preserve_folder, new_rel_path)))
                tree.insert("", "end", values=(rel_path, hash_value, "MOVE WITH RENAME (path exists but content differs)"))
            else:
                move_new_plan.append((cleanup_fullpath, os.path.join(preserve_folder, rel_path)))
                tree.insert("", "end", values=(rel_path, hash_value, "MOVE - New file to preserve folder"))

    progress_var.set(100)
    progress_label.config(text=f"Completed: {files_processed}/{total_files}")

    delete_button.config(state=tk.NORMAL if delete_plan else tk.DISABLED)
    move_mismatch_button.config(state=tk.NORMAL if move_mismatch_plan else tk.DISABLED)
    move_new_button.config(state=tk.NORMAL if move_new_plan else tk.DISABLED)

    messagebox.showinfo(
        "Comparison Ready",
        f"Ready to process:\n"
        f"• {len(delete_plan)} files to delete (content exists in preserve)\n"
        f"• {len(move_mismatch_plan)} files to rename and move\n"
        f"• {len(move_new_plan)} new files to move\n"
        f"• {len(preserve_files)} reference files in preserve folder"
    )


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

    if sort_column == column:
        sort_reverse = not sort_reverse
    else:
        sort_column = column
        sort_reverse = False

    item_list = [(
        tree.set(item, "Path"),
        tree.set(item, "SHA256"),
        tree.set(item, "Action"),
        item
    ) for item in tree.get_children("")]

    if column == "Path":
        item_list.sort(key=lambda x: os.path.basename(x[0].lower()), reverse=sort_reverse)
    elif column == "SHA256":
        item_list.sort(key=lambda x: x[1].lower(), reverse=sort_reverse)
    else:
        item_list.sort(key=lambda x: x[2].lower(), reverse=sort_reverse)

    for index, (path, sha256, action, item) in enumerate(item_list):
        tree.move(item, "", index)

    for col in ["Path", "SHA256", "Action"]:
        if col == column:
            direction = "▼" if sort_reverse else "▲"
            tree.heading(col, text=f"{col} {direction}")
        else:
            tree.heading(col, text=col)
