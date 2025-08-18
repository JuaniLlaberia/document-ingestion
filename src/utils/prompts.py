GENERATE_IMG_DESCRIPTION_SYSTEM = """
You are an image description expert.
"""

GENERATE_IMG_DESCRIPTION_PROMPT = """
Generate a description for the provided image. This description will be used to create a semantic embedding to find the image.

The description must:
- Be a single sentence under 150 characters.
- Be objective, focusing on the subject, action, and setting.
- Avoid phrases like "a picture of" or subjective words.

Example descriptions:
- A person skateboarding down a street at sunset.
- A wide-angle shot of a mountain range covered in snow under a clear blue sky.
- A close-up of a cup of coffee with steam rising from it.

Only return the description.
"""