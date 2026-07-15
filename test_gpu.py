import torch

print(torch.__version__)

print("CUDA:", torch.cuda.is_available())

print("Device:", torch.device("cuda" if torch.cuda.is_available() else "cpu"))