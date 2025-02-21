from texify.inference import batch_inference
from texify.model.model import load_model
from texify.model.processor import load_processor
from PIL import Image
import re

class OCRExpressionWorker:
    def __init__(self):
        self.model = load_model()
        self.processor = load_processor()

    def get_latex_expression(self, file_obj):
        file_obj.seek(0)
        img = Image.open(file_obj)
        result = batch_inference([img], self.model, self.processor)[0]

        corrected_expression = re.sub(r'\\\\', r'\\', result)

        return corrected_expression