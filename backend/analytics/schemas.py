from pydantic import BaseModel, Field
from typing import List, Union
from datetime import datetime

class ChartDataset(BaseModel):
    label: str
    data: List[Union[float, int, None]] = Field(default_factory=list)
    border_color: str = "#4A90D9"
    background_color: str = "rgba(74, 144, 217, 0.1)"
    fill: bool = False
    tension: float = 0.4

class ChartData(BaseModel):
    labels: List[str] = Field(default_factory=list)  # x-axis labels (dates, categories)
    datasets: List[ChartDataset] = Field(default_factory=list)

class FrequencyItem(BaseModel):
    name: str
    count: int

class VitalTrends(BaseModel):
    blood_pressure: ChartData = Field(default_factory=ChartData)
    heart_rate: ChartData = Field(default_factory=ChartData)
    blood_sugar: ChartData = Field(default_factory=ChartData)
    weight: ChartData = Field(default_factory=ChartData)
    temperature: ChartData = Field(default_factory=ChartData)
    spo2: ChartData = Field(default_factory=ChartData)

class AnalyticsResponse(BaseModel):
    patient_id: str
    risk_over_time: ChartData = Field(default_factory=ChartData)
    symptom_frequency: List[FrequencyItem] = Field(default_factory=list)
    medication_frequency: List[FrequencyItem] = Field(default_factory=list)
    condition_frequency: List[FrequencyItem] = Field(default_factory=list)
    consultation_count: int = 0
    doctor_visit_count: int = 0
    vital_trends: VitalTrends = Field(default_factory=VitalTrends)
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
