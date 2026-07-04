import os
import shutil

os.makedirs('static/images', exist_ok=True)
shutil.copy('dataset/healthy/0.jpg', 'static/images/healthy_sample.jpg')
shutil.copy('dataset/miner/1000.jpg', 'static/images/miner_sample.jpg')
shutil.copy('dataset/phoma/100.jpg', 'static/images/phoma_sample.jpg')
shutil.copy('dataset/rust/1028.jpg', 'static/images/rust_sample.jpg')
print("Samples copied successfully.")
