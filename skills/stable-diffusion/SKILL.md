# 🎨 Stable Diffusion on Intel XPU (IPEX)

A modular skill to generate images using Intel Extension for PyTorch (IPEX) and `diffusers`.

## 📦 Requirements
- `torch`
- `intel_extension_for_pytorch`
- `diffusers`
- `transformers`
- `accelerate`

## 🚀 Execution
Run this script via `/run` or through a dedicated bash handler.

```python
import torch
import intel_extension_for_pytorch as ipex
from diffusers import AutoPipelineForText2Image
import os

# MSI Claw Hardware Acceleration Settings
os.environ["ONEAPI_DEVICE_SELECTOR"] = "level_zero:0"
os.environ["PYTORCH_ENABLE_XPU_FALLBACK"] = "1"

def generate_image(prompt, output_path="output.png"):
    print(f"🎨 Jules is drawing: '{prompt}' on Intel Arc...")

    # Use a lightweight model for speed (SD-Turbo is ideal for 1-step generation)
    model_id = "stabilityai/sd-turbo"

    # Load pipeline
    pipe = AutoPipelineForText2Image.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        variant="fp16"
    )

    # Move to Intel GPU (XPU)
    pipe.to("xpu")

    # Optimize with IPEX
    pipe.unet = ipex.optimize(pipe.unet, dtype=torch.float16)

    # Generate
    image = pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]

    # Save
    image.save(output_path)
    print(f"✅ Image saved to: {output_path}")

if __name__ == "__main__":
    prompt = "A high-tech coding workstation on a handheld gaming PC, synthwave style"
    generate_image(prompt)
```
