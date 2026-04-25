from app.models.body_metric import WaistMeasurement
from app.routes._body_metric_crud import make_body_metric_blueprint
from app.services.body_metrics import WAIST

bp = make_body_metric_blueprint("waist_measurements", WaistMeasurement, WAIST)
