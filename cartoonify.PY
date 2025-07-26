import cv2
import numpy as np
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# ---- Color Theme ----
MAIN_BG   = '#e0f7fa'   # Soft blue
FRAME_BG  = '#ffffff'   # White for frames/containers
BUTTON_BG = '#00838f'   # Deep blue-green for buttons
BUTTON_FG = '#ffffff'   # White text for buttons
LABEL_FG  = '#006064'   # Dark blue for labels

# ---- Globals ----
step_images = {}
selected_image_path = ''

# ---- Cartoon Effect with Color Quantization ----
def color_quantization(img, k=9):
    data = np.float32(img).reshape((-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)
    _, label, center = cv2.kmeans(
        data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )
    center = np.uint8(center)
    result = center[label.flatten()]
    result = result.reshape(img.shape)
    return result

# ---- Upload & Process ----
def upload_image():
    global selected_image_path
    filetypes = (
        ('Image files', '*.jpg *.jpeg *.png *.bmp'),
        ('All files', '*.*')
    )
    selected_image_path = filedialog.askopenfilename(
        title='Select an image', filetypes=filetypes
    )
    if selected_image_path:
        cartoonify(selected_image_path)

def cartoonify(image_path):
    try:
        original = cv2.imread(image_path)
        if original is None:
            messagebox.showerror("Error", "Cannot open image file.")
            return

        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        step_images.clear()
        step_images['Original'] = cv2.resize(original_rgb, (560, 320))

        # Grayscale
        gray = cv2.cvtColor(original_rgb, cv2.COLOR_RGB2GRAY)
        step_images['Gray'] = cv2.resize(
            cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB), (560, 320)
        )

        # Median Blur
        blur = cv2.medianBlur(gray, 7)
        step_images['Blur'] = cv2.resize(
            cv2.cvtColor(blur, cv2.COLOR_GRAY2RGB), (560, 320)
        )

        # Edge Detection (adaptive threshold & invert)
        edges = cv2.adaptiveThreshold(
            blur, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=9,
            C=2
        )
        edges_inv = cv2.bitwise_not(edges)
        step_images['Edges'] = cv2.resize(
            cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2RGB), (560, 320)
        )

        # Color Quantization
        color = color_quantization(original_rgb, k=9)
        color_blur = cv2.bilateralFilter(color, d=11, sigmaColor=250, sigmaSpace=250)
        step_images['Color'] = cv2.resize(color_blur, (560, 320))

        # Final Cartoon Image
        cartoon = cv2.bitwise_and(color_blur, color_blur, mask=edges)
        step_images['Cartoon'] = cv2.resize(cartoon, (560, 320))

        display_all_images()
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ---- Display and Download ----
def display_all_images():
    for widget in image_frame.winfo_children():
        widget.destroy()
    row, col = 0, 0

    for name, img in step_images.items():
        tk_img = ImageTk.PhotoImage(Image.fromarray(cv2.resize(img, (200, 120))))
        img_panel = tk.Label(
            image_frame, image=tk_img, bg=FRAME_BG, borderwidth=2, relief='groove'
        )
        img_panel.photo = tk_img
        img_panel.grid(row=row*3, column=col, padx=10, pady=(10,2))
        name_label = tk.Label(
            image_frame, text=name,
            font=('calibri', 10, 'bold'),
            bg=FRAME_BG, fg=LABEL_FG
        )
        name_label.grid(row=row*3+1, column=col)
        download_btn = tk.Button(
            image_frame, text="Download",
            command=lambda n=name: save_image(n),
            bg=BUTTON_BG, fg=BUTTON_FG, font=('calibri', 9, 'bold')
        )
        download_btn.grid(row=row*3+2, column=col, pady=(0,10))

        col += 1
        if col == 6:
            col = 0
            row += 1

def save_image(step_name):
    if step_name in step_images:
        out_img = step_images[step_name]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All Files", "*.*")],
            title=f"Save {step_name} image"
        )
        if save_path:
            out_bgr = cv2.cvtColor(out_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(save_path, out_bgr)
            messagebox.showinfo("Saved", f"{step_name} saved successfully!")

# ---- TKinter GUI ----
top = tk.Tk()
top.geometry('1250x520')
top.title('Enhanced Cartoonify Your Image')
top.configure(background=MAIN_BG)

upload_btn = tk.Button(
    top, text="Cartoonify an Image", command=upload_image,
    padx=12, pady=7, bg=BUTTON_BG, fg=BUTTON_FG, font=('calibri', 14, 'bold'),
    relief='raised', borderwidth=3
)
upload_btn.pack(side=tk.TOP, pady=18)

image_frame = tk.Frame(top, bg=MAIN_BG)
image_frame.pack(side=tk.TOP, padx=20, pady=18)

top.mainloop()
