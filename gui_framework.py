import tkinter as tk
from tkinter import ttk

import logic


def create_gui():
    """Builds the GUI and starts the Tkinter main loop."""
    logic.root = tk.Tk()
    root = logic.root
    root.title("Preserve and Cleanup Folder Comparator")

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    folder_frame = ttk.LabelFrame(main_frame, text="Folder Selection", padding=5)
    folder_frame.pack(fill=tk.X, pady=5)

    preserve_frame = ttk.Frame(folder_frame)
    preserve_frame.pack(fill=tk.X, pady=2)
    preserve_button = ttk.Button(
        preserve_frame,
        text="Select Preserve Folder",
        command=logic.browse_preserve_folder,
    )
    preserve_button.pack(side=tk.LEFT, padx=5)
    logic.preserve_label = ttk.Label(preserve_frame, text="Preserve Folder: Not Selected")
    logic.preserve_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    cleanup_frame = ttk.Frame(folder_frame)
    cleanup_frame.pack(fill=tk.X, pady=2)
    cleanup_button = ttk.Button(
        cleanup_frame,
        text="Select Cleanup Folder",
        command=logic.browse_cleanup_folder,
    )
    cleanup_button.pack(side=tk.LEFT, padx=5)
    logic.cleanup_label = ttk.Label(cleanup_frame, text="Cleanup Folder: Not Selected")
    logic.cleanup_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=5)

    prepare_button = ttk.Button(button_frame, text="Prepare Comparison", command=logic.prepare_comparison)
    prepare_button.pack(side=tk.LEFT, padx=5)

    logic.delete_button = ttk.Button(button_frame, text="Delete Identical", command=logic.execute_delete, state=tk.DISABLED)
    logic.delete_button.pack(side=tk.LEFT, padx=5)

    logic.move_mismatch_button = ttk.Button(button_frame, text="Move Mismatched", command=logic.execute_move_mismatch, state=tk.DISABLED)
    logic.move_mismatch_button.pack(side=tk.LEFT, padx=5)

    logic.move_new_button = ttk.Button(button_frame, text="Move New", command=logic.execute_move_new, state=tk.DISABLED)
    logic.move_new_button.pack(side=tk.LEFT, padx=5)

    progress_frame = ttk.Frame(main_frame)
    progress_frame.pack(fill=tk.X, pady=5)

    logic.progress_label = ttk.Label(progress_frame, text="")
    logic.progress_label.pack(side=tk.LEFT, padx=5)

    logic.progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(
        progress_frame,
        orient=tk.HORIZONTAL,
        length=100,
        mode='determinate',
        variable=logic.progress_var,
    )
    progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

    tree_frame = ttk.Frame(main_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    vsb = ttk.Scrollbar(tree_frame, orient="vertical")
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
    hsb.pack(side=tk.BOTTOM, fill=tk.X)

    logic.tree = ttk.Treeview(
        tree_frame,
        columns=("Path", "SHA256", "Action"),
        show="headings",
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set,
    )

    vsb.config(command=logic.tree.yview)
    hsb.config(command=logic.tree.xview)

    logic.tree.heading("Path", text="Path", command=lambda: logic.sort_by_column("Path"))
    logic.tree.heading("SHA256", text="SHA256", command=lambda: logic.sort_by_column("SHA256"))
    logic.tree.heading("Action", text="Action", command=lambda: logic.sort_by_column("Action"))

    logic.tree.column("Path", width=350, anchor="w")
    logic.tree.column("SHA256", width=350, anchor="w")
    logic.tree.column("Action", width=300, anchor="w")

    logic.tree.pack(fill=tk.BOTH, expand=True)

    root.geometry("1000x600")
    root.minsize(800, 500)

    root.mainloop()
