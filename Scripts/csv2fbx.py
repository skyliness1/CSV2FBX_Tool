import os
import sys
import traceback
import threading
import time
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from csv import reader
import fbx
from FbxCommon import *

class CSV2FBXConverter:
    def read_csv_file(self, file_path):
        csvList = []
        try:
            with open(file_path, "r") as csvfile:
                next(csvfile)  # Skip header row
                csv_reader = reader(csvfile)
                for row in csv_reader:
                    row_data = []
                    for item in row:
                        try:
                            value = float(item)
                            row_data.append(value)
                        except ValueError:
                            row_data.append(item)
                    csvList.append(row_data)
            return csvList
        except Exception as e:
            self.log_message(f"Error reading CSV file: {str(e)}")
            return []

    def create_fbx_scene(self):
        fbx_manager = FbxManager.Create()
        scene = FbxScene.Create(fbx_manager, "My Scene")
        return fbx_manager, scene

    def set_mesh_point_at(self, csvList, newMesh, vtxID, vertexID):
        count = len(csvList)
        newMesh.InitControlPoints(count)
        for i in range(0, count):
            _csv = csvList[i]
            pos = FbxVector4(float(_csv[vertexID]), float(_csv[vertexID+1]), float(_csv[vertexID+2]))
            newMesh.SetControlPointAt(pos, i)

    def set_mesh_polygon(self, csvList, newMesh):
        count = len(csvList)
        for i in range(0, int(count/3)):
            newMesh.BeginPolygon(i)
            newMesh.AddPolygon(i*3)
            newMesh.AddPolygon(i*3+1)
            newMesh.AddPolygon(i*3+2)
            newMesh.EndPolygon()

    def set_mesh_uv(self, csvList, newMesh, uv0ID, uv1ID=None):
        count = len(csvList)
        uv_layer = newMesh.CreateElementUV("uv0")

        # Using confirmed enum values
        uv_layer.SetMappingMode(fbx.FbxLayerElement.EMappingMode.eByPolygonVertex)
        uv_layer.SetReferenceMode(fbx.FbxLayerElement.EReferenceMode.eIndexToDirect)

        uv_array = uv_layer.GetDirectArray()
        uv_index_array = uv_layer.GetIndexArray()
        uv_array.Resize(count)
        uv_index_array.Resize(count)

        for i in range(0, count):
            _csv = csvList[i]
            uv0 = FbxVector2(float(_csv[uv0ID]), float(_csv[uv0ID+1]))
            uv_array.SetAt(i, uv0)
            uv_index_array.SetAt(i, i)

    def set_mesh_normal(self, csvList, newMesh, normalID):
        count = len(csvList)
        normal_layer = newMesh.CreateElementNormal()

        if newMesh.GetElementNormalCount() > 1:
            newMesh.RemoveElementNormal(newMesh.GetElementNormal(0))

        # Using confirmed enum values
        normal_layer.SetMappingMode(fbx.FbxLayerElement.EMappingMode.eByControlPoint)
        normal_layer.SetReferenceMode(fbx.FbxLayerElement.EReferenceMode.eDirect)

        normal_array = normal_layer.GetDirectArray()
        normal_array.Resize(count)

        self.log_message(f"Current mesh's normalLayerCount: {newMesh.GetElementNormalCount()}")

        for i in range(0, count):
            _csv = csvList[i]
            normal = FbxVector4(float(_csv[normalID]), float(_csv[normalID+1]), float(_csv[normalID+2]))
            normal_array.SetAt(i, normal)

    def getASCIIFormatIndex(self, pManager):
        numFormats = pManager.GetIOPluginRegistry().GetWriterFormatCount()
        formatIndex = pManager.GetIOPluginRegistry().GetNativeWriterFormat()
        for i in range(0, numFormats):
            if pManager.GetIOPluginRegistry().WriterIsFBX(i):
                description = pManager.GetIOPluginRegistry().GetWriterFormatDescription(i)
                if 'ascii' in description:
                    formatIndex = i
                    break
        return formatIndex

    def save_scene(self, pFilename, pFbxmanager, pFbxScene, pAsASCII=False):
        exporter = FbxExporter.Create(pFbxmanager, '')
        if pAsASCII:
            asciiFormatIndex = self.getASCIIFormatIndex(pFbxmanager)
            isInitialized = exporter.Initialize(pFilename, asciiFormatIndex)
        else:
            isInitialized = exporter.Initialize(pFilename)

        if not isInitialized:
            raise Exception(f'Exporter failed to initialize. Error: {exporter.GetStatus().GetErrorString()}')

        exporter.Export(pFbxScene)
        exporter.Destroy()

    def csv_to_fbx(self, csv_path, fbx_path, vtx_id=0, vertex_id=2, uv_id=8, normal_id=5, as_ascii=True):
        """
        Convert CSV data to FBX format
        
        Parameters:
        csv_path (str): Path to the CSV file
        fbx_path (str): Path to save the FBX file
        vtx_id (int): Column index for vertex ID
        vertex_id (int): Starting column index for vertex position (x,y,z)
        uv_id (int): Starting column index for UV coordinates (u,v)
        normal_id (int): Starting column index for normal vectors (x,y,z)
        as_ascii (bool): Whether to save as ASCII format (readable) or binary
        """
        try:
            # Read CSV data
            self.log_message(f"Reading CSV file: {csv_path}")
            csv_data = self.read_csv_file(csv_path)

            if not csv_data:
                self.log_message("Error: CSV file is empty or has invalid format")
                return False

            # Create FBX scene
            self.log_message("Creating FBX scene")
            manager, scene = self.create_fbx_scene()

            # Create mesh and node
            mesh_name = os.path.splitext(os.path.basename(csv_path))[0]
            mesh = FbxMesh.Create(scene, mesh_name)
            node = FbxNode.Create(scene, mesh_name)
            node.SetNodeAttribute(mesh)

            # Add node to scene
            root_node = scene.GetRootNode()
            root_node.AddChild(node)

            # Set mesh data
            self.log_message(f"Processing {len(csv_data)} vertices")
            self.set_mesh_point_at(csv_data, mesh, vtx_id, vertex_id)
            self.set_mesh_polygon(csv_data, mesh)
            self.set_mesh_uv(csv_data, mesh, uv_id)
            self.set_mesh_normal(csv_data, mesh, normal_id)

            # Save FBX file
            self.log_message(f"Saving FBX file: {fbx_path}")
            self.save_scene(fbx_path, manager, scene, as_ascii)

            # Clean up
            manager.Destroy()
            self.log_message("Conversion completed successfully")
            return True

        except Exception as e:
            self.log_message(f"Error converting CSV to FBX: {str(e)}")
            traceback.print_exc()
            return False

    def log_message(self, message):
        # This will be overridden by the GUI class
        print(message)


class CSV2FBXGUI(CSV2FBXConverter):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.root.title("CSV to FBX Converter")
        self.root.geometry("750x600")
        self.root.resizable(True, True)

        # Create style for ttk widgets
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        self.style.configure("TLabel", padding=6)
        self.style.configure("TFrame", padding=10)

        # Create main frames
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Path selection frame
        self.path_frame = ttk.LabelFrame(self.main_frame, text="File Paths")
        self.path_frame.pack(fill=X, padx=5, pady=5)

        # CSV input
        self.csv_frame = ttk.Frame(self.path_frame)
        self.csv_frame.pack(fill=X, padx=5, pady=5)

        ttk.Label(self.csv_frame, text="CSV File:").pack(side=LEFT, padx=5)
        self.csv_path_var = StringVar()
        self.csv_path_entry = ttk.Entry(self.csv_frame, textvariable=self.csv_path_var, width=50)
        self.csv_path_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(self.csv_frame, text="Browse...", command=self.browse_csv).pack(side=LEFT, padx=5)

        # FBX output
        self.fbx_frame = ttk.Frame(self.path_frame)
        self.fbx_frame.pack(fill=X, padx=5, pady=5)

        ttk.Label(self.fbx_frame, text="FBX Output:").pack(side=LEFT, padx=5)
        self.fbx_path_var = StringVar()
        self.fbx_path_entry = ttk.Entry(self.fbx_frame, textvariable=self.fbx_path_var, width=50)
        self.fbx_path_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(self.fbx_frame, text="Browse...", command=self.browse_fbx).pack(side=LEFT, padx=5)

        # Options frame
        self.options_frame = ttk.LabelFrame(self.main_frame, text="Column Mapping")
        self.options_frame.pack(fill=X, padx=5, pady=5)

        # Create column mapping options
        self.options_grid = ttk.Frame(self.options_frame)
        self.options_grid.pack(fill=X, padx=5, pady=5)

        # Vertex ID
        ttk.Label(self.options_grid, text="Vertex ID Column:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.vtx_id_var = IntVar(value=0)
        self.vtx_id_spinbox = ttk.Spinbox(self.options_grid, from_=0, to=50, textvariable=self.vtx_id_var, width=5)
        self.vtx_id_spinbox.grid(row=0, column=1, sticky=W, padx=5, pady=5)

        # Vertex Position
        ttk.Label(self.options_grid, text="Position Columns (X,Y,Z):").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.vertex_id_var = IntVar(value=2)
        self.vertex_id_spinbox = ttk.Spinbox(self.options_grid, from_=0, to=50, textvariable=self.vertex_id_var, width=5)
        self.vertex_id_spinbox.grid(row=1, column=1, sticky=W, padx=5, pady=5)

        # Normal
        ttk.Label(self.options_grid, text="Normal Columns (X,Y,Z):").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.normal_id_var = IntVar(value=5)
        self.normal_id_spinbox = ttk.Spinbox(self.options_grid, from_=0, to=50, textvariable=self.normal_id_var, width=5)
        self.normal_id_spinbox.grid(row=2, column=1, sticky=W, padx=5, pady=5)

        # UV
        ttk.Label(self.options_grid, text="UV Columns (U,V):").grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.uv_id_var = IntVar(value=8)
        self.uv_id_spinbox = ttk.Spinbox(self.options_grid, from_=0, to=50, textvariable=self.uv_id_var, width=5)
        self.uv_id_spinbox.grid(row=3, column=1, sticky=W, padx=5, pady=5)

        # Format options
        self.format_frame = ttk.Frame(self.options_frame)
        self.format_frame.pack(fill=X, padx=5, pady=5)

        self.ascii_var = BooleanVar(value=True)
        self.ascii_check = ttk.Checkbutton(self.format_frame, text="Export as ASCII (readable format)",
                                           variable=self.ascii_var)
        self.ascii_check.pack(side=LEFT, padx=5, pady=5)

        # Conversion button
        self.convert_frame = ttk.Frame(self.main_frame)
        self.convert_frame.pack(fill=X, padx=5, pady=10)

        self.convert_button = ttk.Button(self.convert_frame, text="Convert CSV to FBX",
                                         command=self.start_conversion)
        self.convert_button.pack(side=TOP, fill=X, padx=5, pady=5)

        # Progress indicator
        self.progress_var = DoubleVar()
        self.progress = ttk.Progressbar(self.convert_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=X, padx=5, pady=5)

        # Log frame
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Log")
        self.log_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.log_text = Text(self.log_frame, height=10, width=80, wrap=WORD)
        self.log_text.pack(fill=BOTH, expand=True, side=LEFT, padx=5, pady=5)

        self.log_scroll = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_scroll.pack(fill=Y, side=RIGHT, padx=0, pady=5)
        self.log_text.config(yscrollcommand=self.log_scroll.set)

        # Bottom buttons
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=X, padx=5, pady=5)

        self.clear_log_button = ttk.Button(self.bottom_frame, text="Clear Log", command=self.clear_log)
        self.clear_log_button.pack(side=LEFT, padx=5)

        self.about_button = ttk.Button(self.bottom_frame, text="About", command=self.show_about)
        self.about_button.pack(side=RIGHT, padx=5)

        # Initialize with welcome message
        self.log_message("Welcome to CSV to FBX Converter!\n")
        self.log_message("Please select a CSV file and an output path, then configure the column mappings.")
        self.log_message("Column indices start at 0. For position, normal, and UV, specify the starting column.")

    def browse_csv(self):
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_path_var.set(filename)
            # Auto-update FBX path if empty
            if not self.fbx_path_var.get():
                fbx_filename = os.path.splitext(filename)[0] + ".fbx"
                self.fbx_path_var.set(fbx_filename)

    def browse_fbx(self):
        filename = filedialog.asksaveasfilename(
            title="Save FBX File",
            filetypes=[("FBX files", "*.fbx"), ("All files", "*.*")],
            defaultextension=".fbx"
        )
        if filename:
            self.fbx_path_var.set(filename)

    def start_conversion(self):
        # Get all parameters
        csv_path = self.csv_path_var.get()
        fbx_path = self.fbx_path_var.get()

        # Validate inputs
        if not csv_path or not os.path.exists(csv_path):
            messagebox.showerror("Error", "Please select a valid CSV file.")
            return

        if not fbx_path:
            messagebox.showerror("Error", "Please specify an output FBX file path.")
            return

        # Disable UI during conversion
        self.convert_button.config(state="disabled")
        self.progress_var.set(0)

        # Get parameters
        vtx_id = self.vtx_id_var.get()
        vertex_id = self.vertex_id_var.get()
        normal_id = self.normal_id_var.get()
        uv_id = self.uv_id_var.get()
        as_ascii = self.ascii_var.get()

        # Start conversion in a separate thread
        self.conversion_thread = threading.Thread(
            target=self.run_conversion,
            args=(csv_path, fbx_path, vtx_id, vertex_id, uv_id, normal_id, as_ascii),
            daemon=True
        )
        self.conversion_thread.start()

        # Start progress update
        self.update_progress()

    def run_conversion(self, csv_path, fbx_path, vtx_id, vertex_id, uv_id, normal_id, as_ascii):
        # Clear the log
        self.root.after(0, self.clear_log)

        # Run the conversion
        success = self.csv_to_fbx(
            csv_path,
            fbx_path,
            vtx_id=vtx_id,
            vertex_id=vertex_id,
            uv_id=uv_id,
            normal_id=normal_id,
            as_ascii=as_ascii
        )

        # Show result message
        if success:
            self.root.after(0, lambda: messagebox.showinfo("Success", "Conversion completed successfully!"))
        else:
            self.root.after(0, lambda: messagebox.showerror("Error", "Conversion failed. Check the log for details."))

        # Enable UI
        self.root.after(0, lambda: self.convert_button.config(state="normal"))
        self.root.after(0, lambda: self.progress_var.set(100))

    def update_progress(self):
        if hasattr(self, 'conversion_thread') and self.conversion_thread.is_alive():
            # Still running, update progress (simulated)
            current = self.progress_var.get()
            if current < 90:  # Leave room for completion
                self.progress_var.set(current + 5)
            self.root.after(200, self.update_progress)
        else:
            # If we get here and the thread is not running, ensure 100%
            self.progress_var.set(100)

    def log_message(self, message):
        # Add timestamp
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        formatted_message = f"[{timestamp}] {message}\n"

        # Insert into text widget
        self.root.after(0, lambda: self.log_text.insert(END, formatted_message))
        self.root.after(0, lambda: self.log_text.see(END))

    def clear_log(self):
        self.log_text.delete(1.0, END)

    def show_about(self):
        about_text = """CSV to FBX Converter v1.0

This tool converts CSV mesh data to FBX format.

CSV Format:
- First row is header (skipped)
- Columns should include vertex ID, position (X,Y,Z), normal (X,Y,Z), and UV (U,V)
- Specify the starting column index for each data type

Developed by: skyliness1
Date: 2025-07-14
        """
        messagebox.showinfo("About", about_text)


if __name__ == "__main__":
    root = Tk()
    app = CSV2FBXGUI(root)
    root.mainloop()