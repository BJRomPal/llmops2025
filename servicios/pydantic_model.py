from pydantic import BaseModel, Field
from typing import Optional

# --- 1. Definición del Modelo Pydantic ---
# Esto asegura que la salida del LLM siempre tenga un formato JSON consistente.
class ProductDimensions(BaseModel):
    """
    Pydantic model to store the dimensions and weight of a product.

    """
    alto: Optional[float] = Field(0, description="How tall the product is in centimeters.")
    ancho: Optional[float] = Field(0, description="How wide the product is in centimeters.")
    largo: Optional[float] = Field(0, description="How long the product is in centimeters.")
    peso: Optional[float] = Field(0, description="What is the weight of the product is in kilograms.")
    fuente: Optional[str] = Field(0, description="Where did you get the source of the information.")